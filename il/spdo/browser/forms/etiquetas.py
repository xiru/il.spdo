# -*- coding: utf-8 -*-

import datetime

from five import grok
from zope.component import getUtility
from z3c.form import button
from plone.directives import form
from plone.app.layout.navigation.interfaces import INavigationRoot
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, letter

from il.spdo.etiquetas import FORMATOS_SUPORTADOS, geraPagina
from il.spdo.db import calculaDigitoVerificador
from il.spdo.config import Session
from il.spdo.config import MessageFactory as _
from il.spdo.interfaces import IEtiquetas
from il.spdo.log import log
from il.spdo.nav import go	
from il.spdo.interfaces import ISecurityChecker

class EtiquetasPrintForm(form.SchemaForm):
    """Formulário de impressão de etiquetas com códigos de barras.
    """

    grok.context(INavigationRoot)
    grok.name('print-etiquetas')
    grok.require('zope2.View')

    ignoreContext = True

    schema = IEtiquetas
    label = _(u'Imprimir Etiquetas')
    description = _(u'Formulário de impressão de etiquetas com códigos de barras.')

    def update(self):
        sc = getUtility(ISecurityChecker)
        sc.enforce('acessar_print_etiquetas')
        super(EtiquetasPrintForm, self).update()

    @log
    def imprimeEtiquetas(self, data):
        tipo = data['formato']
        formato = FORMATOS_SUPORTADOS[tipo]

        # protocolos não utilizados
        paginas = self.request.paginas
        if paginas:

            # TODO: refatorar, semelhante ao db.Protocolo.__init__
            ano = datetime.datetime.now().year
            session = Session()
            max_seq = session.bind.execute('SELECT max(p.seq) from protocolo p where p.ano = %d' % ano).fetchone()[0]
            seq = max_seq is None and 1 or max_seq + 1            

            p = []
            for pagina in range(paginas):
                l = []
                for linha in range(formato['Linhas']):
                    c = []
                    for coluna in range(formato['Colunas']):
                        dv = calculaDigitoVerificador(seq, ano)
                        numero = "%08d/%04d-%02d" % (seq, ano, dv)
                        seq += 1
                        c.append(numero)
                    l.append(c)
                p.append(l)
                
        # protocolos e quantidades
        nq = []
        for i in range(10):
            numero = self.request.get('numero%d' % i, '')
            quantidade = self.request.get('quantidade%d' % i, 0)
            if numero and quantidade:
                for j in range(quantidade):
                    nq.append(numero)                    
        while nq:
            l = []
            for linha in range(formato['Linhas']):
                c = []
                for coluna in range(formato['Colunas']):
                    numero = nq.pop(0)
                    c.append(numero)
                    if not nq: break
                l.append(c)
                if not nq: break
            p.append(l)

        pagesize = formato['Papel'] == 'A4' and A4 or letter
        c = canvas.Canvas('/tmp/%s.pdf' % self.request.SESSION.id, pagesize=pagesize)
        for numeros in p:
            geraPagina(formato, numeros, c, pagesize)
            c.showPage()
        c.save()

        go('download-etiquetas')

    @button.buttonAndHandler(_(u'Imprimir'), name='imprimir')
    def handleImprimir(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return
        self.imprimeEtiquetas(data)

    def updateActions(self):
        self.request.set('disable_border', True)
        super(EtiquetasPrintForm, self).updateActions()
        self.actions["imprimir"].addClass("context")
