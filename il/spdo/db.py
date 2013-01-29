# -*- coding: utf-8 -*-

from zope.interface import implements
from sqlalchemy import create_engine, Table, Column, Integer, String, DateTime, Text, Boolean, ForeignKey, func
from sqlalchemy.orm import relationship, backref, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.schema import UniqueConstraint
from il.spdo.config import DEFAULT_DSN, TABLE_ARGS, CREATE_ALL_TABLES, CREATE_SAMPLES, LOTS_OF_SAMPLES, Session
from il.spdo import interfaces
from il.spdo.history_meta import VersionedMeta, VersionedListener
from random import choice
import bcrypt
import datetime
import string
import math
import sys
from zExceptions import Forbidden

Base = declarative_base(metaclass=VersionedMeta)

if __name__ == '__main__':
    engine = create_engine(DEFAULT_DSN)
    Session = sessionmaker(bind=engine, extension=VersionedListener())

def nextVersion(tabela, **kw):
    session = Session()
    clausula_where = ''
    if kw:
        # Xiru: proteção contra SQL Injection
        for v in kw.values():
            try:
                int(v)
            except ValueError:
                raise Forbidden
        clausula_where = 'where ' + " and ".join(["%s=%s" % (k, str(v)) for k, v in kw.items()])
    max_version = session.bind.execute('SELECT max(version) from %s_history %s' % (tabela, clausula_where)).fetchone()[0]
    return max_version is None and 1 or (max_version + 1)

class Area(Base):
    implements(interfaces.IArea)
    __tablename__ = 'area'
    __table_args__ = TABLE_ARGS
    id = Column(Integer, primary_key=True)
    sigla = Column(String(20), unique=True, nullable=False)
    nome = Column(String(100), unique=True, nullable=False)
    chefia_id = Column(Integer, ForeignKey('area.id'))
    chefia = relationship("Area", backref=backref('area', remote_side=id))

class UF(Base):
    implements(interfaces.IUF)
    __tablename__ = 'uf'
    __table_args__ = TABLE_ARGS
    id = Column(Integer, primary_key=True)
    sigla = Column(String(2), unique=True, nullable=False)
    nome = Column(String(40), unique=True, nullable=False)

def geraSenha(tamanho):
    chars = string.letters + string.digits
    s = ""
    for i in range(tamanho):
        s += choice(chars)
    return s

def geraHash(senha):
    return bcrypt.hashpw(senha, bcrypt.gensalt())

class Pessoa(Base):
    implements(interfaces.IPessoa)
    __tablename__ = 'pessoa'
    __table_args__ = TABLE_ARGS
    id = Column(Integer, primary_key=True)
    nome = Column(String(100), nullable=False)
    email = Column(String(254), unique=True, nullable=False)
    endereco = Column(String(100))
    bairro = Column(String(50))
    cep = Column(String(8))
    cidade = Column(String(50))
    uf_id = Column(Integer, ForeignKey('uf.id'))
    uf = relationship("UF", backref="pessoa")
    telefone = Column(String(30))
    cpf_cnpj = Column(String(20))
    tipopessoa = Column(String(1), nullable=False)
    contato = Column(String(100))
    area_id = Column(Integer, ForeignKey('area.id'))
    area = relationship("Area", backref="pessoa")
    senha = Column(Text(), nullable=False)
    
    def __init__(self, nome, email, endereco=None, bairro=None, cep=None, cidade=None, uf_id=None, 
                 telefone=None, cpf_cnpj=None, tipopessoa='F', contato=None, area_id=None):
        self.nome = nome
        self.email = email
        self.endereco = endereco
        self.bairro = bairro
        self.cep = cep
        self.cidade = cidade
        self.uf_id = uf_id
        self.telefone = telefone
        self.cpf_cnpj = cpf_cnpj
        self.tipopessoa = tipopessoa
        self.contato = contato
        self.area_id = area_id
        self.senha = geraHash(geraSenha(8))

    def __repr__(self):
        return "<Pessoa:%s>" % self.email

class Responsavel(Base):
    implements(interfaces.IResponsavel)
    __tablename__ = 'responsavel'
    __table_args__ = TABLE_ARGS
    id = Column(Integer, primary_key=True)
    area_id = Column(Integer, ForeignKey('area.id'))
    pessoa_id = Column(Integer, ForeignKey('pessoa.id'))
    data_responsavel = Column(DateTime(), default=datetime.date.today, nullable=False)
    area = relationship("Area", backref=backref("responsavel", order_by=data_responsavel))
    pessoa = relationship("Pessoa", backref=backref("responsavel", order_by=data_responsavel))

