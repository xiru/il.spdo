# -*- coding: utf-8 -*-

from five import grok
from plone.app.layout.navigation.interfaces import INavigationRoot

from il.spdo.browser.forms import base
from il.spdo.config import MessageFactory as _
from il.spdo.config import Session
from il.spdo.interfaces import IFluxo
from il.spdo.db import Fluxo
from il.spdo.log import log

class FluxoAddForm(base.AddForm):
    """Formulário de cadastro de um fluxo de tramitação.
    """

    grok.context(INavigationRoot)
    grok.name('add-fluxo')
    grok.require('cmf.ManagePortal')

    schema = IFluxo
    klass = Fluxo
    label = _(u'Adicionar Fluxo')
    description = _(u'Formulário de cadastro de um fluxo de tramitação.')

    @log
    def createAndAdd(self, data):
        fluxo = Fluxo()
        fluxo.nome = data['nome']
        fluxo.tipoprotocolo = data['tipoprotocolo']
        fluxo.tipodocumento_id = data['tipodocumento_id']
        fluxo.flexivel = data['flexivel']
        session = Session()
        session.add(fluxo)
        session.flush()

class FluxoEditForm(base.EditForm):
    """Formulário de edição de um fluxo de tramitação.
    """

    grok.context(INavigationRoot)
    grok.name('edit-fluxo')
    grok.require('cmf.ManagePortal')

    schema = IFluxo
    klass = Fluxo
    label = _(u'Editar Fluxo')
    descrition = _(u'Formulário de edição de um fluxo de tramitação.')

class FluxoShowForm(base.ShowForm):
    """Formulário de visualização de um fluxo de tramitação.
    """
    
    grok.context(INavigationRoot)
    grok.name('show-fluxo')
    grok.require('cmf.ManagePortal')

    schema = IFluxo
    klass = Fluxo
    label = _(u'Detalhes do Fluxo')
    description = _(u'Formulário de visualização de um fluxo de tramitação.')
