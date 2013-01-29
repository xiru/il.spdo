# -*- coding: utf-8 -*-

import datetime
import re

from zope import interface, schema
from zope.component import getUtility
from zope.globalrequest import getRequest
from plone.directives import form
from plone.formwidget.multifile import MultiFileFieldWidget
from plone.namedfile.field import NamedFile
from plone.formwidget.autocomplete import AutocompleteFieldWidget, AutocompleteMultiFieldWidget
from collective.z3cform.datetimewidget import DateFieldWidget

from il.spdo.config import MessageFactory as _
from il.spdo.config import ENABLE_FLASH_MULTIFILE, EMAIL_RE
from il.spdo.util import valida_cpf_cnpj

# Default Factories #

def getProtocoloId():
    api = getUtility(ISPDOAPI)
    return api.getProtocoloId()

def _getDefault(campo):
    r = getRequest()
    v = r.get(campo, r.get('search-protocolo-' + campo, None))
    # API de cookies do Zope não suporta unicode
    if type(v) == type(''):
        v = unicode(v, 'utf-8')
    return v

def getTipoProtocolo():
    return _getDefault('tipoprotocolo') 

def getTipoDocumento():
    v = _getDefault('tipodocumento_id')
    return v is not None and int(v) or v

def getAssunto():
    return _getDefault('assunto')

def getSituacao():
    v = _getDefault('situacao_id')
    return v is not None and int(v) or v

def getOrigem():
    return _getDefault('origem')

def getDestino():
    return _getDefault('destino')

def getArea():
    v = _getDefault('area_id')
    return v is not None and int(v) or v

def getTempoInativo():
    v = _getDefault('tempo_inativo')
    return v is not None and int(v) or v

# API #

class ISPDOAPI(interface.Interface):
    """Marker interface.
    """

# Segurança #

class ISecurityChecker(interface.Interface):
    """Global Utility para verificações de segurança.
    """

    def check(acao, **kwargs):
        """Executa todas as verificações de uma ação e retorna
        verdadeiro se o usuário autenticado tem permissão de executar
        a ação e falso caso contrário.
        """

    def enforce(acao, **kwargs):
        """Executa o método check desta interface e caso o retorno
        seja falso (o usuário não tem permissão de executar a ação),
        levanta uma exceção do tipo Unauthorized.
        """

# Formulários #

class IBaseFormSchema(form.Schema):
    pass

class IArea(IBaseFormSchema):

    form.mode(id='hidden')
    id = schema.Int(
        title=_(u'ID'),
        description=_(u'Identificador da Área.'),
        required=False)

    sigla = schema.TextLine(
        title=_(u'Sigla'),
        description=_(u'Informe a sigla da  Área.'),
        max_length=20)
    
    nome = schema.TextLine(
        title=_(u'Nome'),
        description=_(u'Informe o nome da Área.'),
        max_length=100)

    chefia_id = schema.Choice(
        title=_(u'Chefia'),
        description=_(u'Selecione a Área de Chefia.'),
        required=False,
        vocabulary='il.spdo.areas-vocab')

    # TODO: validar ciclos
    @interface.invariant
    def verifyAreaPai(area):
        if area.id and area.chefia_id and area.id == area.chefia_id:
            raise interface.Invalid(_(u'A área de chefia precisa ser diferente da própria área. Se a área não possuir chefia, não selecione nenhuma área.'))

class IUF(IBaseFormSchema):

    form.mode(id='hidden')
    id = schema.Int(
        title=_(u'ID'),
        description=_(u'Identificador da UF.'),
        required=False)

    sigla = schema.TextLine(
        title=_(u'Sigla'),
        description=_(u'Informe a sigla da UF.'))

    nome = schema.TextLine(
        title=_(u'Nome'),
        description=_(u'Informe o nome da UF.'))