class TipoDocumento(Base):
    implements(interfaces.ITipoDocumento)
    __tablename__ = 'tipodocumento'
    __table_args__ = TABLE_ARGS
    id = Column(Integer, primary_key=True)
    nome = Column(String(40), unique=True, nullable=False)

class Situacao(Base):
    implements(interfaces.ISituacao)
    __tablename__ = 'situacao'
    __table_args__ = TABLE_ARGS
    id = Column(Integer, primary_key=True)
    nome = Column(String(40), unique=True, nullable=False)
    inicial = Column(Boolean(), default=False)
    final = Column(Boolean(), default=False)

class PessoaOrigem(Base):
    implements(interfaces.IPessoaOrigem)
    __tablename__ = 'pessoa_origem'
    __table_args__ = TABLE_ARGS
    protocolo_id = Column(Integer, ForeignKey('protocolo.id'), primary_key=True)
    pessoa_id = Column(Integer, ForeignKey('pessoa.id'), primary_key=True)
    pessoa = relationship("Pessoa", backref="pessoa_origem")

class TipoEntrega(Base):
    implements(interfaces.ITipoEntrega)
    __tablename__ = 'tipoentrega'
    __table_args__ = TABLE_ARGS
    id = Column(Integer, primary_key=True)
    nome = Column(String(40), unique=True, nullable=False)

class PessoaDestino(Base):
    implements(interfaces.IPessoaDestino, interfaces.IEntrega)
    __tablename__ = 'pessoa_destino'
    __table_args__ = TABLE_ARGS
    protocolo_id = Column(Integer, ForeignKey('protocolo.id'), primary_key=True)
    pessoa_id = Column(Integer, ForeignKey('pessoa.id'), primary_key=True)
    pessoa = relationship("Pessoa", backref="pessoa_destino")
    tipoentrega_id = Column(Integer, ForeignKey('tipoentrega.id'))
    tipoentrega = relationship("TipoEntrega", backref="pessoa_destino")
    data_entrega = Column(DateTime())
    objeto_correios = Column(String(20))

class Observacao(Base):
    implements(interfaces.IObservacao)
    __tablename__ = 'observacao'
    __table_args__ = TABLE_ARGS
    id = Column(Integer, primary_key=True)
    protocolo_id = Column(Integer, ForeignKey('protocolo.id'))
    texto = Column(Text(), nullable=False)
    data_observacao = Column(DateTime(), default=datetime.datetime.now, nullable=False)
    usuario = Column(String(254), nullable=False)

class Anexo(Base):
    implements(interfaces.IAddAnexo)
    __tablename__ = 'anexo'
    __table_args__ = TABLE_ARGS
    id = Column(Integer, primary_key=True)
    protocolo_id = Column(Integer, ForeignKey('protocolo.id'))
    arquivo = Column(Text(), nullable=False)
    tamanho = Column(Integer(), nullable=False)
    data_anexo = Column(DateTime(), default=datetime.datetime.now, nullable=False)
    usuario = Column(String(254), nullable=False)

"""
Há 3 tabelas que merecem alguns comentários, pois seu funcionamento
não é trivial. A tabela "Tramite" armazena o histórico da tramitação
de um protocolo. As tabelas TramiteInbox e TramiteOutbox podem ser
encaradas como estruturas auxiliares. A tabela "TramiteInbox" simula a
caixa de entrada de uma determinada área, armazenando referências para
todos os protocolos recebidos. Por sua vez, a tabela "TramiteOutbox"
simula a caixa de saída, armazenando referências para todos os
protocolos enviados enviados e ainda não recebidos.
"""

