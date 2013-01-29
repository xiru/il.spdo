# -*- coding: utf-8 -*-

from five import grok
from zope.component import getUtility
from plone.app.layout.navigation.interfaces import INavigationRoot

from il.spdo.browser.forms import base
from il.spdo.config import MessageFactory as _
from il.spdo.config import Session
from il.spdo.interfaces import IPessoa
from il.spdo.db import Pessoa
from il.spdo.log import log
from il.spdo.interfaces import ISecurityChecker

class PessoaAddForm(base.AddForm):
    """Formulário de cadastro de uma pessoa.
    """

    grok.context(INavigationRoot)
    grok.name('add-pessoa')
    grok.require('zope2.View')

    schema = IPessoa
    klass = Pessoa
    label = _(u'Adicionar Pessoa')
    description = _(u'Formulário de cadastro de uma pessoa.')

    def update(self):
        sc = getUtility(ISecurityChecker)
        sc.enforce('acessar_add_pessoa')
        super(PessoaAddForm, self).update()

    @log
    def createAndAdd(self, data):
        del data['id']

        # garante que alguns campos são armazenados apenas como
        # números, mesmo sendo strings
        for campo in ('cep', 'cpf_cnpj'):
            if data[campo] is not None:
                data[campo] = ''.join([c for c in data[campo] if c.isdigit()])

        # ROLE_ADMIN ou ROLE_GESTOR são necessários para definir a
        # lotação de uma pessoa. Isso é importante para evitar que um
        # operador modifique a própria lotação para contornar
        # restrições de segurança.
        sc = getUtility(ISecurityChecker)
        if not sc.check('lotacao_pessoa'):
            del data['area_id']

        pessoa = Pessoa(**data)
        session = Session()
        session.add(pessoa)
        session.flush()

class PessoaEditForm(base.EditForm):
    """Formulário de edição de uma pessoa.
    """

    grok.context(INavigationRoot)
    grok.name('edit-pessoa')
    grok.require('zope2.View')

    schema = IPessoa
    klass = Pessoa
    label = _(u'Editar Pessoa')
    descrition = _(u'Formulário de edição de uma pessoa.')

    def update(self):
        sc = getUtility(ISecurityChecker)
        sc.enforce('acessar_edit_pessoa')
        super(PessoaEditForm, self).update()

    @log
    def applyChanges(self, data):
        content = self.getContent()
        if content:
            for k, v in data.items():

                # garante que alguns campos são armazenados apenas
                # como números, mesmo sendo strings
                if k in ('cep', 'cpf_cnpj') and v is not None:
                    v = ''.join([c for c in v if c.isdigit()])

                # ROLE_ADMIN ou ROLE_GESTOR são necessários para
                # definir a lotação de uma pessoa. Isso é importante
                # para evitar que um operador modifique a própria
                # lotação para contornar restrições de segurança.
                if k == 'area_id':
                    sc = getUtility(ISecurityChecker)
                    if not sc.check('lotacao_pessoa'):
                        continue
                
                setattr(content, k, v)

class PessoaShowForm(base.ShowForm):
    """Formulário de visualização de uma pessoa.
    """
    
    grok.context(INavigationRoot)
    grok.name('show-pessoa')
    grok.require('zope2.View')

    schema = IPessoa
    klass = Pessoa
    label = _(u'Detalhes da Pessoa')
    description = _(u'Formulário de visualização de uma pessoa.')

    def update(self):
        sc = getUtility(ISecurityChecker)
        sc.enforce('acessar_show_pessoa')
        super(PessoaShowForm, self).update()
