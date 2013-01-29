# -*- coding: utf-8 -*-

from five import grok
from plone.app.layout.navigation.interfaces import INavigationRoot

from il.spdo.browser.forms import base
from il.spdo.config import MessageFactory as _
from il.spdo.config import Session
from il.spdo.interfaces import IResponsavel
from il.spdo.db import Responsavel
from il.spdo.log import log

class ResponsavelAddForm(base.AddForm):
    """Formulário de cadastro de um responsável.
    """

    grok.context(INavigationRoot)
    grok.name('add-responsavel')
    grok.require('cmf.ManagePortal')

    schema = IResponsavel
    klass = Responsavel
    label = _(u'Adicionar Responsável')
    description = _(u'Formulário de cadastro de um responsável.')

    @log
    def createAndAdd(self, data):
        responsavel = Responsavel()
        responsavel.area_id = data['area_id']
        responsavel.pessoa_id = data['pessoa_id']
        responsavel.data_responsavel = data['data_responsavel']
        session = Session()
        session.add(responsavel)
        session.flush()

class ResponsavelEditForm(base.EditForm):
    """Formulário de edição de um responsável.
    """

    grok.context(INavigationRoot)
    grok.name('edit-responsavel')
    grok.require('cmf.ManagePortal')

    schema = IResponsavel
    klass = Responsavel
    label = _(u'Editar Responsável')
    descrition = _(u'Formulário de edição de um responsável.')

class ResponsavelShowForm(base.ShowForm):
    """Formulário de visualização de um responsável.
    """
    
    grok.context(INavigationRoot)
    grok.name('show-responsavel')
    grok.require('cmf.ManagePortal')

    schema = IResponsavel
    klass = Responsavel
    label = _(u'Detalhes da Responsável')
    description = _(u'Formulário de visualização de um responsável.')
