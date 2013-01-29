# -*- coding: utf-8 -*-

from five import grok
from zope.component import getUtility
from plone.app.layout.navigation.interfaces import INavigationRoot

from il.spdo.browser.forms import base
from il.spdo.config import MessageFactory as _
from il.spdo.config import Session
from il.spdo.interfaces import IPessoaOrigem
from il.spdo.db import PessoaOrigem, nextVersion
from il.spdo.log import log
from il.spdo.nav import go
from il.spdo.interfaces import ISPDOAPI, ISecurityChecker

class PessoaOrigemAddForm(base.AddForm):
    """Formulário de cadastro de origens.
    """

    grok.context(INavigationRoot)
    grok.name('add-pessoaorigem')
    grok.require('zope2.View')

    schema = IPessoaOrigem
    klass = PessoaOrigem
    label = _(u'Adicionar Origem')
    description = _(u'Formulário de cadastro de origens.')

    def update(self):
        sc = getUtility(ISecurityChecker)
        sc.enforce('acessar_add_pessoaorigem', ajax=True)
        super(PessoaOrigemAddForm, self).update()

    @log
    def createAndAdd(self, data):
        api = getUtility(ISPDOAPI)
        protocolo_id = api.getProtocoloId()
        session = Session()
        for i in data['pessoa_id']:
            pessoaorigem = PessoaOrigem()
            pessoaorigem.protocolo_id = protocolo_id
            pessoaorigem.pessoa_id = i
            pessoaorigem.version = nextVersion('pessoa_origem', protocolo_id=protocolo_id, pessoa_id=i)
            session.add(pessoaorigem)
        session.flush()

    def nextURL(self):
        api = getUtility(ISPDOAPI)
        protocolo_id = api.getProtocoloId()
        go('show-protocolo', id=protocolo_id)