class IPessoa(IBaseFormSchema): 
    
    """ Interface que descreve representações de Pessoa, classe que
    pode ser utilizada para representar pessoas físicas, organizações
    e ainda usuários do sistema """

    form.fieldset('endereco',
      label=u"Endereço",
      fields=['endereco', 'bairro', 'cep', 'cidade', 'uf_id'])

    form.fieldset('lotacao',
      label=u"Lotação",
      fields=['area_id'])

    form.mode(id='hidden')
    id = schema.Int(
        title=_(u'ID'),
        description=_(u'Identificador da Pessoa.'),
        required=False)

    nome = schema.TextLine(
        title=_(u'Nome'),
        description=_(u'Nome completo da Pessoa.'),
        max_length=100)

    email = schema.TextLine(
        title=_(u'Email'),
        description=_(u'Informe o email da Pessoa.'),
        max_length=254)

    endereco = schema.TextLine(
        title=_(u'Endereço'),
        description=_(u'Logradouro, número e complemento.'),
        max_length=100,
        required=False)

    bairro = schema.TextLine(
        title=_(u'Bairro'),
        description=_(u'Informe o bairro.'),
        max_length=50,
        required=False)

    cep = schema.TextLine(
        title=_(u'CEP'),
        description=_(u'Informe o CEP (apenas números)'),
        required=False)

    cidade = schema.TextLine(
        title=_(u'Cidade'),
        description=_(u'Informe a cidade.'),
        max_length=50,
        required=False)

    uf_id = schema.Choice(
        title=_(u'UF'),
        description=_(u'Selecione o estado da federação.'),
        required=False,
        vocabulary='il.spdo.uf-vocab')

    tipopessoa = schema.Choice(
        title=_(u'Tipo'),
        description=_(u'Informe se a pessoa é física ou uma organização.'),
        default=u'F',
        vocabulary='il.spdo.tipopessoa-vocab')

    cpf_cnpj = schema.TextLine(
        title=_(u'CPF/CNPJ'),
        description=_(u'Informe o CPF ou CNPJ de acordo com o tipo de pessoa: física ou organização.'),
        max_length=20,
        required=False)

    contato = schema.TextLine(
        title=_(u'Contato'),
        description=_(u'Pessoa ou organização de contato.'),
        max_length=100,
        required=False)

    telefone = schema.TextLine(
        title=_(u'Telefone'),
        description=_(u'Informe o telefone com DDD.'),
        max_length=30,
        required=False)

    area_id = schema.Choice(
        title=_(u'Área'),
        description=_(u'Selecione a área de lotação da pessoa no organograma.'),
        required=False,
        vocabulary='il.spdo.areas-vocab')

class IResponsavel(IBaseFormSchema):

    form.mode(id='hidden')
    id = schema.Int(
        title=_(u'ID'),
        description=_(u'Identificador do Responsável.'),
        required=False)

    area_id = schema.Choice(
        title=_(u'Área'),
        description=_(u'Área do Organograma'),
        vocabulary='il.spdo.areas-vocab')

    form.widget(pessoa_id=AutocompleteFieldWidget)
    pessoa_id = schema.Choice(
        title=_(u'Pessoa'),
        description=_(u'Selecione a pessoa responsável pela área.'),
        vocabulary='il.spdo.pessoa-vocab')

    form.widget(data_responsavel=DateFieldWidget)
    data_responsavel = schema.Date(
        title=_(u'Data como Responsável.'),
        description=_(u'Informe a data a partir da qual a pessoa tornou-se responsável pela área.'),
        defaultFactory=datetime.date.today)

class ITipoDocumento(IBaseFormSchema):

    form.mode(id='hidden')
    id = schema.Int(
        title=_(u'ID'),
        description=_(u'Identificador do Tipo de Documento.'),
        required=False)

    nome = schema.TextLine(
        title=_(u'Nome'),
        description=_(u'Informe o nome do tipo do documento.'))

class ISituacao(IBaseFormSchema):

    form.mode(id='hidden')
    id = schema.Int(
        title=_(u'ID'),
        description=_(u'Identificador da Situação.'),
        required=False)

    nome = schema.TextLine(
        title=_(u'Nome'),
        description=_(u'Informe o nome da situação.'))

    inicial = schema.Bool(
        title=_(u'Inicial'),
        description=_(u'Situação inicial?'),
        required=False)

    final = schema.Bool(
        title=_(u'Final'),
        description=_(u'Situação final?'),
        required=False)

