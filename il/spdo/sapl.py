# -*- coding: utf-8 -*-

from zope.interface import Interface
from zope import schema
from five import grok
from Products.CMFCore.interfaces import ISiteRoot

from plone.z3cform import layout
from plone.directives import form
from plone.app.registry.browser.controlpanel import RegistryEditForm
from plone.app.registry.browser.controlpanel import ControlPanelFormWrapper


class ISAPLSettings(form.Schema):
    """ Define a estrutura dos dados """

    use_sapl = schema.Bool(
        title=u"Integrar com o SAPL?",
        description=u"Selecione caso queira fazer a integração com o SAPL",
    )
    end_sapl = schema.TextLine(
        title=u"Endereço do SAPL",
        description=u"Informe o endereço completo do SAPL, incluindo porta caso seja necessário",
    )
    user_sapl_login = schema.TextLine(
        title=u"Usuário do SAPL",
        description=u"Informe o usuário do SAPL que irá responder às requisições do SPDO."
                    u"Lembrando que ele terá que ter o papel de Operador Matéria.",
    )
    user_sapl_senha = schema.TextLine(
        title=u"Senha do usuário do SAPL",
        description=u"Informe a senha para conexão com o usuário do SAPL",
    )


class SAPLSettingsEditForm(RegistryEditForm):
    """ Define a logica do formulario
    """
    schema = ISAPLSettings
    label = u"Configurações para integração com o SAPL"


class SAPLSettingsView(grok.CodeView):
    """ View para configuração da integração com o SAPL
    """
    grok.name("sapl-settings")
    grok.context(ISiteRoot)

    def render(self):
        view_factor = layout.wrap_form(SAPLSettingsEditForm, ControlPanelFormWrapper)
        view = view_factor(self.context, self.request)
        return view()
