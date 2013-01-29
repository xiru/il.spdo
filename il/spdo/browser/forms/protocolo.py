# -*- coding: utf-8 -*-

from sqlalchemy import or_
from five import grok
from z3c.form import button
from plone.directives import form
from zope.component import getUtility
from plone.app.layout.navigation.interfaces import INavigationRoot
from Products.statusmessages.interfaces import IStatusMessage

from il.spdo.browser.forms import base
from il.spdo.config import MessageFactory as _
from il.spdo.interfaces import IAddProtocolo, IEditProtocolo, IApenso, INumeroProtocolo, ISearchProtocolo
from il.spdo import db
from il.spdo.log import log
from il.spdo.nav import go
from il.spdo.interfaces import ISPDOAPI, ISecurityChecker
from il.spdo.config import Session

class ProtocoloAddForm(base.AddForm):
    """Formulário de cadastro de um protocolo.
    """

    grok.context(INavigationRoot)
    grok.name('add-protocolo')
    grok.require('zope2.View')

    schema = IAddProtocolo
    label = _(u'Adicionar protocolo')
    description = _(u'Formulário de cadastro de um protocolo.')

    def update(self):
        sc = getUtility(ISecurityChecker)
        sc.enforce('acessar_add_protocolo', ajax=True)
        super(ProtocoloAddForm, self).update()
 
    @log
    def createAndAdd(self, data):
        api = getUtility(ISPDOAPI)
        protocolo_id = api.addProtocolo(**data)

        # IMPORTANTE: Por definição, exceto na criação dos protocolos,
        # os anexos e as observações são sempre adicionadas ANTES da
        # tramitação ocorrer.

        api.TramiteInicial(protocolo_id)
        api.addObservacao(protocolo_id, data['observacao'])
        api.addAnexos(protocolo_id, data['anexos'])
        self.protocolo_id = protocolo_id

    def nextURL(self):
        go('show-protocolo', id=self.protocolo_id)

    def cancelURL(self):
        go('list-protocolo')

        
class ApensoAddForm(base.AddForm):
    """Formulário de cadastro de apenso.
    """

    grok.context(INavigationRoot)
    grok.name('add-apenso')
    grok.require('zope2.View')

    schema = IApenso
    klass = db.Protocolo
    label = _(u'Adicionar apenso')
    descrition = _(u'Formulário de cadastro de apenso.')

    def update(self):
        sc = getUtility(ISecurityChecker)
        sc.enforce('acessar_add_apenso', ajax=True)
        super(ApensoAddForm, self).update()

    @log
    def createAndAdd(self, data):
        api = getUtility(ISPDOAPI)
        protocolo = api.getProtocolo()
        # garante que o protocolo não seja apensado em si mesmo
        if protocolo.id == data['apenso_id']:
            return
        protocolo.apenso_id = data['apenso_id']

    def nextURL(self):
        api = getUtility(ISPDOAPI)
        protocolo_id = api.getProtocoloId()
        go('show-protocolo', id=protocolo_id)


class ProtocoloEditForm(base.EditForm):
    """Formulário de edição de um protocolo.
    """

    grok.context(INavigationRoot)
    grok.name('edit-protocolo')
    grok.require('zope2.View')

    schema = IEditProtocolo
    klass = db.Protocolo
    label = _(u'Editar protocolo')
    descrition = _(u'Formulário de edição de um protocolo.')

    def update(self):
        sc = getUtility(ISecurityChecker)
        sc.enforce('acessar_edit_protocolo')
        super(ProtocoloEditForm, self).update()

    def _applyChangesApensos(self, content, data):
        api = getUtility(ISPDOAPI)
        usuario = api.getAuthId()
        for apenso in content.apenso:
            for k, v in data.items():
                if k in ('tipoprotocolo', 'tipodocumento_id', 'situacao_id'):
                    setattr(apenso, k, v)
            apenso.numero = "%s-%08d/%04d-%02d" % (apenso.tipoprotocolo, apenso.seq, apenso.ano, apenso.dv)
            apenso.usuario = usuario
            self._applyChangesApensos(apenso, data)

    @log
    def applyChanges(self, data):
        content = self.getContent()
        if not content:
            return
        for k, v in data.items():
            setattr(content, k, v)
        content.numero = "%s-%08d/%04d-%02d" % (content.tipoprotocolo, content.seq, content.ano, content.dv)
        api = getUtility(ISPDOAPI)
        content.usuario = api.getAuthId()
        # propaga atualização nos apensos
        self._applyChangesApensos(content, data)