class IBaseProtocolo(IBaseFormSchema):

    form.mode(id='hidden')
    id = schema.Int(
        title=_(u'ID'),
        description=_(u'Identificador do Protocolo.'),
        required=False)

    tipoprotocolo = schema.Choice(
        title=_(u'Tipo de Protocolo'),
        description=_(u'Selecione o tipo do protocolo.'),
        vocabulary='il.spdo.tipoprotocolo-vocab')

    tipodocumento_id = schema.Choice(
        title=_(u'Tipo de Documento'),
        description=_(u'Selecione o tipo do documento.'),
        vocabulary='il.spdo.tipodocumento-vocab')

    numero_documento = schema.TextLine(
        title=_(u'Número do Documento'),
        description=_(u'Informe o número do documento.'),
        max_length=20,
        required=False)

    form.widget(data_emissao=DateFieldWidget)
    data_emissao = schema.Date(
        title=_(u'Data Emissão Documento'),
        description=_(u'Informe a data de emissão do documento.'),
        defaultFactory=datetime.date.today,
        required=False)

    assunto = schema.TextLine(
        title=_(u'Assunto'),
        description=_(u'Informe o assunto do documento.'),
        max_length=100)

    situacao_id = schema.Choice(
        title=_(u'Situação'),
        description=_(u'Selecione a situação atual do protocolo.'),
        vocabulary='il.spdo.situacao-atual-vocab')

    @interface.invariant
    def verifyFluxo(protocolo):
        if not protocolo.tipoprotocolo:
            raise interface.Invalid(_(u'O parâmetro tipoprotocolo não foi informado.'))
        if not protocolo.tipodocumento_id:
            raise interface.Invalid(_(u'O parâmetro tipodocumento_id não foi informado.'))
        sc = getUtility(ISecurityChecker)
        if not sc.check('fluxo_rigoroso_area_inicial', tipoprotocolo=protocolo.tipoprotocolo, tipodocumento_id=protocolo.tipodocumento_id):
            raise interface.Invalid(_(u'Esse tipo de protocolo e/ou tipo de documento não pode ser protocolado pela sua área.'))

class IAddProtocolo(IBaseProtocolo):

    situacao_id = schema.Choice(
        title=_(u'Situação'),
        description=_(u'Selecione a situação inicial do protocolo.'),
        vocabulary='il.spdo.situacao-inicial-vocab')

    form.widget(origem=AutocompleteMultiFieldWidget)
    origem = schema.List(
        title=_(u'Origem'),
        description=_(u'Selecione uma ou mais pessoas de origem do protocolo.'),
        value_type=schema.Choice(vocabulary='il.spdo.pessoa-vocab'))

    form.widget(destino=AutocompleteMultiFieldWidget)
    destino = schema.List(
        title=_(u'Destino'),
        description=_(u'Selecione uma ou mais pessoas de destino do protocolo.'),
        value_type=schema.Choice(vocabulary='il.spdo.pessoa-vocab'))

    observacao = schema.Text(
        title=_(u'Observação'),
        description=_(u'Informe qualquer observação que seja necessária.'),
        required=False)

    if ENABLE_FLASH_MULTIFILE:
        form.widget(anexos=MultiFileFieldWidget)
    anexos = schema.List(
        title=_(u'Anexos'),
        description=_(u'Adicione anexos ao protocolo (opcional).'),
        required=False,
        value_type=NamedFile())

class IEditProtocolo(IBaseProtocolo):

    pass

class IApenso(IBaseFormSchema):

    form.mode(protocolo_id='hidden')
    protocolo_id = schema.Int(
        title=_(u'ID do Protocolo'),
        description=_(u'Identificador do Protocolo.'),
        defaultFactory=getProtocoloId,
        required=False)

    form.widget(apenso_id=AutocompleteFieldWidget)
    apenso_id = schema.Choice(
        title=_(u'Apenso'),
        description=_(u'Número de Protocolo de Apenso'),
        vocabulary='il.spdo.protocolo-vocab',
        required=False)

    @interface.invariant
    def verifyApenso(apenso):
        if not apenso.apenso_id:
            return
        if not apenso.protocolo_id:
            raise interface.Invalid(_(u'O parâmetro protocolo_id não foi informado.'))
        if apenso.protocolo_id == apenso.apenso_id:
            raise interface.Invalid(_(u'O protocolo não pode ser apensado a ele mesmo.'))
        sc = getUtility(ISecurityChecker)
        if not sc.check('ciclo_apenso', protocolo_id=apenso.protocolo_id, apenso_id=apenso.apenso_id):
            raise interface.Invalid(_(u'Ciclo de apensos detectado!'))
        if not sc.check('momento_tramitacao', protocolo_id=apenso.protocolo_id, apenso_id=apenso.apenso_id):
            raise interface.Invalid(_(u'Para que um protocolo seja apensado em outro é necessário que ambos compartilhem o mesmo momento na tramitação, ou seja, estejam tramitando nas mesmas áreas e tenham o mesmo tipo de documento e protocolo.'))