class Tramite(Base):
    implements(interfaces.IAddTramite)
    __tablename__ = 'tramite'
    __table_args__ = TABLE_ARGS
    id = Column(Integer, primary_key=True)
    protocolo_id = Column(Integer, ForeignKey('protocolo.id'))
    area_id = Column(Integer, ForeignKey('area.id'))
    area = relationship("Area", primaryjoin=(area_id==Area.id), backref="tramite")
    data_disponibilizacao = Column(DateTime())
    data_recebimento = Column(DateTime())
    despacho = Column(Text())
    copia = Column(Boolean(), default=False)
    area_id_anterior = Column(Integer, ForeignKey('area.id'))
    area_anterior = relationship("Area", primaryjoin=(area_id_anterior==Area.id), backref="tramite_anterior")
    responsavel_id = Column(Integer, ForeignKey('responsavel.id'))
    responsavel = relationship("Responsavel", backref="tramite")
    usuario = Column(String(254), nullable=False)

    def __init__(self, protocolo_id, area_id, data_disponibilizacao, data_recebimento, despacho, usuario, copia=False, area_id_anterior=None):
        self.protocolo_id = protocolo_id
        self.area_id = area_id
        self.data_disponibilizacao = data_disponibilizacao
        self.data_recebimento = data_recebimento
        self.despacho = despacho
        self.copia = copia
        self.area_id_anterior = area_id_anterior
        # o responsável pelo tramite é o responsável atual da área de destino
        session = Session()
        self.responsavel_id = session.query(Responsavel.id).filter_by(area_id=area_id).\
                              order_by(Responsavel.data_responsavel).all()[-1][0]
        self.usuario = usuario

def calculaDigitoVerificador(seq, ano):
    return int(math.log(seq + ano) * 10000) % 100

class Protocolo(Base):
    implements(interfaces.IAddProtocolo, 
               interfaces.IEditProtocolo, 
               interfaces.IApenso)
    __tablename__ = 'protocolo'
    __table_args__ = TABLE_ARGS
    id = Column(Integer, primary_key=True)
    tipoprotocolo = Column(String(1), nullable=False)
    seq = Column(Integer, nullable=False)
    ano = Column(Integer, nullable=False)
    dv = Column(Integer, nullable=False)
    numero = Column(String(18), unique=True, nullable=False)
    data_protocolo = Column(DateTime(), default=datetime.datetime.now, nullable=False)
    tipodocumento_id = Column(Integer, ForeignKey('tipodocumento.id'))
    tipodocumento = relationship("TipoDocumento", backref="protocolo")
    numero_documento = Column(String(20))
    data_emissao = Column(DateTime())
    assunto = Column(String(100), nullable=False)
    situacao_id = Column(Integer, ForeignKey('situacao.id'))
    situacao = relationship("Situacao", backref="protocolo")
    apenso_id = Column(Integer, ForeignKey('protocolo.id'))
    apenso = relationship("Protocolo", backref=backref('apensado', remote_side=id))
    pessoa_origem = relationship("PessoaOrigem", backref="pessoa_origem")
    pessoa_destino = relationship("PessoaDestino", backref="pessoa_destino")
    observacao = relationship("Observacao", backref="protocolo")
    anexo = relationship("Anexo", backref="protocolo")
    tramite = relationship("Tramite", backref="protocolo")
    usuario = Column(String(254), nullable=False)
    
    def __init__(self, tipoprotocolo, tipodocumento_id, numero_documento, data_emissao, assunto, situacao_id, usuario):
        self.tipoprotocolo = tipoprotocolo
        self.tipodocumento_id = tipodocumento_id
        self.numero_documento = numero_documento
        self.data_emissao = data_emissao
        self.assunto = assunto
        self.situacao_id = situacao_id
        self.usuario = usuario
        session = Session()

        # TODO: isso não poderia ser feito dessa maneira, pois desconsidera o session e requer um commit ao invez de um flush
        self.ano = datetime.datetime.now().year
        max_seq = session.bind.execute('SELECT max(p.seq) from protocolo p where p.ano = %d' % self.ano).fetchone()[0]
        self.seq = max_seq is None and 1 or max_seq + 1
        self.dv = calculaDigitoVerificador(self.seq, self.ano)
        self.numero = "%s-%08d/%04d-%02d" % (tipoprotocolo, self.seq, self.ano, self.dv)

    def __repr__(self):
        return "<Protocolo:%s>" % self.numero

class TramiteInbox(Base):
    __tablename__ = 'tramite_inbox'
    __table_args__ = TABLE_ARGS
    protocolo_id = Column(Integer, ForeignKey('protocolo.id'), primary_key=True)
    protocolo = relationship("Protocolo", backref="tramite_inbox")
    area_id = Column(Integer, ForeignKey('area.id'), primary_key=True)
    area = relationship("Area", backref="tramite_inbox")

