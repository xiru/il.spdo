# -*- coding: utf-8 -*-

# Banco de Dados #
DEFAULT_DSN = 'mysql://root:interlegis@localhost/spdo?charset=utf8'
TABLE_ARGS = {'mysql_engine':'InnoDB','mysql_charset':'utf8'}
CREATE_ALL_TABLES = True
CREATE_SAMPLES = True
LOTS_OF_SAMPLES = False
DISABLE_VERSIONS = True

# Anexos #
PATH_ANEXOS = '/var/interlegis/spdo/anexos'
ENABLE_FLASH_MULTIFILE = True

# Quantidade máxima de protocolos retornados em uma pesquisa. Aviso:
# não defina esse limite com um valor muito alto, pois poderá
# acarretar lentidão na pesquisa de protocolos.
SEARCH_LIMIT = 1000

# Validação de e-mails #
EMAIL_RE = "^([0-9a-zA-Z_&.'+-]+!)*[0-9a-zA-Z_&.'+-]+@(([0-9a-zA-Z]([0-9a-zA-Z-]*[0-9a-z-A-Z])?\.)+[a-zA-Z]{2,6}|([0-9]{1,3}\.){3}[0-9]{1,3})$"

# Notificações #
NOTIFICACAO_ASSUNTO = u"[SPDO] O protocolo %(numero)s tramitou."
NOTIFICACAO_MSG = u"""Olá,

essa mensagem é uma notificação do Sistema de Protocolo de Documentos,
enviada automaticamente para todas as pessoas interessadas em acompanhar
a tramitação de um determinado protocolo.

O seguinte protocolo tramitou:

Número do Protocolo: %(numero)s
Data da Última Tramitação: %(data_tramitacao)s
Assunto: %(assunto)s
Área de Origem: %(area_origem)s
Responsável pelo Encaminhamento: %(responsavel_origem)s
Área de Destino: %(area_destino)s
Responsável pelo Recebimento: %(responsavel_destino)s
Situação: %(situacao)s

Você pode acessar os detalhes desse protocolo no seguinte link:
%(url_protocolo)s

Essa é uma mensagem automática. Por favor, não responda! Caso não
queira mais receber notificações como essa acesse o link a seguir,
removendo os protocolos que não deseja mais acompanhar:
%(url_notificacoes)s

--
Sistema de Protocolo de Documentos - SPDO
"""

from z3c.saconfig import named_scoped_session
import zope.i18nmessageid

def Session():
    return named_scoped_session('spdo_session')

MessageFactory = zope.i18nmessageid.MessageFactory('il.spdo')
