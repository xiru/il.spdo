# -*- coding: utf-8 -*-

import bcrypt

from zope.interface import Interface
from zope.component import getUtility
from zope.app.component.hooks import getSite
from zope.globalrequest import getRequest
from five import grok
from AccessControl import Unauthorized
from Products.CMFCore.utils import getToolByName

from il.spdo.config import MessageFactory as _
from il.spdo.config import Session
from il.spdo import db
from il.spdo.interfaces import ISPDOAPI, ISecurityChecker
from il.spdo.log import logger

ROLE_USUARIO = 'Usuario SPDO'
ROLE_OPERADOR = 'Operador SPDO'
ROLE_GESTOR = 'Gestor SPDO'
ROLE_ADMIN = 'Manager'

TRAMITANDO = ('protocolo_tramita_area', 'protocolo_situacao_final', 'protocolo_apensado')

CONFIG = {
    'acessar_add_anexo': ('privilegio_admin', TRAMITANDO),
    'acessar_add_apenso': (('protocolo_tramita_area', 'protocolo_situacao_final'),),
    'acessar_add_notificacao': ('privilegio_usuario',),
    'acessar_add_observacao': ('privilegio_admin', TRAMITANDO),
    'acessar_add_pessoadestino': (TRAMITANDO,),
    'acessar_add_pessoaorigem': (TRAMITANDO,),
    'acessar_add_pessoa': ('privilegio_admin', 'privilegio_operador'),
    'acessar_add_protocolo': ('privilegio_operador',),
    'acessar_add_referencia': (TRAMITANDO,),
    'acessar_add_tramite': (TRAMITANDO,),
    'acessar_ajuda': ('privilegio_admin', 'privilegio_operador'),
    'acessar_edit_observacao': ('privilegio_admin', TRAMITANDO + ('privilegio_criador_observacao',)),
    'acessar_edit_pessoadestino': (TRAMITANDO,),
    'acessar_edit_pessoa': ('privilegio_admin', 'privilegio_operador'),
    'acessar_edit_protocolo': (('protocolo_tramita_area', 'protocolo_apensado'),),
    'acessar_envio_tramite': ('privilegio_operador',),
    'acessar_list_notificacao': ('privilegio_usuario',),
    'acessar_list_pessoa': ('privilegio_admin', 'privilegio_operador'),
    'acessar_list_protocolo': ('privilegio_operador',),
    'acessar_list_referencia': ('privilegio_admin', 'privilegio_usuario'),
    'acessar_print_etiquetas': ('privilegio_operador',),
    'acessar_recebimento_tramite_barra': ('privilegio_operador',),
    'acessar_recebimento_tramite': ('privilegio_operador',),
    'acessar_recuperacao_tramite': ('privilegio_operador',),
    'acessar_remove_anexo': ('privilegio_admin', TRAMITANDO + ('privilegio_criador_anexo',)),    
    'acessar_remove_notificacao': ('privilegio_usuario',),
    'acessar_remove_observacao': ('privilegio_admin', TRAMITANDO + ('privilegio_criador_observacao',)),
    'acessar_remove_pessoadestino': (TRAMITANDO,),
    'acessar_remove_pessoaorigem': (TRAMITANDO,),
    'acessar_remove_referencia': (TRAMITANDO,),
    'acessar_search_protocolo_barra': ('privilegio_admin', 'privilegio_usuario'),
    'acessar_search_protocolo': ('privilegio_admin', 'privilegio_operador'),
    'acessar_show_pessoa': ('privilegio_admin', 'privilegio_operador'),
    'acessar_show_protocolo': ('privilegio_admin', 'privilegio_usuario'),
    'acessar_ws_add_protocolo': ('privilegio_operador',),
    'ciclo_apenso': ('protocolo_apenso_ciclo',),
    'fluxo_rigoroso_area_inicial': ('protocolo_fluxo_area_inicial',),
    'fluxo_rigoroso': ('protocolo_fluxo',),
    'lotacao_pessoa': ('privilegio_admin', ('privilegio_operador', 'privilegio_gestor')),
    'momento_tramitacao': ('protocolo_apenso_momento',),
    'tramitar_envio': (TRAMITANDO,),
    'tramitar_recebimento': (('protocolo_enviado', 'protocolo_situacao_final', 'protocolo_apensado'),),
    'tramitar_recuperacao': (('protocolo_nao_recebido', 'protocolo_situacao_final', 'protocolo_apensado'),),    
    'visualizar_anexos': ('privilegio_admin', 'protocolo_tramita_area', ('privilegio_operador', 'privilegio_gestor')),
    'visualizar_despachos': ('privilegio_admin', 'protocolo_tramita_area', ('privilegio_operador', 'privilegio_gestor')),
    'visualizar_observacoes': ('privilegio_admin', 'protocolo_tramita_area', ('privilegio_operador', 'privilegio_gestor')),
    }

