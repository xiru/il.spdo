# -*- coding: utf-8 -*-

from five import grok
from zope.component import getUtility
from plone.app.layout.navigation.interfaces import INavigationRoot

from il.spdo.browser.forms import base
from il.spdo.config import MessageFactory as _
from il.spdo.interfaces import IObservacao
from il.spdo.db import Observacao
from il.spdo.log import log
from il.spdo.nav import go
from il.spdo.interfaces import ISPDOAPI, ISecurityChecker

class ObservacaoAddForm(base.AddForm):
    """Formulário de cadastro de observações.
    """

    grok.context(INavigationRoot)
    grok.name('add-observacao')
    grok.require('zope2.View')

    schema = IObservacao
    klass = Observacao
    label = _(u'Adicionar Observação')
    description = _(u'Formulário de cadastro de observações.')

    def update(self):
        sc = getUtility(ISecurityChecker)
        sc.enforce('acessar_add_observacao')
        super(ObservacaoAddForm, self).update()

    @log
    def createAndAdd(self, data):
        api = getUtility(ISPDOAPI)
        protocolo_id = api.getProtocoloId()
        api.addObservacao(protocolo_id, data['texto'])

    def nextURL(self):
        api = getUtility(ISPDOAPI)
        protocolo_id = api.getProtocoloId()
        go('show-protocolo', id=protocolo_id)

class ObservacaoEditForm(base.EditForm):
    """Formulário de edição de uma observação.
    """

    grok.context(INavigationRoot)
    grok.name('edit-observacao')
    grok.require('zope2.View')

    schema = IObservacao
    klass = Observacao
    label = _(u'Editar Observação')
    descrition = _(u'Formulário de edição de uma observação.')

    def update(self):
        r = self.request
        protocolo_id = r.get('protocolo_id', r.get('form.widgets.protocolo_id', None))
        observacao_id = r.get('id', r.get('form.widgets.id', None))
        sc = getUtility(ISecurityChecker)
        sc.enforce('acessar_edit_observacao', protocolo_id=protocolo_id, observacao_id=observacao_id)
        super(ObservacaoEditForm, self).update()

    @log
    def applyChanges(self, data):
        content = self.getContent()
        if not content:
            return
        for k, v in data.items():
            setattr(content, k, v)
        api = getUtility(ISPDOAPI)
        content.usuario = api.getAuthId()

    def nextURL(self):
        api = getUtility(ISPDOAPI)
        protocolo_id = api.getProtocoloId()
        go('show-protocolo', id=protocolo_id)
