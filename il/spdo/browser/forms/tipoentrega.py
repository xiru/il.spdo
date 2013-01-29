# -*- coding: utf-8 -*-

from five import grok
from plone.app.layout.navigation.interfaces import INavigationRoot

from il.spdo.browser.forms import base
from il.spdo.config import MessageFactory as _
from il.spdo.config import Session
from il.spdo.interfaces import ITipoEntrega
from il.spdo.db import TipoEntrega
from il.spdo.log import log

class TipoEntregaAddForm(base.AddForm):
    """Formulário de cadastro de um tipo de entrega.
    """

    grok.context(INavigationRoot)
    grok.name('add-tipoentrega')
    grok.require('cmf.ManagePortal')

    schema = ITipoEntrega
    klass = TipoEntrega
    label = _(u'Adicionar Tipo de Entrega')
    description = _(u'Formulário de cadastro de um tipo de entrega.')

    @log
    def createAndAdd(self, data):
        tipoentrega = TipoEntrega()
        tipoentrega.nome = data['nome']
        session = Session()
        session.add(tipoentrega)
        session.flush()

class TipoEntregaEditForm(base.EditForm):
    """Formulário de edição de um tipo de entrega.
    """

    grok.context(INavigationRoot)
    grok.name('edit-tipoentrega')
    grok.require('cmf.ManagePortal')

    schema = ITipoEntrega
    klass = TipoEntrega
    label = _(u'Editar Tipo de Entrega')
    descrition = _(u'Formulário de edição de um tipo de entrega.')

class TipoEntregaShowForm(base.ShowForm):
    """Formulário de visualização de um tipo de entrega.
    """
    
    grok.context(INavigationRoot)
    grok.name('show-tipoentrega')
    grok.require('cmf.ManagePortal')

    schema = ITipoEntrega
    klass = TipoEntrega
    label = _(u'Detalhes da Tipo de Entrega')
    description = _(u'Formulário de visualização de um tipo de entrega.')
