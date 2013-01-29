# -*- coding: utf-8 -*-

from five import grok
from zope.component import getUtility
from plone.app.layout.navigation.interfaces import INavigationRoot

from il.spdo.browser.forms import base
from il.spdo.config import MessageFactory as _
from il.spdo.config import Session
from il.spdo.interfaces import IAddReferencia
from il.spdo.db import Referencia, nextVersion
from il.spdo.log import log
from il.spdo.nav import go
from il.spdo.interfaces import ISPDOAPI, ISecurityChecker

class ReferenciaAddForm(base.AddForm):
    """Formulário de cadastro de referências.
    """

    grok.context(INavigationRoot)
    grok.name('add-referencia')
    grok.require('zope2.View')

    schema = IAddReferencia
    klass = Referencia
    label = _(u'Adicionar Referências')
    description = _(u'Formulário de cadastro de referências.')

    def update(self):
        sc = getUtility(ISecurityChecker)
        sc.enforce('acessar_add_referencia', ajax=True)
        super(ReferenciaAddForm, self).update()

    @log
    def createAndAdd(self, data):
        api = getUtility(ISPDOAPI)
        protocolo_id = api.getProtocoloId()
        session = Session()
        for i in data['referencia_id']:
            # garante que o protocolo não faz referência para ele mesmo
            if protocolo_id == i:
                continue
            referencia = Referencia()
            referencia.protocolo_id = protocolo_id
            referencia.referencia_id = i
            referencia.version = nextVersion('referencia', protocolo_id=protocolo_id, referencia_id=i)
            session.add(referencia)
        session.flush()

    def nextURL(self):
        api = getUtility(ISPDOAPI)
        protocolo_id = api.getProtocoloId()
        go('list-referencia', protocolo_id=protocolo_id)
