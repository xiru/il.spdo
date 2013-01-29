# -*- coding: utf-8 -*-

from five import grok
from plone.app.layout.navigation.interfaces import INavigationRoot

from il.spdo.browser.forms import base
from il.spdo.config import MessageFactory as _
from il.spdo.config import Session
from il.spdo.interfaces import IArea
from il.spdo.db import Area
from il.spdo.log import log

class AreaAddForm(base.AddForm):
    """Formulário de cadastro de uma área do organograma.
    """

    grok.context(INavigationRoot)
    grok.name('add-area')
    grok.require('cmf.ManagePortal')

    schema = IArea
    klass = Area
    label = _(u'Adicionar Área')
    description = _(u'Formulário de cadastro de uma área do organograma.')

    @log
    def createAndAdd(self, data):
        area = Area()
        area.sigla = data['sigla']
        area.nome = data['nome']
        area.chefia_id = data['chefia_id']
        session = Session()
        session.add(area)
        session.flush()
        return area


class AreaEditForm(base.EditForm):
    """Formulário de edição de uma área do organograma.
    """

    grok.context(INavigationRoot)
    grok.name('edit-area')
    grok.require('cmf.ManagePortal')

    schema = IArea
    klass = Area
    label = _(u'Editar Área')
    descrition = _(u'Formulário de edição de uma área do organograma.')


class AreaShowForm(base.ShowForm):
    """Formulário de visualização de uma área do organograma.
    """
    
    grok.context(INavigationRoot)
    grok.name('show-area')
    grok.require('cmf.ManagePortal')

    schema = IArea
    klass = Area
    label = _(u'Detalhes da Área')
    description = _(u'Formulário de visualização de uma área do organograma.')
