# -*- coding: utf-8 -*-

from zope.interface import implements
from zope.component import provideUtility
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.interfaces import IContextSourceBinder
from z3c.formwidget.query.interfaces import IQuerySource

from il.spdo.config import Session
from il.spdo import db
from il.spdo.config import MessageFactory as _
from il.spdo.etiquetas import FORMATOS_SUPORTADOS


class BaseQueryVocabulary(object):

    implements(IVocabularyFactory, IQuerySource)

    vocab = None

    def update(self):
        raise NotImplementedError

    def __call__(self, context):
        self.vocab = self.update()
        return self
 
    def __contains__(self, term):
        return self.vocab.__contains__(term)

    def __iter__(self):
        return self.vocab.__iter__()
 
    def __len__(self):
        return self.vocab.__len__()
 
    def getTerm(self, value):
        return self.vocab.getTerm(value)
 
    def getTermByToken(self, value):
        return self.vocab.getTermByToken(value)
 
    def search(self, query_string):
        q = query_string.lower()
        return [x for x in self if x.title.lower().find(q) != -1]


class PessoaVocabulary(BaseQueryVocabulary):

    def update(self):
         session = Session()
         query = session.query(db.Pessoa).order_by(db.Pessoa.nome).all()
         return SimpleVocabulary([SimpleTerm(p.id, p.id, p.nome) for p in query])

PessoaVocabularyFactory = PessoaVocabulary()
provideUtility(PessoaVocabularyFactory, IVocabularyFactory,
               name='il.spdo.pessoa-vocab')


class ProtocoloVocabulary(BaseQueryVocabulary):

    def update(self):
         session = Session()
         query = session.query(db.Protocolo).order_by(db.Protocolo.numero).all()
         return SimpleVocabulary([SimpleTerm(p.id, p.id, p.numero) for p in query])

ProtocoloVocabularyFactory = ProtocoloVocabulary()
provideUtility(ProtocoloVocabularyFactory, IVocabularyFactory,
               name='il.spdo.protocolo-vocab')

               
class AreasVocabulary(object):

    implements(IVocabularyFactory)

    def __call__(self, context):
        session = Session()
        areas = session.query(db.Area).order_by(db.Area.nome).all()
        return SimpleVocabulary([SimpleTerm(a.id, a.id, a.nome) for a in areas])

AreasVocabularyFactory = AreasVocabulary()
provideUtility(AreasVocabularyFactory, IVocabularyFactory,
               name='il.spdo.areas-vocab')

               
class TipoDocumentoVocabulary(object):

    implements(IVocabularyFactory)

    def __call__(self, context):
        session = Session()
        query = session.query(db.TipoDocumento).order_by(db.TipoDocumento.nome).all()
        return SimpleVocabulary([SimpleTerm(t.id, t.id, t.nome) for t in query])

TipoDocumentoVocabularyFactory = TipoDocumentoVocabulary()
provideUtility(TipoDocumentoVocabularyFactory, IVocabularyFactory,
               name='il.spdo.tipodocumento-vocab')

               
class SituacaoInicialVocabulary(object):

    implements(IVocabularyFactory)

    def __call__(self, context):
        session = Session()
        query = session.query(db.Situacao).filter_by(inicial=True).order_by(db.Situacao.nome).all()
        return SimpleVocabulary([SimpleTerm(s.id, s.id, s.nome) for s in query])

SituacaoInicialVocabularyFactory = SituacaoInicialVocabulary()
provideUtility(SituacaoInicialVocabularyFactory, IVocabularyFactory,
               name='il.spdo.situacao-inicial-vocab')

               
class SituacaoAtualVocabulary(object):

    implements(IVocabularyFactory)

    def __call__(self, context):
        session = Session()
        query = session.query(db.Situacao).order_by(db.Situacao.nome).all()
        return SimpleVocabulary([SimpleTerm(s.id, s.id, s.nome) for s in query])

SituacaoAtualVocabularyFactory = SituacaoAtualVocabulary()
provideUtility(SituacaoAtualVocabularyFactory, IVocabularyFactory,
               name='il.spdo.situacao-atual-vocab')

               
class UFVocabulary(object):

    implements(IVocabularyFactory)

    def __call__(self, context):
        session = Session()
        query = session.query(db.UF).order_by(db.UF.nome).all()
        return SimpleVocabulary([SimpleTerm(a.id, a.id, a.nome) for a in query])

UFVocabularyFactory = UFVocabulary()
provideUtility(UFVocabularyFactory, IVocabularyFactory,
               name='il.spdo.uf-vocab')


class TipoEntregaVocabulary(object):

    implements(IVocabularyFactory)

    def __call__(self, context):
        session = Session()
        query = session.query(db.TipoEntrega).order_by(db.TipoEntrega.nome).all()
        return SimpleVocabulary([SimpleTerm(t.id, t.id, t.nome) for t in query])

TipoEntregaVocabularyFactory = TipoEntregaVocabulary()
provideUtility(TipoEntregaVocabularyFactory, IVocabularyFactory,
               name='il.spdo.tipoentrega-vocab')

               
def TipoPessoaVocabulary(context):
    return SimpleVocabulary([
        SimpleTerm('F','F', _(u'Física')),
        SimpleTerm('O','O', _(u'Organização')),
    ])

provideUtility(TipoPessoaVocabulary, IVocabularyFactory,
               name='il.spdo.tipopessoa-vocab')

               
def TipoProtocoloVocabulary(context):
    return SimpleVocabulary([
        SimpleTerm('R','R', _(u'Recebido')),
        SimpleTerm('E','E', _(u'Expedido')),
        SimpleTerm('I','I', _(u'Interno')),
    ])

provideUtility(TipoProtocoloVocabulary, IVocabularyFactory,
               name='il.spdo.tipoprotocolo-vocab')


def FormatoEtiquetaVocabulary(context):
    ret = []
    for k, v in FORMATOS_SUPORTADOS.items():
        ret.append(SimpleTerm(k, k, _(u'Tipo: %d, Papel: %s, %d linhas x %d colunas (PIMACO: %s)' % (
                                      k, v['Papel'], v['Linhas'], v['Colunas'], v['Codigo']))))
    return SimpleVocabulary(ret)

provideUtility(FormatoEtiquetaVocabulary, IVocabularyFactory,
               name='il.spdo.formato-vocab')
