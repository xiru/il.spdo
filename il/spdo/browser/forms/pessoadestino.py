# -*- coding: utf-8 -*-

from five import grok
from zope.component import getUtility
from plone.app.layout.navigation.interfaces import INavigationRoot

from il.spdo.browser.forms import base
from il.spdo.config import MessageFactory as _
from il.spdo.config import Session
from il.spdo.interfaces import IPessoaDestino, IEntrega
from il.spdo.db import PessoaDestino, nextVersion
from il.spdo.log import log
from il.spdo.nav import go
from il.spdo.interfaces import ISPDOAPI, ISecurityChecker

class PessoaDestinoAddForm(base.AddForm):
    """Formulário de cadastro de destinatários.
    """

    grok.context(INavigationRoot)
    grok.name('add-pessoadestino')
    grok.require('zope2.View')

    schema = IPessoaDestino
    klass = PessoaDestino
    label = _(u'Adicionar Destinatário')
    description = _(u'Formulário de cadastro de destinatários.')

    def update(self):
        sc = getUtility(ISecurityChecker)
        sc.enforce('acessar_add_pessoadestino', ajax=True)
        super(PessoaDestinoAddForm, self).update()

    @log
    def createAndAdd(self, data):
        api = getUtility(ISPDOAPI)
        protocolo_id = api.getProtocoloId()
        session = Session()
        for i in data['pessoa_id']:
            pessoadestino = PessoaDestino()
            pessoadestino.protocolo_id = protocolo_id
            pessoadestino.pessoa_id = i
            pessoadestino.version = nextVersion('pessoa_destino', protocolo_id=protocolo_id, pessoa_id=i)
            session.add(pessoadestino)
        session.flush()

    def nextURL(self):
        api = getUtility(ISPDOAPI)
        protocolo_id = api.getProtocoloId()
        go('show-protocolo', id=protocolo_id)

class PessoaDestinoEditForm(base.EditForm):
    """Formulário de edição dos dados de entrega.
    """

    grok.context(INavigationRoot)
    grok.name('edit-pessoadestino')
    grok.require('zope2.View')

    schema = IEntrega
    klass = PessoaDestino
    label = _(u'Editar Entrega')
    descrition = _(u'Formulário de edição dos dados de entrega.')

    def update(self):
        sc = getUtility(ISecurityChecker)
        sc.enforce('acessar_edit_pessoadestino')
        super(PessoaDestinoEditForm, self).update()

    def getContent(self):
        r = self.request
        protocolo_id = r.get('protocolo_id', r.get('form.widgets.protocolo_id', None))
        pessoa_id = r.get('pessoa_id', r.get('form.widgets.pessoa_id', None))
        session = Session()
        return session.query(PessoaDestino).get((protocolo_id, pessoa_id))

    def nextURL(self):
        api = getUtility(ISPDOAPI)
        protocolo_id = api.getProtocoloId()
        go('show-protocolo', id=protocolo_id)