class SecurityCheckerUtility(grok.GlobalUtility):
    """Verificador de Segurança.
    """

    grok.provides(ISecurityChecker)

    def _run_verificacoes(self, acao, verificacoes, **kwargs):
        """Esse método executa as verificações, de acordo com as
        definições da estrutura de dados CONFIG, considerando que as
        componentes da tupla representam um OR das diversas
        possibilidades de verificação. Quando a componente for uma
        tupla, a validação deve ser calculada como um AND das
        componentes.
        """

        # o widget de autocomplete faz chamadas ajax no contexto da
        # view e esses requests não devem ser bloqueados
        if kwargs.get('ajax', None) is not None and acao.startswith('acessar_'):
            r = getRequest()
            url = r.URL
            view = acao.replace('acessar_', '/@@').replace('_', '-')
            if not url.endswith(view):
                logger(_(u'Permitindo acesso direto a URL: ') + unicode(url, 'utf-8'))
                return True

        context = self
        for v in verificacoes:
            if type(v) == type(()):
                result = True
                for vi in v:
                    func = getattr(context, "_valida_%s" % vi, None)
                    if func is None:
                        result = False
                        break
                    ret = func(**kwargs)
                    if not ret:
                        result = False
                        break
                if result:
                    return True
            else:
                func = getattr(context, "_valida_%s" % v, None)
                if func is not None:
                    ret = func(**kwargs)
                    if ret:
                        return True
        return False

    def check(self, acao, **kwargs):
        verificacoes = CONFIG.get(acao, None)
        if verificacoes is None:
            logger(_(u'Ação informada não existe na configuração do sistema. Ação: ') + unicode(acao, 'utf-8'))
            raise Unauthorized
        return self._run_verificacoes(acao, verificacoes, **kwargs)

    def enforce(self, acao, **kwargs):
        if not self.check(acao, **kwargs):
            logger(kwargs.get('msg', _(u'Privilégios Insuficientes. Ação: ') + unicode(acao, 'utf-8')))
            raise Unauthorized

    # Métodos Auxiliares #

    def _valida_role(self, role):
        pm = getToolByName(getSite(), 'portal_membership')
        return role in pm.getAuthenticatedMember().getRoles()

    def _valida_permissao(self, permissao):
        pu = getToolByName(getSite(), 'portal_url')
        pm = getToolByName(getSite(), 'portal_membership')
        portal = pu.getPortalObject()
        return pm.checkPermission(permissao, portal)

    def _get_area_usuario(self):
        pm = getToolByName(getSite(), 'portal_membership')
        user_id = str(pm.getAuthenticatedMember())
        api = getUtility(ISPDOAPI)
        pessoa = api.getPessoaByEmail(user_id)
        if pessoa is not None:
            return pessoa.area_id

    def _valida_area_responsavel(self, area_id):
        session = Session()
        return bool(session.query(db.Responsavel).\
                    filter_by(area_id=area_id).first())

    # Verificações #

    def _valida_privilegio_usuario(self, **kwargs):
        """Estar autenticado com role ROLE_USUARIO e possuir um
        registro pessoa que case com o e-mail de login.
        """
        pm = getToolByName(getSite(), 'portal_membership')
        user_id = str(pm.getAuthenticatedMember())
        api = getUtility(ISPDOAPI)
        return self._valida_role(ROLE_USUARIO) and api.getPessoaByEmail(user_id) is not None

    def _valida_privilegio_operador(self, **kwargs):
        """Estar autenticado com role ROLE_OPERADOR e possuir um
        registro pessoa lotado em uma área do organograma.
        """
        if not self._valida_role(ROLE_OPERADOR):
            return False
        area_id = self._get_area_usuario()
        if area_id is None:
            return False
        return self._valida_area_responsavel(area_id)

    def _valida_privilegio_gestor(self, **kwargs):
        """Estar autenticado com role ROLE_GESTOR e possuir um
        registro pessoa lotado em uma área do organograma.
        """
        if not self._valida_role(ROLE_GESTOR):
            return False
        area_id = self._get_area_usuario()
        if area_id is None:
            return False
        return self._valida_area_responsavel(area_id)

    def _valida_privilegio_admin(self, **kwargs):
        """Estar autenticado com ROLE_ADMIN e ter a permissão “Manage
        portal” no contexto da raiz do site.
        """
        return self._valida_role(ROLE_ADMIN) and self._valida_permissao('Manage portal')

    def _valida_privilegio_criador_anexo(self, **kwargs):
        """O anexo deve ter sido criado pelo usuário que quer
        apagá-lo. Não deve existir um tramite com data de
        disponibilização posterior a data do anexo.
        """
        anexo_id = kwargs.get('anexo_id', None)
        protocolo_id = kwargs.get('protocolo_id', None)
	if anexo_id is None or protocolo_id is None:
            logger(_(u'O método _valida_privilegio_criador_anexo não recebeu os parâmetros anexo_id ou protocolo_id.'))
            return False
        session = Session()
        api = getUtility(ISPDOAPI)
        usuario = api.getAuthId()
        anexo = session.query(db.Anexo).\
                filter_by(id=anexo_id).\
                filter_by(protocolo_id=protocolo_id).\
                filter_by(usuario=usuario).first()
        if anexo is None:
            return False
        tramite = session.query(db.Tramite).\
                  filter_by(protocolo_id=anexo.protocolo_id).\
                  filter(db.Tramite.data_disponibilizacao > anexo.data_anexo).first()
        return not bool(tramite)

    def _valida_privilegio_criador_observacao(self, **kwargs):
        """A observação deve ter sido criada pelo usuário que quer
        modificá-la ou apagá-la. Não deve existir um tramite com data
        de disponibilização posterior a data da observação.
        """
        observacao_id = kwargs.get('observacao_id', None)
        protocolo_id = kwargs.get('protocolo_id', None)
        if observacao_id is None or protocolo_id is None:
            logger(_(u'O método _valida_privilegio_criador_observacao não recebeu os parâmetros observacao_id ou protocolo_id.'))
            return False
        session = Session()
        api = getUtility(ISPDOAPI)
        usuario = api.getAuthId()
        observacao = session.query(db.Observacao).\
                     filter_by(id=observacao_id).\
                     filter_by(protocolo_id=protocolo_id).\
                     filter_by(usuario=usuario).first()
        if observacao is None:
            return False
        tramite = session.query(db.Tramite).\
                  filter_by(protocolo_id=observacao.protocolo_id).\
                  filter(db.Tramite.data_disponibilizacao > observacao.data_observacao).first()
        return not bool(tramite)

    def _valida_protocolo_apensado(self, **kwargs):
        """Protocolo não estar apensado em outro protocolo.
        """
        api = getUtility(ISPDOAPI)
        protocolo_id = kwargs.get('protocolo_id', api.getProtocoloId())
        if protocolo_id is None:
            logger(_(u'O método _valida_protocolo_apensado não recebeu o parâmetro protocolo_id.'))
            return False
        protocolo = api.getProtocolo(protocolo_id)
        if protocolo is None:
            return False
        return protocolo.apenso_id is None

    def _procura_ciclo(self, protocolo, apenso_id, ids_visitados):
        ret = False
        for p in protocolo.apenso:
            # ids_visitados evita uma recursão infinita
            if p.id in ids_visitados:
                continue
            ids_visitados.append(p.id)
            if p.id == apenso_id or self._procura_ciclo(p, apenso_id, ids_visitados):
                ret = True
                break
        return ret

    def _valida_protocolo_apenso_ciclo(self, **kwargs):
        """Não podem existir ciclos nas definições de apensos.
        """
        protocolo_id = kwargs.get('protocolo_id', None)
        apenso_id = kwargs.get('apenso_id', None)
        if protocolo_id is None or apenso_id is None:
            logger(_(u'O método _valida_protocolo_apenso_ciclo não recebeu os parâmetros protocolo_id ou apenso_id.'))
            return False
        api = getUtility(ISPDOAPI)
        protocolo = api.getProtocolo(protocolo_id)
        if protocolo is None:
            return False
        ids_visitados = []
        return not self._procura_ciclo(protocolo, apenso_id, ids_visitados)

    def _compara_protocolos(self, p1, p2):
        if p1.tipoprotocolo != p2.tipoprotocolo or p1.tipodocumento_id != p2.tipodocumento_id:
            return False
        inbox1 = [i.area_id for i in p1.tramite_inbox]; inbox1.sort()
        inbox2 = [i.area_id for i in p2.tramite_inbox]; inbox2.sort()
        if inbox1 != inbox2: return False
        outbox1 = [i.area_id for i in p1.tramite_outbox]; outbox1.sort()
        outbox2 = [i.area_id for i in p2.tramite_outbox]; outbox2.sort()
        if outbox1 != outbox2: return False
        return True

    def _valida_protocolo_apenso_momento(self, **kwargs):
        """Para que um protocolo seja apensado em outro é necessário
        que ambos compartilhem o mesmo momento na tramitação, ou seja,
        estejam tramitando nas mesmas áreas e tenham o mesmo tipo de
        documento e protocolo.
        """
        protocolo_id = kwargs.get('protocolo_id', None)
        apenso_id = kwargs.get('apenso_id', None)
        if protocolo_id is None or apenso_id is None:
            logger(_(u'O método _valida_protocolo_apenso_momento não recebeu os parâmetros protocolo_id ou apenso_id.'))
            return False
        api = getUtility(ISPDOAPI)
        protocolo = api.getProtocolo(protocolo_id)
        if protocolo is None:
            return False
        apenso = api.getProtocolo(apenso_id)
        if apenso is None:
            return False
        return self._compara_protocolos(protocolo, apenso)

    def _valida_protocolo_enviado(self, **kwargs):
        """Protocolo enviado para área de lotação do usuário mas ainda
        não recebido.
        """
        api = getUtility(ISPDOAPI)
        protocolo_id = kwargs.get('protocolo_id', api.getProtocoloId())
        if protocolo_id is None:
            logger(_(u'O método _valida_protocolo_enviado não recebeu o parâmetro protocolo_id.'))
            return False
        area_id_auth = self._get_area_usuario()
        if area_id_auth is None:
            return False
        session = Session()
        return bool(session.query(db.Tramite).\
                    filter_by(area_id=area_id_auth).\
                    filter_by(protocolo_id=protocolo_id).\
                    filter_by(data_recebimento=None).first())

    def _valida_protocolo_fluxo_area_inicial(self, **kwargs):
        """O tipo de protocolo e o tipo de documento possuem uma
        definição de fluxo rigoroso. A área onde o usuário está lotado
        deve corresponder a uma área inicial de uma das transições
        desse fluxo.
        """
        tipoprotocolo = kwargs.get('tipoprotocolo', None) 
        tipodocumento_id = kwargs.get('tipodocumento_id', None)
        if tipoprotocolo is None or tipodocumento_id is None:
            logger(_(u'O método _valida_protocolo_fluxo_area_inicial não recebeu os parâmetros tipoprotocolo e tipodocumento_id.'))
            return False
        area_id_auth = self._get_area_usuario()
        if area_id_auth is None:
            return False
        session = Session()
        fluxo = session.query(db.Fluxo).\
                filter_by(tipoprotocolo=tipoprotocolo).\
                filter_by(tipodocumento_id=tipodocumento_id).\
                filter_by(flexivel=False).first()
        if fluxo is None:
            return True
        return bool(session.query(db.Transicao).\
                    filter_by(fluxo_id=fluxo.id).\
                    filter_by(area_origem_id=area_id_auth).\
                    filter_by(inicial=True).first())

    def _valida_protocolo_fluxo(self, **kwargs):
        """O tipo de protocolo e o tipo de documento possuem uma
        definição de fluxo rigoroso. A tramitação de envio deve seguir
        uma transição desse fluxo.
        """
        protocolo_id = kwargs.get('protocolo_id', None)
        areas = kwargs.get('areas', [])
        if protocolo_id is None or not areas:
            logger(_(u'O método _valida_protocolo_fluxo não recebeu os parâmetros protocolo_id e areas.'))
            return False
        api = getUtility(ISPDOAPI)
        protocolo = api.getProtocolo(protocolo_id)
        if protocolo is None:
            return False
        tipoprotocolo = protocolo.tipoprotocolo
        tipodocumento_id = protocolo.tipodocumento_id
        session = Session()
        fluxo = session.query(db.Fluxo).\
                filter_by(tipoprotocolo=tipoprotocolo).\
                filter_by(tipodocumento_id=tipodocumento_id).\
                filter_by(flexivel=False).first()
        if fluxo is None:
            return True
        area_id_auth = self._get_area_usuario()
        if area_id_auth is None:
            return False
        for area in areas:
            if not bool(session.query(db.Transicao).\
                        filter_by(fluxo_id=fluxo.id).\
                        filter_by(area_origem_id=area_id_auth).\
                        filter_by(area_destino_id=area).first()):
                return False
        return True

    def _valida_protocolo_nao_recebido(self, **kwargs):
        """Protocolo enviado pela área de lotação do usuário mas ainda
        não recebido pela área destino.
        """
        api = getUtility(ISPDOAPI)
        protocolo_id = kwargs.get('protocolo_id', api.getProtocoloId())
        if protocolo_id is None:
            logger(_(u'O método _valida_protocolo_nao_recebido não recebeu o parâmetro protocolo_id.'))
            return False
        area_id_auth = self._get_area_usuario()
        if area_id_auth is None:
            return False
        session = Session()
        return bool(session.query(db.TramiteOutbox).\
                    filter_by(area_id=area_id_auth).\
                    filter_by(protocolo_id=protocolo_id).first())

    def _valida_protocolo_situacao_final(self, **kwargs):
        """Protocolo não pode estar em situação final.
        """
        api = getUtility(ISPDOAPI)
        protocolo_id = kwargs.get('protocolo_id', api.getProtocoloId())
        if protocolo_id is None:
            logger(_(u'O método _valida_protocolo_situacao_final não recebeu o parâmetro protocolo_id.'))
            return False
        protocolo = api.getProtocolo(protocolo_id)
        if protocolo is None:
            return False
        return not protocolo.situacao.final

    def _valida_protocolo_tramita_area(self, **kwargs):
        """Protocolo tramita na área onde o usuário autenticado está
        lotado.
        """
        api = getUtility(ISPDOAPI)
        protocolo_id = kwargs.get('protocolo_id', api.getProtocoloId())
        if protocolo_id is None:
            logger(_(u'O método _valida_protocolo_tramita_area não recebeu o parâmetro protocolo_id.'))
            return False
        area_id_auth = self._get_area_usuario()
        if area_id_auth is None:
            return False
        session = Session()
        return bool(session.query(db.TramiteInbox).\
                    filter_by(protocolo_id=protocolo_id).\
                    filter_by(area_id=area_id_auth).first())


def verifica_senha(email, senha_plain):
    """Verifica se a senha informada confere com o hash armazenado."""
    api = getUtility(ISPDOAPI)
    pessoa = api.getPessoaByEmail(email)
    return bcrypt.hashpw(senha_plain, pessoa.senha) == pessoa.senha

def modifica_senha(email, senha_plain):
    """Altera a senha de uma pessoa, gerando um novo hash."""
    api = getUtility(ISPDOAPI)
    pessoa = api.getPessoaByEmail(email)
    pessoa.senha = bcrypt.hashpw(senha_plain, bcrypt.gensalt())
