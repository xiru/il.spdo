#!/bin/sh

# Script de Instalação Automática do SPDO
# wget -O - http://repositorio.interlegis.gov.br/il.spdo/trunk/docs/install-spdo.sh | sh

VERSION="1.0"
INSTALL_DIR="/var/interlegis/spdo"
DOWNLOAD_URL="http://launchpad.net/plone/4.1/4.1.4/+download/Plone-4.1.4-UnifiedInstaller.tgz"
LOG_FILE="/tmp/spdo-install.log"
AUTOSOLVER=1
PRESERVE_ARCHIVE=0
UNINSTALL=0
ERR_FATAL=1

for PARAM in $@; do
  eval $PARAM
done

log() {
  echo `date` $1 >> $LOG_FILE
}

puts() {
  echo $1
  log "$1"
}

puts_separator() {
  puts "-----------------------------------"
}

exec_cmd() {
  TITLE=$1
  COMMAND=$2
  
  puts "$TITLE $COMMAND"
  `$COMMAND`
}

fatal_error() {
  puts "Erro: $1"
  exit $ERR_FATAL
}

is_command_present() {
  puts "Verificando a existência do comando: $1"
  
  CMD=`whereis -b $1 | awk '{ print $2 }'`
  [ -n "$CMD" ] && return 0 || return 1
}

detect_os() {
  puts "Detectando a distribuição..."

  is_command_present "lsb_release"
  if [ $? -eq 0 ]; then
    puts "LSB info: `lsb_release -a`"
    DISTRIB_ID=`lsb_release -si`
    return 0
  fi
  
  [ -f /etc/redhat-release ] && DISTRIB_ID="RedHat"  
  [ -f /etc/fedora-release ] && DISTRIB_ID="Fedora"
  [ -f /etc/debian_version ] && DISTRIB_ID="Debian"
}

resolve_deps() {
  puts "Resolvendo dependências..."

  if [ "$DISTRIB_ID" = "Debian" -o "$DISTRIB_ID" = "Ubuntu" ]; then
      apt-get update
      apt-get -y install build-essential git-core libfreetype6 libfreetype6-dev \
      libjpeg62 libjpeg62-dev libmysqlclient-dev libreadline6 libreadline-dev \
      libssl-dev mysql-client ssh subversion zlib1g zlib1g-dev
      DEBIAN_FRONTEND=noninteractive apt-get -y install mysql-server
  fi
  
  if [ "$DISTRIB_ID" = "RedHat" -o "$DISTRIB_ID" = "Fedora" -o "$DISTRIB_ID" = "CentOS" ]; then
      fatal_error "O instalador automático ainda não suporta sua distribuição."
  fi
}

check_dependencies() {
  [ "x$AUTOSOLVER" = "x1" ] && resolve_deps
}

check_environment() {
  puts "Verificando ambiente..."
  
  [ "`whoami`" != "root" ] && fatal_error "O instalador deve ser executado com o usuário root."
  
  puts "Sistema: `uname -a`"
  
  detect_os
  [ "x$DISTRIB_ID" != "x" ] && puts "Distribuição: $DISTRIB_ID"
}

install_product() {
  puts "Instalando..."
  
  mkdir -p $INSTALL_DIR/installer; cd $INSTALL_DIR/installer
  
  exec_cmd "Baixando instalador:" "wget $DOWNLOAD_URL"
  [ $? -ne 0 ] && fatal_error "Erro ao tentar baixar o instalador do Plone."

  tar -zxvf Plone-4.1.4-UnifiedInstaller.tgz
  cd Plone-4.1.4-UnifiedInstaller
  ./install.sh --target=$INSTALL_DIR standalone
  
  if [ "x$PRESERVE_ARCHIVE" != "x1" ]; then
    exec_cmd "Removendo instalador:" "rm -rf $INSTALL_DIR/installer"
    cd $INSTALL_DIR
  fi

  puts "Baixando o código fonte do il.spdo..."
  cd $INSTALL_DIR/zinstance/src
  svn co http://repositorio.interlegis.gov.br/il.spdo/trunk/ il.spdo

  puts "Executando o buildout..."
  cd $INSTALL_DIR/zinstance
  ln -sf $INSTALL_DIR/zinstance/src/il.spdo/il/spdo/buildout/*.cfg .
  ./bin/buildout -c develop.cfg

  puts "Criando banco de dados..."
  mysql -uroot -e "create database spdo"
  mysql -uroot -e "grant all on spdo.* to root@localhost identified by 'interlegis'; flush privileges"
  $INSTALL_DIR/zinstance/bin/zopepy $INSTALL_DIR/zinstance/src/il.spdo/il/spdo/db.py

  puts "Criando diretório para armazenamento de anexos..."
  mkdir -p $INSTALL_DIR/anexos
  chown -R plone $INSTALL_DIR/anexos

  puts "Atualizando o /etc/rc.local"
  sed -i '/exit 0/d' /etc/rc.local
  echo "$INSTALL_DIR/zinstance/bin/instance start" >> /etc/rc.local
  echo "exit 0" >> /etc/rc.local

  puts "Iniciando o SPDO..."
  $INSTALL_DIR/zinstance/bin/instance start

  puts "SPDO instalado!"
}

uninstall_product() {
  rm -rf $INSTALL_DIR
  sed -i '/$INSTALL_DIR\/zinstance\/bin\/instance start/d' /etc/rc.local
  puts "SPDO desinstalado!"
}

main() {
  puts_separator
  puts "Instalador Automático SPDO."
  puts_separator
  
  check_environment
  
  if [ "x$UNINSTALL" = "x1" ]; then
    uninstall_product
  else
    check_dependencies
    install_product
  fi
}

main