class IAddReferencia(IBaseFormSchema):

    form.mode(protocolo_id='hidden')
    protocolo_id = schema.Int(
        title=_(u'ID do Protocolo'),
        description=_(u'Identificador do Protocolo.'),
        defaultFactory=getProtocoloId,
        required=False)

    form.widget(referencia_id=AutocompleteMultiFieldWidget)
    referencia_id = schema.List(
        title=_(u'Referências'),
        description=_(u'Números de Protocolo Referenciados'),
        value_type=schema.Choice(vocabulary='il.spdo.protocolo-vocab'))

class IAddNotificacao(IBaseFormSchema):

    form.widget(protocolo_id=AutocompleteMultiFieldWidget)
    protocolo_id = schema.List(
        title=_(u'Protocolos'),
        description=_(u'Protocolos que serão acompanhados, enviando notificações por email ao serem atualizados.'),
        value_type=schema.Choice(vocabulary='il.spdo.protocolo-vocab'))
        
class IAddTramite(IBaseFormSchema):

    form.mode(protocolo_id='hidden')
    protocolo_id = schema.Int(
        title=_(u'ID do Protocolo'),
        description=_(u'Identificador do Protocolo.'),
        defaultFactory=getProtocoloId,        
        required=False)

    areas = schema.List(
        title=_(u'Área'),
        description=_(u'Área para qual o protocolo deve tramitar. Selecione mais de uma área para realizar tramitação por cópia.'),
        value_type=schema.Choice(vocabulary='il.spdo.areas-vocab'))

    despacho = schema.Text(
        title=_(u'Despacho'),
        description=_(u'Despacho que descreve as ações que devem ser tormadas para a tramitação prosseguir.'),
        required=False)

    if ENABLE_FLASH_MULTIFILE:
        form.widget(anexos=MultiFileFieldWidget)
    anexos = schema.List(
        title=_(u'Anexos'),
        description=_(u'Adicione anexos ao protocolo (opcional).'),
        required=False,
        value_type=NamedFile())

    @interface.invariant
    def verifyFluxo(tramite):
        if not tramite.protocolo_id:
            raise interface.Invalid(_(u'O parâmetro protocolo_id não foi informado.'))
        if not tramite.areas:
            raise interface.Invalid(_(u'O parâmetro areas não foi informado.'))
        sc = getUtility(ISecurityChecker)
        if not sc.check('fluxo_rigoroso', protocolo_id=tramite.protocolo_id, areas=tramite.areas):
            raise interface.Invalid(_(u'Não é possível tramitar esse protocolo para as áreas escolhidas. O fluxo de tramitação definido para o tipo de protocolo e documento não é flexível.'))

class IPessoaOrigem(IBaseFormSchema):

    form.mode(protocolo_id='hidden')
    protocolo_id = schema.Int(
        title=_(u'ID do Protocolo'),
        description=_(u'Identificador do Protocolo.'),
        defaultFactory=getProtocoloId,
        required=False)

    form.widget(pessoa_id=AutocompleteMultiFieldWidget)
    pessoa_id = schema.List(
        title=_(u'Pessoa'),
        description=_(u'Origem do Protocolo.'),
        value_type=schema.Choice(vocabulary='il.spdo.pessoa-vocab'))
        
class IPessoaDestino(IBaseFormSchema):

    form.mode(protocolo_id='hidden')
    protocolo_id = schema.Int(
        title=_(u'ID do Protocolo'),
        description=_(u'Identificador do Protocolo.'),
        defaultFactory=getProtocoloId,
        required=False)

    form.widget(pessoa_id=AutocompleteMultiFieldWidget)
    pessoa_id = schema.List(
        title=_(u'Pessoa'),
        description=_(u'Destinatário do Protocolo.'),
        value_type=schema.Choice(vocabulary='il.spdo.pessoa-vocab'))