class TramiteOutbox(Base):
    __tablename__ = 'tramite_outbox'
    __table_args__ = TABLE_ARGS
    protocolo_id = Column(Integer, ForeignKey('protocolo.id'), primary_key=True)
    protocolo = relationship("Protocolo", backref="tramite_outbox")
    area_id = Column(Integer, ForeignKey('area.id'), primary_key=True)
    area = relationship("Area", backref="tramite_outbox")

class Referencia(Base):
    implements(interfaces.IAddReferencia)
    __tablename__ = 'referencia'
    __table_args__ = TABLE_ARGS
    protocolo_id = Column(Integer, ForeignKey('protocolo.id'), primary_key=True)
    protocolo = relationship("Protocolo", primaryjoin=(protocolo_id==Protocolo.id), backref="protocolo")
    referencia_id = Column(Integer, ForeignKey('protocolo.id'), primary_key=True)
    referencia = relationship("Protocolo", primaryjoin=(referencia_id==Protocolo.id), backref="referencia")

class Notificacao(Base):
    implements(interfaces.IAddNotificacao)
    __tablename__ = 'notificacao'
    __table_args__ = TABLE_ARGS
    pessoa_id = Column(Integer, ForeignKey('pessoa.id'), primary_key=True)
    pessoa = relationship("Pessoa", backref="notificacao")
    protocolo_id = Column(Integer, ForeignKey('protocolo.id'), primary_key=True)
    protocolo = relationship("Protocolo", backref="notificacao")

class Transicao(Base):
    implements(interfaces.IAddTransicao)
    __tablename__ = 'transicao'
    __table_args__ = (
        UniqueConstraint('fluxo_id', 'area_origem_id', 'area_destino_id', name="uc_transicao"),
        TABLE_ARGS,
        )
    id = Column(Integer, primary_key=True)
    fluxo_id = Column(Integer, ForeignKey('fluxo.id'))
    inicial = Column(Boolean(), default=False)
    area_origem_id = Column(Integer, ForeignKey('area.id'))
    area_origem = relationship("Area", primaryjoin=(area_origem_id==Area.id), backref="area_origem")
    area_destino_id = Column(Integer, ForeignKey('area.id'))
    area_destino = relationship("Area", primaryjoin=(area_destino_id==Area.id), backref="area_destino")

class Fluxo(Base):
    implements(interfaces.IFluxo)
    __tablename__ = 'fluxo'
    __table_args__ = (
        UniqueConstraint('tipoprotocolo', 'tipodocumento_id', name="uc_fluxo"),
        TABLE_ARGS,
        )
    id = Column(Integer, primary_key=True)
    nome = Column(String(40), unique=True, nullable=False)
    tipoprotocolo = Column(String(1), nullable=False)
    tipodocumento_id = Column(Integer, ForeignKey('tipodocumento.id'), nullable=False)
    tipodocumento = relationship("TipoDocumento", backref="fluxo")
    flexivel = Column(Boolean(), default=False)
    transicao = relationship("Transicao", backref="fluxo")

class Log(Base):
    __tablename__ = 'log'
    __table_args__ = TABLE_ARGS
    id = Column(Integer, primary_key=True)
    usuario = Column(String(254), nullable=False)
    url = Column(Text(), nullable=False)
    modulo = Column(Text())
    classe = Column(Text())
    funcao = Column(Text())
    args = Column(Text())
    kwargs = Column(Text())

