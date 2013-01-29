# -*- coding: utf-8 -*-

from five import grok
from z3c.form import button
from plone.directives import form
from zope.component import getUtility
from plone.app.layout.navigation.interfaces import INavigationRoot
from Products.statusmessages.interfaces import IStatusMessage

from il.spdo.browser.forms import base
from il.spdo.config import MessageFactory as _
from il.spdo.interfaces import IAddTramite, IBaseFormSchema, INumeroProtocolo
from il.spdo.db import Tramite, Protocolo
from il.spdo.log import log
from il.spdo.nav import go, url
from il.spdo.interfaces import ISPDOAPI, ISecurityChecker
from il.spdo.config import Session

class TramiteAddForm(base.AddForm):
    """Formulário de tramitação de protocolo.
    """

    grok.context(INavigationRoot)
    grok.name('add-tramite')
    grok.require('zope2.View')

    schema = IAddTramite
    label = _(u'Tramitação de Protocolo')
    description = _(u'Formulário de tramitação de um protocolo.')

    def update(self):
        sc = getUtility(ISecurityChecker)
        sc.enforce('acessar_add_tramite')
        super(TramiteAddForm, self).update()

    @log
    def createAndAdd(self, data):
        api = getUtility(ISPDOAPI)
        protocolo_id = api.getProtocoloId()
        api.addAnexos(protocolo_id, data['anexos'])
        api.TramiteEnvio([protocolo_id], data['areas'], data['despacho'])

    def nextURL(self):
        api = getUtility(ISPDOAPI)
        protocolo_id = api.getProtocoloId()
        go('show-protocolo', id=protocolo_id)

class TramiteEnvioForm(base.AddForm):
    """Formulário de tramitação de envio de protocolos.
    """

    grok.context(INavigationRoot)
    grok.name('envio-tramite')
    grok.require('zope2.View')

    schema = IAddTramite
    label = _(u'Tramitação de Protocolos - Envio')
    description = _(u'Formulário de tramitação de envio de protocolos.')

    dados = []

    @log
    def update(self):
        self.request.set('disable_border', True)
        sc = getUtility(ISecurityChecker)
        sc.enforce('acessar_envio_tramite')
        api = getUtility(ISPDOAPI)
        self.dados = api.getProtocolosCriadosRecebidos()
        super(TramiteEnvioForm, self).update()
    
    @log
    def createAndAdd(self, data):
        api = getUtility(ISPDOAPI)
        protocolos = self.request.protocolos
        for protocolo_id in protocolos:
            api.addAnexos(protocolo_id, data['anexos'])
        api.TramiteEnvio(protocolos, data['areas'], data['despacho'])

    def nextURL(self):
        go('envio-tramite')

    def cancelURL(self):
        go('list-protocolo')

class TramiteRecebimentoForm(base.AddForm):
    """Formulário de tramitação de recebimento de protocolos.
    """

    grok.context(INavigationRoot)
    grok.name('recebimento-tramite')
    grok.require('zope2.View')

    schema = IBaseFormSchema
    label = _(u'Tramitação de Protocolos - Recebimento')
    description = _(u'Formulário de tramitação de recebimento de protocolos.')

    dados = []

    @log
    def update(self):
        self.request.set('disable_border', True)
        sc = getUtility(ISecurityChecker)
        sc.enforce('acessar_recebimento_tramite')
        api = getUtility(ISPDOAPI)
        self.dados = api.getProtocolosNaoRecebidos()
        super(TramiteRecebimentoForm, self).update()
    
    @log
    def createAndAdd(self, data):
        api = getUtility(ISPDOAPI)
        protocolos = self.request.protocolos
        api.TramiteRecebimento(protocolos)

    def nextURL(self):
        go('recebimento-tramite')

    def cancelURL(self):
        go('list-protocolo')

class TramiteRecebimentoProtocoloForm(form.SchemaForm):
    """Formulário de tramitação de recebimento de um protocolo (código de barras).
    """

    grok.context(INavigationRoot)
    grok.name('recebimento-tramite-barra')
    grok.require('zope2.View')

    ignoreContext = True

    schema = INumeroProtocolo
    label = _(u'Tramitação de Protocolos - Recebimento (Código de Barras)')
    description = _(u'Utilize um scanner para efetuar a leitura do código de barras e receber o protocolo.')

    def update(self):
        sc = getUtility(ISecurityChecker)
        sc.enforce('acessar_recebimento_tramite_barra')
        super(TramiteRecebimentoProtocoloForm, self).update()

    def receberProtocolo(self, data):
        status = IStatusMessage(self.request)
        session = Session()
        protocolo = session.query(Protocolo).filter_by(numero=data['numero']).first()
        if protocolo is None:
            status.add(_(u'Verifique o número informado. Protocolo: ' + data['numero']), 'error')
        else:
            sc = getUtility(ISecurityChecker)
            if not sc.check('tramitar_recebimento', protocolo_id=protocolo.id):
                status.add(_(u'Protocolo não disponível para recebimento. Protocolo: ') + protocolo.numero, 'error')
            else:
                api = getUtility(ISPDOAPI)
                api.TramiteRecebimento([protocolo.id])
                status.add(_(u'Protocolo recebido com sucesso! Protocolo: ') + protocolo.numero, 'info')            
        go('recebimento-tramite-barra')
    
    @button.buttonAndHandler(_(u'Receber'), name='receber')
    def handleReceber(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return
        self.receberProtocolo(data)

    def updateActions(self):
        self.request.set('disable_border', True)
        super(TramiteRecebimentoProtocoloForm, self).updateActions()
        self.actions["receber"].addClass("context")

class TramiteRecuperacaoForm(base.AddForm):
    """Formulário de recuperação de protocolos enviados e não recebidos.
    """

    grok.context(INavigationRoot)
    grok.name('recuperacao-tramite')
    grok.require('zope2.View')

    schema = IBaseFormSchema
    label = _(u'Tramitação de Protocolos - Recuperação')
    description = _(u'Formulário de recuperação de protocolos enviados e não recebidos.')

    dados = []

    @log
    def update(self):
        self.request.set('disable_border', True)
        sc = getUtility(ISecurityChecker)
        sc.enforce('acessar_recuperacao_tramite')
        api = getUtility(ISPDOAPI)
        self.dados = api.getProtocolosEnviados()
        super(TramiteRecuperacaoForm, self).update()
    
    @log
    def createAndAdd(self, data):
        api = getUtility(ISPDOAPI)
        protocolos = self.request.protocolos
        api.TramiteRecuperacao(protocolos)

    def nextURL(self):
        go('recuperacao-tramite')

    def cancelURL(self):
        go('list-protocolo')