class ITipoEntrega(IBaseFormSchema):

    form.mode(id='hidden')
    id = schema.Int(
        title=_(u'ID'),
        description=_(u'Identificador do Tipo de Entrega.'),
        required=False)

    nome = schema.TextLine(
        title=_(u'Nome'),
        description=_(u'Informe o nome do tipo do entrega.'))

class IEntrega(IBaseFormSchema):

    form.mode(protocolo_id='hidden')
    protocolo_id = schema.Int(
        title=_(u'ID do Protocolo'),
        description=_(u'Identificador do Protocolo.'),
        defaultFactory=getProtocoloId)

    form.mode(pessoa_id='hidden')
    pessoa_id = schema.Int(
        title=_(u'ID da Pessoa'),
        description=_(u'Identificador da Pessoa.'))
        
    tipoentrega_id = schema.Choice(
        title=_(u'Tipo de Entrega'),
        description=_(u'Selecione o tipo de entrega.'),
        vocabulary='il.spdo.tipoentrega-vocab')

    form.widget(data_entrega=DateFieldWidget)
    data_entrega = schema.Date(
        title=_(u'Data de Entrega'),
        description=_(u'Informe a data de entrega do protocolo expedido.'),
        defaultFactory=datetime.date.today,
        required=False)

    objeto_correios = schema.TextLine(
        title=_(u'Objeto dos Correios'),
        description=_(u'Informe o identificador do objeto dos correios, quando for o caso.'),
        max_length=20,
        required=False)

class IObservacao(IBaseFormSchema):

    form.mode(id='hidden')
    id = schema.Int(
        title=_(u'ID'),
        description=_(u'Identificador da Observação.'),
        required=False)

    form.mode(protocolo_id='hidden')
    protocolo_id = schema.Int(
        title=_(u'ID do Protocolo'),
        description=_(u'Identificador do Protocolo.'),
        defaultFactory=getProtocoloId,
        required=False)

    texto = schema.Text(
        title=_(u'Texto'),
        description=_(u'Texto da Observação.'))

class IAddAnexo(IBaseFormSchema):

    form.mode(protocolo_id='hidden')
    protocolo_id = schema.Int(
        title=_(u'ID do Protocolo'),
        description=_(u'Identificador do Protocolo.'),
        defaultFactory=getProtocoloId,
        required=False)

    if ENABLE_FLASH_MULTIFILE:
        form.widget(anexos=MultiFileFieldWidget)
    anexos = schema.List(
        title=_(u'Anexos'),
        description=_(u'Adicione anexos ao protocolo.'),
        value_type=NamedFile())

class IFluxo(IBaseFormSchema):

    form.mode(id='hidden')
    id = schema.Int(
        title=_(u'ID'),
        description=_(u'Identificador do Fluxo.'),
        required=False)

    nome = schema.TextLine(
        title=_(u'Nome'),
        description=_(u'Informe o nome do fluxo.'))

    tipoprotocolo = schema.Choice(
        title=_(u'Tipo de Protocolo'),
        description=_(u'Selecione o tipo do protocolo.'),
        vocabulary='il.spdo.tipoprotocolo-vocab')

    tipodocumento_id = schema.Choice(
        title=_(u'Tipo de Documento'),
        description=_(u'Selecione o tipo do documento.'),
        vocabulary='il.spdo.tipodocumento-vocab')

    flexivel = schema.Bool(
        title=_(u'Flexível'),
        description=_(u'O fluxo possui tramitação flexível?'),
        required=False)

class IAddTransicao(IBaseFormSchema):

    form.mode(fluxo_id='hidden')
    fluxo_id = schema.Int(
        title=_(u'ID'),
        description=_(u'Identificador do Fluxo.'),
        required=False)

    inicial = schema.Bool(
        title=_(u'Inicial'),
        description=_(u'Transição inicial?'),
        required=False)

    area_origem_id = schema.List(
        title=_(u'Área de Origem'),
        description=_(u'Selecione as Áreas de Origem.'),
        value_type=schema.Choice(vocabulary='il.spdo.areas-vocab'))

    area_destino_id = schema.List(
        title=_(u'Áreas de Destino'),
        description=_(u'Selecione as Áreas de Destino.'),
        value_type=schema.Choice(vocabulary='il.spdo.areas-vocab'))

