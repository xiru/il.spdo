# -*- coding: utf-8 -*-

from sqlalchemy.exc import IntegrityError

from five import grok
from z3c.form import button
from plone.directives import form
from plone.app.layout.navigation.interfaces import INavigationRoot
from Products.statusmessages.interfaces import IStatusMessage

from il.spdo.config import MessageFactory as _
from il.spdo.config import Session
from il.spdo.log import log, logger
from il.spdo.nav import go

def vs(klass):
    return klass.__name__.lower()

class AddForm(form.SchemaForm):
    """Formulário base de cadastro.
    """

    grok.context(INavigationRoot)

    ignoreContext = True

    def createAndAdd(self, data):
        raise NotImplementedError

    def nextURL(self):
        go('list-'+vs(self.klass))

    def cancelURL(self):
        self.nextURL()

    @button.buttonAndHandler(_(u'Cadastrar'), name='cadastrar')
    def handleCadastrar(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return
        status = IStatusMessage(self.request)
        try:
            obj = self.createAndAdd(data)
            session = Session()
            session.flush()
        except IntegrityError, e:
            msg = _(u'Falha de integridade relacional: ' + str(e))
            status.add(msg, 'error')
            logger(msg)
            raise
        else:
            status.add(_(u'Cadastro efetuado com sucesso.'), 'info')
            self.nextURL()

    @button.buttonAndHandler(_(u'Cancelar'), name='cancelar')
    def handleCancelar(self, action):
        self.cancelURL()

    def updateActions(self):
        self.request.set('disable_border', True)
        super(AddForm, self).updateActions()
        self.actions["cadastrar"].addClass("context")
        self.actions["cancelar"].addClass("standalone")


class EditForm(form.SchemaForm):
    """Formulário base de edição dos formmulários.
    """

    grok.context(INavigationRoot)

    def getContent(self):
        session = Session()
        return session.query(self.klass).get(self.rec_id())

    @log
    def applyChanges(self, data):
        content = self.getContent()
        if content:
            for k, v in data.items():
                setattr(content, k, v)

    def nextURL(self):
        go('show-'+vs(self.klass), id=self.rec_id())

    def rec_id(self):
        return self.request.get('id', self.request.get('form.widgets.id', None))

    @button.buttonAndHandler(_(u'Salvar'), name='salvar')
    def handleSalvar(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return
        status = IStatusMessage(self.request)
        try:
            self.applyChanges(data)
            session = Session()
            session.flush()
        except IntegrityError, e:
            msg = _(u'Falha de integridade relacional: ' + str(e))
            status.add(msg, 'error')
            logger(msg)
            raise
        else:
            status.add(_(u"Alterações efetuadas"), "info")
            self.nextURL()

    @button.buttonAndHandler(_(u'Cancelar'), name='cancelar')
    def handleCancelar(self, action):
        self.nextURL()

    def updateActions(self):
        self.request.set('disable_border', True)
        super(EditForm, self).updateActions()
        self.actions["salvar"].addClass("context")
        self.actions["cancelar"].addClass("standalone")


class ShowForm(form.SchemaForm):
    """Formulário base de visualização.
    """

    grok.context(INavigationRoot)

    mode = 'display'

    @log
    def removeItem(self):
        content = self.getContent()
        status = IStatusMessage(self.request)
        try:
            session = Session()
            session.delete(content)
            session.flush()
        except AssertionError, e:
            msg = _(u'Falha de integridade relacional: ' + str(e))
            status.add(msg, 'error')
            logger(msg)
            raise
        else:
            status.add(_(u'Registro removido.'), 'info')
            self.nextURL()

    def getContent(self):
        session = Session()
        return session.query(self.klass).get(self.rec_id())

    def nextURL(self):
        go('list-'+vs(self.klass))

    def editURL(self):
        go('edit-'+vs(self.klass), id=self.rec_id())

    def rec_id(self):
        return self.request.get('id', self.request.get('form.widgets.id', None))

    @button.buttonAndHandler(_(u'Editar'), name='editar')
    def handleEditar(self, action):
        self.editURL()

    @button.buttonAndHandler(_(u'Excluir'), name='excluir')
    def handleExcluir(self, action):
        self.removeItem()

    @button.buttonAndHandler(_(u'Voltar'), name='voltar')
    def handleVoltar(self, action):
        self.nextURL()

    def updateActions(self):
        self.request.set('disable_border', True)
        super(ShowForm, self).updateActions()
        self.actions["editar"].addClass("context")
        self.actions["excluir"].addClass("context")
        self.actions["voltar"].addClass("standalone")
