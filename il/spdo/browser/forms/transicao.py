# -*- coding: utf-8 -*-

from five import grok
from zope.component import getUtility
from plone.app.layout.navigation.interfaces import INavigationRoot

from il.spdo.browser.forms import base
from il.spdo.config import MessageFactory as _
from il.spdo.config import Session
from il.spdo.interfaces import IAddTransicao
from il.spdo.db import Transicao
from il.spdo.log import log
from il.spdo.nav import go
from il.spdo.interfaces import ISPDOAPI

class TransicaoAddForm(base.AddForm):
    """Formulário de cadastro de transições.
    """

    grok.context(INavigationRoot)
    grok.name('add-transicao')
    grok.require('cmf.ManagePortal')

    schema = IAddTransicao
    klass = Transicao
    label = _(u'Adicionar Transições')
    description = _(u'Formulário de cadastro de transições.')

    @log
    def createAndAdd(self, data):
        api = getUtility(ISPDOAPI)
        fluxo_id = api.getFluxoId()
        session = Session()
        for i in data['area_origem_id']:
            for j in data['area_destino_id']:
                # garante que a transição não tenha origem e destino iguais
                if i == j:
                    continue
                transicao = Transicao()
                transicao.fluxo_id = fluxo_id
                transicao.inicial = data['inicial']
                transicao.area_origem_id = i
                transicao.area_destino_id = j
                session.add(transicao)
        session.flush()

    def nextURL(self):
        api = getUtility(ISPDOAPI)
        fluxo_id = api.getFluxoId()
        go('list-transicao', fluxo_id=fluxo_id)
