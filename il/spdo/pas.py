# -*- coding: utf-8 -*-
import sqlalchemy as rdb

from zope.component import getUtility
from zope.interface import implements
from zope.publisher.browser import BrowserView
from AccessControl import ClassSecurityInfo
from Products.PlonePAS.sheet import MutablePropertySheet
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.PluggableAuthService.plugins.BasePlugin import BasePlugin
from Products.PluggableAuthService.interfaces.plugins import (
        IAuthenticationPlugin,
        IPropertiesPlugin,
        IRolesPlugin,
        IUserEnumerationPlugin,
    )
from Products.PlonePAS.interfaces.plugins import IUserManagement
from Products.PlonePAS.interfaces.capabilities import IDeleteCapability
from Products.PlonePAS.interfaces.capabilities import IPasswordSetCapability

from il.spdo.config import Session
from il.spdo.db import Pessoa
from il.spdo.interfaces import ISPDOAPI
from il.spdo.seguranca import modifica_senha, verifica_senha

class AddForm(BrowserView):
    """Add form for SPDO PAS Plugin.
    """
    template = ViewPageTemplateFile('pas_templates/add_pas_form.pt')

    def __call__(self):
        """Render form template or process after submission.
        """
        if 'form.button.Add' in self.request.form:
            name = self.request.form.get('id', 'spdo_plugin')
            title = self.request.form.get('title', 'SPDO PAS Plugin')
            plugin = SPDOPASPlugin(name, title)
            self.context.context[name] = plugin
            url = self.context.absolute_url() + '/manage_workspace?manage_tabs_message=Plugin+added.'
            self.request.response.redirect(url)
        else:
            return self.template()

class SPDOPASPlugin(BasePlugin):
    """SPDO PAS plugin para integração com cadastro de pessoas.
    """
    
    implements(
            IAuthenticationPlugin,
            IPropertiesPlugin,
            IRolesPlugin,
            IUserEnumerationPlugin,
            IUserManagement,
            IDeleteCapability,
            IPasswordSetCapability,
        )

    security = ClassSecurityInfo()

    def __init__(self, id, title=None):
        self.__name__ = self.id = id
        self.title = title


    # IAuthenticationPlugin #

    security.declarePrivate('authenticateCredentials')
    def authenticateCredentials(self, credentials):
        """Validação do login de acordo com o email da pessoa e senha.
        """
        login = credentials.get('login', None)
        password = credentials.get('password', None)
        if not login or not password:
            return
        api = getUtility(ISPDOAPI)
        pessoa = api.getPessoaByEmail(login)
        if pessoa is not None and pessoa.email == login and verifica_senha(pessoa.email, password):
            return (pessoa.email, pessoa.email)


    # IRolesPlugin #

    security.declarePrivate('getRolesForPrincipal')
    def getRolesForPrincipal(self, principal, request=None):
        """Retorna as Roles de cada pessoa.
        """
	roles = []
        api = getUtility(ISPDOAPI)
        pessoa = api.getPessoaByEmail(principal.getId())
        if pessoa is not None:
            roles.append('Usuario SPDO')
            if pessoa.area_id is not None:
	   	roles.append('Operador SPDO')
        return tuple(roles)


    # IPropertiesPlugin # 

    security.declarePrivate('getPropertiesForUser')
    def getPropertiesForUser(self, user, request=None):
        """Retorna as propriedades de uma pessoa.
        """
        api = getUtility(ISPDOAPI) 
        pessoa = api.getPessoaByEmail(user.getId())
        if pessoa is None:
            return {}
        keys = Pessoa.__mapper__.columns.keys()
        remove_keys = ['id', 'nome', 'senha', 'version', 'version_date']
        keys = [k for k in keys if k not in remove_keys]
        data = {'fullname': pessoa.nome,}
        for k in keys:
            value = getattr(pessoa, k)
            if isinstance(value, unicode):
                data[k] = value.encode('utf-8')
            elif value is not None:
                data[k] = value
        return MutablePropertySheet(self.id, **data)


    # IUserEnumerationPlugin #

    security.declarePrivate('enumerateUsers')
    def enumerateUsers(self, id=None, login=None, exact_match=False,
        sort_by=None, max_results=None, **kw):
        """Retorna uma lista de usuários ou um usuário exatamente.
        """
        api = getUtility(ISPDOAPI)

        if exact_match:
            id_login = id is not None and id or login
            pessoa = api.getPessoaByEmail(id_login)
            if pessoa is not None:
                return ({'id': pessoa.email,
                         'login': pessoa.email,
                         'pluginid': self.getId(),
                        },)
            return ()

        session = Session()
        query = session.query(Pessoa)

        clause = None
        if 'fullname' in kw:
            clause = rdb.or_(Pessoa.nome.contains(kw['fullname']),
                             Pessoa.nome.ilike(kw['fullname']))
        elif 'email' in kw:
            clause = rdb.or_(Pessoa.email.contains(kw['email']),
                             Pessoa.email.ilike(kw['email']))
        if clause is not None:
            query = query.filter(clause)

        users = query.all()

        result = []
        for user in users:
            result.append({'id': user.email,
                           'login': user.email,
                           'pluginid': self.getId(),
                           })
        return tuple(result)


    # IDeleteCapability, IPasswordSetCapability #

    security.declarePublic('allowDeletePrincipal')
    def allowDeletePrincipal(self, principal_id):
        """Verdadeiro se a pessoa existir"""
        api = getUtility(ISPDOAPI)
        return api.getPessoaByEmail(principal_id) is not None

    security.declarePublic('allowPasswordSet')
    def allowPasswordSet(self, principal_id):
        """Verdadeiro se a pessoa existir"""
        api = getUtility(ISPDOAPI)
        return api.getPessoaByEmail(principal_id) is not None


    # IUserManagement plugin #

    security.declarePrivate('doDeleteUser')
    def doDeleteUser(self, userid):
        """Apaga o usuário removendo a pessoa do banco de dados. Se
        alguma integridade referencial não for respeitada será lançada
        uma exceção."""
        api = getUtility(ISPDOAPI)
        pessoa = api.getPessoaByEmail(userid)
        session = Session()
        session.delete(pessoa)

    security.declarePrivate('doChangeUser')
    def doChangeUser(self, principal_id, password):
        """Alteração de senha"""
        modifica_senha(principal_id, password)
