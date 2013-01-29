# -*- coding: utf-8 -*-

from five import grok
from plone.app.layout.navigation.interfaces import INavigationRoot

from il.spdo.browser.forms import base
from il.spdo.config import MessageFactory as _
from il.spdo.config import Session
from il.spdo.interfaces import ITipoDocumento
from il.spdo.db import TipoDocumento
from il.spdo.log import log

class TipoDocumentoAddForm(base.AddForm):
    """Formulário de cadastro de um tipo de documento.
    """

    grok.context(INavigationRoot)
    grok.name('add-tipodocumento')
    grok.require('cmf.ManagePortal')

    schema = ITipoDocumento
    klass = TipoDocumento
    label = _(u'Adicionar Tipo de Documento')
    description = _(u'Formulário de cadastro de um tipo de documento.')

    @log
    def createAndAdd(self, data):
        tipodocumento = TipoDocumento()
        tipodocumento.nome = data['nome']
        session = Session()
        session.add(tipodocumento)
        session.flush()

class TipoDocumentoEditForm(base.EditForm):
    """Formulário de edição de um tipo de documento.
    """

    grok.context(INavigationRoot)
    grok.name('edit-tipodocumento')
    grok.require('cmf.ManagePortal')

    schema = ITipoDocumento
    klass = TipoDocumento
    label = _(u'Editar Tipo de Documento')
    descrition = _(u'Formulário de edição de um tipo de documento.')

class TipoDocumentoShowForm(base.ShowForm):
    """Formulário de visualização de um tipo de documento.
    """
    
    grok.context(INavigationRoot)
    grok.name('show-tipodocumento')
    grok.require('cmf.ManagePortal')

    schema = ITipoDocumento
    klass = TipoDocumento
    label = _(u'Detalhes da Tipo de Documento')
    description = _(u'Formulário de visualização de um tipo de documento.')