if __name__ == '__main__':

    if CREATE_ALL_TABLES:
        metadata = Base.metadata
        metadata.drop_all(engine)
        metadata.create_all(engine)

    if not CREATE_SAMPLES:
        sys.exit()

    session = Session()

    # Area
    a1 = Area(sigla='t1', nome='Teste1')
    session.add(a1)
    session.flush()
    a2 = Area(sigla='t2', nome='Teste2', chefia_id=a1.id)
    session.add(a2)
    session.flush()
    a3 = Area(sigla='t3', nome='Teste3', chefia_id=a2.id)
    session.add(a3)
    session.flush()

    # UF
    UFs = """
          AC Acre
          AL Alagoas
          AP Amapá
          AM Amazonas
          BA Bahia
          CE Ceará
          DF Distrito Federal
          ES Espirito Santo
          GO Goiás
          MA Maranhão
          MT Mato Grosso
          MS Mato Grosso do Sul
          MG Minas Gerais
          PA Pará
          PB Paraíba
          PR Paraná
          PE Pernanbuco
          PI Piauí
          RJ Rio de Janeiro
          RN Rio Grande do Norte
          RS Rio Grande do Sul
          RO Rondônia
          RR Roraima
          SC Santa Catarina
          SP São Paulo
          SE Sergipe
          TO Tocantins
          """
    UFs = [{'sigla':uf.strip().split()[0], 
            'nome':" ".join(uf.strip().split()[1:])} \
            for uf in UFs.split('\n') if uf.strip()]
    for uf in UFs:
        uf1 = UF(sigla=uf['sigla'], nome=uf['nome'])
        session.add(uf1)

    # Pessoa
    ps1 = Pessoa(u'Xiru', u'xiru@xiru.org', area_id=a1.id)
    session.add(ps1)
    ps2 = Pessoa(u'Tião Macalé', u'tiao@macale.net', area_id=a2.id)
    session.add(ps2)
    ps3 = Pessoa(u'ZÉ Pequeno', u'john@small.org', 'Rua dos bobos, 0', 'Centro', 95096000, 
                 'Caxias do Sul', 1, '54 3226.1234', '12312312312', 'F', 'Baiano', a3.id)
    session.add(ps3)
    ps4 = Pessoa(u'BOPE', 'cpt.nascimento@bope.gov.br', 'Morro dos Caveiras, 100', u'Favela do Alemão', 12312000,
                 'Rio de Janeiro', 1, '11 1212.1234', '12312312312', 'O', u'Capitão Nascimento', a3.id)
    session.add(ps4)
    ps5 = Pessoa(u'Fabiano Weimar', u'xirumacanudo@gmail.com', area_id=a1.id)
    session.add(ps5)
    if LOTS_OF_SAMPLES:
        for i in xrange(1000):
            psN = Pessoa(u'Teste %s...' % str(i), u'xiru%s@xiru.org' % str(i), area_id=a1.id)
            session.add(psN)

    session.flush()

    # BUG: a pessoa com id = 1 deve ser apagada pois o plone.formwidget.autocomplete
    # não funciona como esperado com esse registro. No futuro esse widget precisará
    # ser reescrito utilizando http://docs.jquery.com/UI/Autocomplete
    session.delete(ps1)

    # Para facilitar os testes, algumas senhas são trocadas para senhas
    ps2.senha = geraHash('12345')
    ps3.senha = geraHash('54321')

    # Responsavel
    re1 = Responsavel(area_id=a1.id, pessoa_id=ps2.id)
    session.add(re1)
    re2 = Responsavel(area_id=a2.id, pessoa_id=ps3.id)
    session.add(re2)
    re3 = Responsavel(area_id=a3.id, pessoa_id=ps4.id)
    session.add(re3)
    re4 = Responsavel(area_id=a1.id, pessoa_id=ps3.id)
    session.add(re4)
    re5 = Responsavel(area_id=a2.id, pessoa_id=ps4.id)
    session.add(re5)
    re6 = Responsavel(area_id=a3.id, pessoa_id=ps2.id)
    session.add(re6)

    # TipoDocumento
    td1 = TipoDocumento(nome='Projeto')
    session.add(td1)
    td2 = TipoDocumento(nome='Parecer')
    session.add(td2)
    td3 = TipoDocumento(nome='Carta')
    session.add(td3)

    # Situacao
    st1 = Situacao(nome='Tramitando', inicial = True)
    session.add(st1)
    st2 = Situacao(nome='Em Análise')
    session.add(st2)
    st3 = Situacao(nome='Arquivado', final = True)
    session.add(st3)

    # TipoEntrega
    te1 = TipoEntrega(nome='Pessoalmente')
    session.add(te1)
    te2 = TipoEntrega(nome='SEDEX')
    session.add(te2)
    te3 = TipoEntrega(nome='email')
    session.add(te3)

    session.flush()

    USUARIO = 'tiao@macale.net'
    
    # Protocolo
    pt1 = Protocolo('I', td1.id, None, None, '...', st1.id, USUARIO)
    session.add(pt1)
    session.commit()
    pt2 = Protocolo('R', td1.id, '123', None, 'Assunto 1...', st1.id, USUARIO)
    session.add(pt2)
    session.commit()
    pt3 = Protocolo('E', td2.id, '456-X', datetime.date.today(), 'Assunto 2...', st2.id, USUARIO)
    session.add(pt3)
    session.commit()
    pt4 = Protocolo('E', td3.id, None, None, 'Assunto 3...', st3.id, USUARIO)
    session.add(pt4)
    session.commit()

    # BUG: o mesmo bug que ocorre com pessoa com id = 1 ocorre com o 
    # protocolo com id = 1
    session.delete(pt1)

    # Pessoa de Origem
    po1 = PessoaOrigem(protocolo_id=pt2.id, pessoa_id=ps4.id)
    session.add(po1)
    po2 = PessoaOrigem(protocolo_id=pt3.id, pessoa_id=ps2.id)
    session.add(po2)
    po3 = PessoaOrigem(protocolo_id=pt4.id, pessoa_id=ps3.id)
    session.add(po3)
    po4 = PessoaOrigem(protocolo_id=pt4.id, pessoa_id=ps4.id)
    session.add(po4)

    # Pessoa de Destino
    pd1 = PessoaDestino(protocolo_id=pt2.id, pessoa_id=ps2.id)
    session.add(pd1)
    pd2 = PessoaDestino(protocolo_id=pt2.id, pessoa_id=ps3.id)
    session.add(pd2)
    pd3 = PessoaDestino(protocolo_id=pt3.id, pessoa_id=ps4.id, tipoentrega_id=te2.id, objeto_correios='RM283505565BR')
    session.add(pd3)
    pd4 = PessoaDestino(protocolo_id=pt4.id, pessoa_id=ps2.id, tipoentrega_id=te3.id, data_entrega=datetime.date.today())
    session.add(pd4)

    if LOTS_OF_SAMPLES:
        for i in xrange(10000):
            ptN = Protocolo('I', td1.id, None, None, 'Teste %s...' % str(i), st1.id, USUARIO)
            session.add(ptN)
            session.commit()
            poN = PessoaOrigem(protocolo_id=ptN.id, pessoa_id=ps2.id)
            session.add(poN)
            pdN = PessoaDestino(protocolo_id=ptN.id, pessoa_id=ps3.id)
            session.add(pdN)
    
    # Referências
    rf1 = Referencia(protocolo_id=pt4.id, referencia_id=pt2.id)
    session.add(rf1)
    rf2 = Referencia(protocolo_id=pt4.id, referencia_id=pt3.id)
    session.add(rf2)
    
    # Notificacao
    nt1 = Notificacao(pessoa_id=ps2.id, protocolo_id=pt2.id)
    session.add(nt1)
    nt2 = Notificacao(pessoa_id=ps2.id, protocolo_id=pt3.id)
    session.add(nt2)
    nt3 = Notificacao(pessoa_id=ps2.id, protocolo_id=pt4.id)
    session.add(nt3)
    
    # Observacao
    ob1 = Observacao(protocolo_id=pt4.id, texto='Texto 1', usuario=USUARIO)
    session.add(ob1)
    ob2 = Observacao(protocolo_id=pt4.id, texto='Texto 2', usuario=USUARIO)
    session.add(ob2)
    ob3 = Observacao(protocolo_id=pt3.id, texto='Texto 3', usuario=USUARIO)
    session.add(ob3)
    ob4 = Observacao(protocolo_id=pt3.id, texto='Texto 4', usuario=USUARIO)
    session.add(ob4)
    
    # Anexo
    an1 = Anexo(protocolo_id=pt4.id, arquivo='documento.txt', tamanho=1000, usuario=USUARIO)
    session.add(an1)
    an2 = Anexo(protocolo_id=pt4.id, arquivo='documento2.doc', tamanho=2000, usuario=USUARIO)
    session.add(an2)
    an3 = Anexo(protocolo_id=pt2.id, arquivo='apresent.ppt', tamanho=3000, usuario=USUARIO)
    session.add(an3)
    an4 = Anexo(protocolo_id=pt2.id, arquivo='apresent2.ppt', tamanho=4000, usuario=USUARIO)
    session.add(an4)

    # Tramite
    data = datetime.datetime.now()
    for pt in (pt2, pt3, pt4):
        tr = Tramite(pt.id, a2.id, None, data, 'Protocolo Criado', USUARIO)
        session.add(tr)
        ti = TramiteInbox()
        ti.protocolo_id = pt.id
        ti.area_id = a2.id
        session.add(ti)

    session.commit()