class ProtocoloNumeroForm(form.SchemaForm):
    """Formulário de consulta de um protocolo (código de barras).
    """

    grok.context(INavigationRoot)
    grok.name('search-protocolo-barra')
    grok.require('zope2.View')

    ignoreContext = True

    schema = INumeroProtocolo
    label = _(u'Consulta um Protocolo (Código de Barras)')
    description = _(u'Utilize um scanner para efetuar a leitura do código de barras e consultar o protocolo.')

    def update(self):
        sc = getUtility(ISecurityChecker)
        sc.enforce('acessar_search_protocolo_barra')
        super(ProtocoloNumeroForm, self).update()

    def consultarProtocolo(self, data):
        status = IStatusMessage(self.request)
        session = Session()
        query = session.query(db.Protocolo)
        clause = or_(db.Protocolo.numero.contains(data['numero']),
                     db.Protocolo.numero.ilike(data['numero']))
        protocolo = query.filter(clause).first()
        if protocolo is None:
            status.add(_(u'Verifique o número informado. Protocolo: ' + data['numero']), 'error')
            go('search-protocolo-barra')
        else:
            go('show-protocolo', id=protocolo.id)
    
    @button.buttonAndHandler(_(u'Consultar'), name='consultar')
    def handleConsultar(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return
        self.consultarProtocolo(data)

    def updateActions(self):
        self.request.set('disable_border', True)
        super(ProtocoloNumeroForm, self).updateActions()
        self.actions["consultar"].addClass("context")

class ProtocoloSearchForm(form.SchemaForm):
    """Formulário de pesquisa de protocolos.
    """

    grok.context(INavigationRoot)
    grok.name('search-protocolo')
    grok.require('zope2.View')

    ignoreContext = True

    schema = ISearchProtocolo
    label = _(u'Pesquisa Protocolos')
    description = _(u'Utilize o formulário a seguir para pesquisar por tipo de protocolo, ' +
                    u'tipo de documento, assunto, situação, origem, destino, área ou ainda ' +
                    u'pelo tempo que o protocolo está sem tramitar.')

    dados = []

    @log
    def update(self):
        self.request.set('disable_border', True)
        sc = getUtility(ISecurityChecker)
        sc.enforce('acessar_search_protocolo')
        api = getUtility(ISPDOAPI)
        self.dados = api.pesquisaProtocolos()
        super(ProtocoloSearchForm, self).update()

    def consultarProtocolos(self, data):
        r = self.request.response
        for campo in ['tipoprotocolo', 'tipodocumento_id', 'assunto', 'situacao_id',
                      'origem', 'destino', 'area_id', 'tempo_inativo']:
            cookie_name = 'search-protocolo-' + campo
            if data[campo] is None:
                r.expireCookie(cookie_name)
            else:
                v = data[campo]
                # API de cookies do Zope não suporta unicode
                if type(v) == type(u''):
                    v = v.encode('utf-8')
                r.setCookie(cookie_name, v)
        go('search-protocolo')
    
    @button.buttonAndHandler(_(u'Consultar'), name='consultar')
    def handleConsultar(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return
        self.consultarProtocolos(data)

    def updateActions(self):
        self.request.set('disable_border', True)
        super(ProtocoloSearchForm, self).updateActions()
        self.actions["consultar"].addClass("context")
