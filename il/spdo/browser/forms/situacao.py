# -*- coding: utf-8 -*-

from five import grok
from plone.app.layout.navigation.interfaces import INavigationRoot

from il.spdo.browser.forms import base
from il.spdo.config import MessageFactory as _
from il.spdo.config import Session
from il.spdo.interfaces import ISituacao
from il.spdo.db import Situacao
from il.spdo.log import log

class SituacaoAddForm(base.AddForm):
    """Formulário de cadastro de uma situação.
    """

    grok.context(INavigationRoot)
    grok.name('add-situacao')
    grok.require('cmf.ManagePortal')

    schema = ISituacao
    klass = Situacao
    label = _(u'Adicionar Situação')
    description = _(u'Formulário de cadastro de uma situação.')

    @log
    def createAndAdd(self, data):
        situacao = Situacao()
        situacao.nome = data['nome']
        situacao.inicial = data['inicial']
        situacao.final = data['final']
        session = Session()
        session.add(situacao)
        session.flush()

class SituacaoEditForm(base.EditForm):
    """Formulário de edição de uma situação.
    """

    grok.context(INavigationRoot)
    grok.name('edit-situacao')
    grok.require('cmf.ManagePortal')

    schema = ISituacao
    klass = Situacao
    label = _(u'Editar Situação')
    descrition = _(u'Formulário de edição de uma situação.')

class SituacaoShowForm(base.ShowForm):
    """Formulário de visualização de uma situação.
    """
    
    grok.context(INavigationRoot)
    grok.name('show-situacao')
    grok.require('cmf.ManagePortal')

    schema = ISituacao
    klass = Situacao
    label = _(u'Detalhes da Situação')
    description = _(u'Formulário de visualização de uma situação.')
