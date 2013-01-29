# -*- coding: utf-8 -*-

from five import grok
from zope.component import getUtility
from plone.app.layout.navigation.interfaces import INavigationRoot

from il.spdo.browser.forms import base
from il.spdo.config import MessageFactory as _
from il.spdo.interfaces import IAddAnexo
from il.spdo.db import Anexo
from il.spdo.log import log
from il.spdo.nav import go
from il.spdo.interfaces import ISPDOAPI, ISecurityChecker

class AnexoAddForm(base.AddForm):
    """Formulário de cadastro de anexos.
    """

    grok.context(INavigationRoot)
    grok.name('add-anexo')
    grok.require('zope2.View')

    schema = IAddAnexo
    klass = Anexo
    label = _(u'Adicionar Anexos')
    description = _(u'Formulário de cadastro de anexos.')

    def update(self):
        sc = getUtility(ISecurityChecker)
        sc.enforce('acessar_add_anexo')
        super(AnexoAddForm, self).update()

    @log
    def createAndAdd(self, data):
        api = getUtility(ISPDOAPI)
        protocolo_id = api.getProtocoloId()
        return api.addAnexos(protocolo_id, data['anexos'])

    def nextURL(self):
        api = getUtility(ISPDOAPI)
        protocolo_id = api.getProtocoloId()
        go('show-protocolo', id=protocolo_id)