class IEtiquetas(IBaseFormSchema):

    formato = schema.Choice(
        title=_(u'Formato das Etiquetas'),
        description=_(u'Verifique o tamanho da folha, número de linhas e colunas e a referência do fabricante para escolher a opção adequada.'),
        vocabulary='il.spdo.formato-vocab')

class INumeroProtocolo(IBaseFormSchema):

    numero = schema.TextLine(
        title=_(u'Número do Protocolo'),
        description=_(u'Informe o número do protocolo ou utilize um scanner de código de barras para efetuar a leitura.'),
        max_length=18)    

class ISearchProtocolo(IBaseFormSchema):

    tipoprotocolo = schema.Choice(
        title=_(u'Tipo de Protocolo'),
        description=_(u'Selecione o tipo do protocolo.'),
        vocabulary='il.spdo.tipoprotocolo-vocab',
        defaultFactory=getTipoProtocolo,
        required=False)

    tipodocumento_id = schema.Choice(
        title=_(u'Tipo de Documento'),
        description=_(u'Selecione o tipo do documento.'),
        vocabulary='il.spdo.tipodocumento-vocab',
        defaultFactory=getTipoDocumento,
        required=False)

    assunto = schema.TextLine(
        title=_(u'Assunto'),
        description=_(u'Informe o assunto do documento.'),
        max_length=100,
        defaultFactory=getAssunto,
        required=False)

    situacao_id = schema.Choice(
        title=_(u'Situação'),
        description=_(u'Selecione a situação atual do protocolo.'),
        vocabulary='il.spdo.situacao-atual-vocab',
        defaultFactory=getSituacao,
        required=False)
    
    origem = schema.TextLine(
        title=_(u'Origem'),
        description=_(u'Informe a origem.'),
        max_length=100,
        defaultFactory=getOrigem,
        required=False)
    
    destino = schema.TextLine(
        title=_(u'Destino'),
        description=_(u'Informe o destino.'),
        max_length=100,
        defaultFactory=getDestino,
        required=False)

    area_id = schema.Choice(
        title=_(u'Área'),
        description=_(u'Selecione a área onde o protocolo deve estar tramitando.'),
        vocabulary='il.spdo.areas-vocab',
        required=False,
        defaultFactory=getArea)

    tempo_inativo = schema.Int(
        title=_(u'Tempo Inativo (em dias)'),
        description=_(u'Exibir somente os protocolos que estão tramitando por pelo menos um determinado tempo.'),
        defaultFactory=getTempoInativo,
        required=False)

# Validadores #

@form.validator(field=IPessoa['cep'])
def validateCep(value):
    if value:
        value = ''.join([c for c in value if c.isdigit()])
        if len(value) != 8:
            raise interface.Invalid(_(u'CEP inválido.'))

@form.validator(field=IPessoa['email'])
def validateEmail(value):
    if value and re.compile(EMAIL_RE).match(value) is None:
        raise interface.Invalid(_(u'E-mail inválido.'))

@form.validator(field=IPessoa['cpf_cnpj'])
def validateCPFCNPJ(value):
    if value and not valida_cpf_cnpj(value):
        raise interface.Invalid(_(u'CPF/CNPJ inválido.'))

@form.validator(field=IAddProtocolo['origem'])
def validateOrigem(value):
    if not value:
        raise interface.Invalid(_(u'Ao menos uma origem deve ser informada.'))

@form.validator(field=IAddProtocolo['destino'])
def validateDestino(value):
    if not value:
        raise interface.Invalid(_(u'Ao menos um destino deve ser informado.'))

@form.validator(field=IAddTramite['areas'])
def validateAreaDestino(value):
    if not value:
        raise interface.Invalid(_(u'Ao menos uma área deve ser informada.'))

@form.validator(field=IAddTransicao['area_origem_id'])
def validateAreaOrigemTransicao(value):
    if not value:
        raise interface.Invalid(_(u'Selecione pelo menos uma área de origem.'))

@form.validator(field=IAddTransicao['area_destino_id'])
def validateAreaDestinoTransicao(value):
    if not value:
        raise interface.Invalid(_(u'Selecione pelo menos uma área de destino.'))
