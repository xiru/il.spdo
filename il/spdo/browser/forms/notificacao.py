# -*- coding: utf-8 -*-

from five import grok
from zope.component import getUtility
from plone.app.layout.navigation.interfaces import INavigationRoot

from il.spdo.browser.forms import base
from il.spdo.config import MessageFactory as _
from il.spdo.config import Session
from il.spdo.interfaces import IAddNotificacao
from il.spdo.db import Notificacao, nextVersion
from il.spdo.log import log
from il.spdo.nav import go
from il.spdo.interfaces import ISPDOAPI, ISecurityChecker

class NotificacaoAddForm(base.AddForm):
    """Formulário de cadastro de notificações.
    """

    grok.context(INavigationRoot)
    grok.name('add-notificacao')
    grok.require('zope2.View')

    schema = IAddNotificacao
    klass = Notificacao
    label = _(u'Adicionar Notificações')
    description = _(u'Formulário de cadastro de notificações.')

    def update(self):
        sc = getUtility(ISecurityChecker)
        sc.enforce('acessar_add_notificacao', ajax=True)
        super(NotificacaoAddForm, self).update()

    @log
    def createAndAdd(self, data):
        api = getUtility(ISPDOAPI)
        pessoa_id = api.getAuthPessoa().id
        session = Session()
        for i in data['protocolo_id']:
            notificacao = Notificacao()
            notificacao.pessoa_id = pessoa_id
            notificacao.protocolo_id = i
            notificacao.version = nextVersion('notificacao', pessoa_id=pessoa_id, protocolo_id=i)
            session.add(notificacao)
        session.flush()

    def nextURL(self):
        go('list-notificacao')
