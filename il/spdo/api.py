# -*- coding: utf-8 -*-

import os
import datetime
import sqlalchemy as rdb
from sqlalchemy.orm import aliased

from five import grok
from zope.interface import Interface
from zope.component import getMultiAdapter, getUtility
from zope.globalrequest import getRequest
from zope.app.component.hooks import getSite
from Products.CMFCore.utils import getToolByName

from il.spdo.config import MessageFactory as _
from il.spdo import db
from il.spdo.config import Session, PATH_ANEXOS, SEARCH_LIMIT, NOTIFICACAO_ASSUNTO, NOTIFICACAO_MSG
from il.spdo.saconfig import ScopeID
from il.spdo.nav import url
from il.spdo.log import log, logger
from il.spdo.interfaces import (ISPDOAPI, ISecurityChecker,
getTipoProtocolo, getTipoDocumento, getAssunto, getSituacao,
getOrigem, getDestino, getArea, getTempoInativo)

class SPDOAPI(grok.GlobalUtility):
    """API SPDO.
    """
    grok.provides(ISPDOAPI)

    def getAuthId(self):
        """Retorna o identificador do usuário autenticado (username).
        """
        context = getSite()
        request = getRequest()
        portal_state = getMultiAdapter((context, request), name=u'plone_portal_state')
        return portal_state.member().getId()

    def getAuthPessoa(self):
        """Retorna o objeto Pessoa que representa o usuário autenticado.
        """
        session = Session()
        return session.query(db.Pessoa).filter_by(email=self.getAuthId()).first()

    def getPessoaByEmail(self, email):
        """Retorna um objeto pessoa a partir do email.
        """
        session = Session()
        return session.query(db.Pessoa).filter_by(email=email).first()

    def getProtocoloId(self):
        """Retorna o valor do parâmetro protocolo_id.
        """
        r = getRequest()
        id = r.get('protocolo_id', r.get('form.widgets.protocolo_id', None))
        if id is not None:
            id = int(id)
        return id

    def getProtocolo(self, id=None):
        """Retorna o objeto Protocolo a partir do ID.
        """
        session = Session()
        if id is None:
            id = self.getProtocoloId()
        return session.query(db.Protocolo).get(id)

    def getFluxoId(self):
        """Retorna o valor do parâmetro fluxo_id.
        """
        r = getRequest()
        id = r.get('fluxo_id', r.get('form.widgets.fluxo_id', None))
        if id is not None:
            id = int(id)
        return id

    def getFluxo(self, id=None):
        """Retorna o objeto Fluxo a partir do ID.
        """
        session = Session()
        if id is None:
            id = self.getFluxoId()
        return session.query(db.Fluxo).get(id)

    @log
    def addProtocolo(self, tipoprotocolo, tipodocumento_id, numero_documento, data_emissao, assunto, situacao_id, origem, destino, **kwargs):
        """Adiciona protocolo.
        """
        session = Session()
        protocolo = db.Protocolo(
                    tipoprotocolo=tipoprotocolo,
                    tipodocumento_id=tipodocumento_id,
                    numero_documento=numero_documento,
                    data_emissao=data_emissao,
                    assunto=assunto,
                    situacao_id=situacao_id,
                    usuario=self.getAuthId(),
                    )
        session.add(protocolo)
        session.flush()
        protocolo_id = protocolo.id
        for pessoa_id in origem:
            pessoa_origem = db.PessoaOrigem(
                            protocolo_id=protocolo_id,
                            pessoa_id=pessoa_id,
                            )
            session.add(pessoa_origem)
        for pessoa_id in destino:
            pessoa_destino = db.PessoaDestino(
                             protocolo_id=protocolo_id,
                             pessoa_id=pessoa_id,
                             )
            session.add(pessoa_destino)
        session.flush()
        return protocolo_id

    @log
    def addObservacao(self, protocolo_id, texto):
        """Adiciona observação.
        """
        if not texto:
            return
        session = Session()
        observacao = db.Observacao(
                     protocolo_id=protocolo_id,
                     texto=texto,
                     usuario=self.getAuthId(),
                     )
        session.add(observacao)
        session.flush()
        return observacao.id

    @log
    def addAnexos(self, protocolo_id, anexos):
        """Adiciona anexos.
        """
        p = self.getProtocolo(protocolo_id)
        if p is None or anexos is None:
            return []
        session = Session()
        path_protocolo = os.path.join(PATH_ANEXOS, ScopeID(), str(p.ano), str(p.id))
        if not os.path.exists(path_protocolo):
            os.makedirs(path_protocolo, 0700)
        ret = []
        for arquivo in anexos:
            anexo = db.Anexo(
                    protocolo_id=protocolo_id,
                    arquivo=arquivo.filename,
                    tamanho=arquivo.getSize(),
                    usuario=self.getAuthId(),
                    )
            session.add(anexo)
            session.flush()
            ret.append(anexo.id)
            path_anexo = os.path.join(path_protocolo, str(anexo.id))
            with open(path_anexo, 'w') as file_anexo:
                file_anexo.write(arquivo.data)
        # propaga anexos nos apensos
        for apenso in p.apenso:
            ret.extend(self.addAnexos(apenso.id, anexos))
        return ret

    def _add_box(self, box, protocolo_id, area_id):
        assert(box in (db.TramiteInbox, db.TramiteOutbox))
        session = Session()
        t = session.query(box).get((protocolo_id, area_id))
        if t is None:
            t = box()
            t.protocolo_id=protocolo_id
            t.area_id=area_id
            tbl = box is db.TramiteInbox and 'tramite_inbox' or 'tramite_outbox'
            t.version = db.nextVersion(tbl, protocolo_id=protocolo_id, area_id=area_id)
            session.add(t)
    
    def _del_box(self, box, protocolo_id, area_id):
        assert(box in (db.TramiteInbox, db.TramiteOutbox))
        session = Session()
        t = session.query(box).get((protocolo_id, area_id))
        if t is not None:
            session.delete(t)

    @log
    def TramiteInicial(self, protocolo_id):
        """Tramite inicial.
        """
        session = Session()
        area_id_auth = self.getAuthPessoa().area_id
        tramite = db.Tramite(
                  protocolo_id=protocolo_id,
                  area_id=area_id_auth,
                  data_disponibilizacao=None,
                  data_recebimento=datetime.datetime.now(),
                  despacho=_(u'Protocolo Criado'),
                  usuario=self.getAuthId(),
                  )
        session.add(tramite)
        self._add_box(db.TramiteInbox, protocolo_id, area_id_auth)
        session.flush()

    def TramiteEnvio(self, protocolos, areas, despacho):
        """Wrapper do tramite de envio.
        """
        protocolos_tramitados = self._TramiteEnvio(protocolos, areas, despacho)
        self._EnviaNotificacoes(protocolos_tramitados)

    @log
    def _TramiteEnvio(self, protocolos, areas, despacho, apenso=False):
        """Tramite de envio.
        """
        protocolos = list(set(protocolos))
        areas = list(set(areas))
        session = Session()
        area_id_auth = self.getAuthPessoa().area_id
        # evita o envio para a própria área
        if areas.count(area_id_auth):
            areas.pop(areas.index(area_id_auth))
        copia = len(areas) > 1
        ret = []
        for protocolo_id in protocolos:
            ret.append(protocolo_id)
            protocolo = self.getProtocolo(protocolo_id)
            if not apenso:
                sc = getUtility(ISecurityChecker)
                msg = _(u'Protocolo não disponível para envio. Protocolo: ') + protocolo.numero
                sc.enforce('tramitar_envio', protocolo_id=protocolo_id, msg=msg)                
            for area_id in areas:
                tramite = db.Tramite(
                          protocolo_id=protocolo_id,
                          area_id=area_id,
                          data_disponibilizacao=datetime.datetime.now(),
                          data_recebimento=None,
                          despacho=despacho,
                          usuario=self.getAuthId(),
                          copia=copia,
                          area_id_anterior=area_id_auth,
                          )
                session.add(tramite)
                self._add_box(db.TramiteOutbox, protocolo_id, area_id_auth)
                self._del_box(db.TramiteInbox, protocolo_id, area_id_auth)
                session.flush()
            # propaga tramitação nos apensos
            for apenso in protocolo.apenso:
                ret.extend(self._TramiteEnvio([apenso.id], areas, despacho, apenso=True))
        return ret
    
    def TramiteRecebimento(self, protocolos):
        """Wrapper do tramite de recebimento.
        """
        self._TramiteRecebimento(protocolos)
    
    @log
    def _TramiteRecebimento(self, protocolos, apenso=False):
        """Tramite de recebimento.
        """
        protocolos = list(set(protocolos))
        session = Session()
        area_id_auth = self.getAuthPessoa().area_id
        ret = []
        for protocolo_id in protocolos:
            ret.append(protocolo_id)
            protocolo = self.getProtocolo(protocolo_id)
            if not apenso:
                sc = getUtility(ISecurityChecker)
                msg = _(u'Protocolo não disponível para recebimento. Protocolo: ') + protocolo.numero
                sc.enforce('tramitar_recebimento', protocolo_id=protocolo_id, msg=msg)
            tramite = session.query(db.Tramite).\
                      filter_by(protocolo_id=protocolo_id).\
                      filter_by(area_id=area_id_auth).\
                      filter_by(data_recebimento=None).first()
            tramite.data_recebimento=datetime.datetime.now()
            self._add_box(db.TramiteInbox, protocolo_id, area_id_auth)
            self._del_box(db.TramiteOutbox, protocolo_id, tramite.area_id_anterior)
            # propaga tramitação nos apensos
            for apenso in protocolo.apenso:
                ret.extend(self._TramiteRecebimento([apenso.id], apenso=True))
        return ret

    def TramiteRecuperacao(self, protocolos):
        """Wrapper do tramite de recuperação.
        """
        self._TramiteRecuperacao(protocolos)

    @log
    def _TramiteRecuperacao(self, protocolos, apenso=False):
        """Tramite de recuperação (recupera um protocolo enviado que não foi recebido).
        """
        protocolos = list(set(protocolos))
        session = Session()
        area_id_auth = self.getAuthPessoa().area_id
        ret = []
        for protocolo_id in protocolos:
            ret.append(protocolo_id)
            protocolo = self.getProtocolo(protocolo_id)
            if not apenso:
                sc = getUtility(ISecurityChecker)
                msg = _(u'Protocolo não disponível para recuperação. Protocolo: ') + protocolo.numero
                sc.enforce('tramitar_recuperacao', protocolo_id=protocolo_id, msg=msg)
            tramites = session.query(db.Tramite).\
                       filter_by(protocolo_id=protocolo_id).\
                       filter_by(area_id_anterior=area_id_auth).\
                       filter_by(data_recebimento=None).all()
            for tramite in tramites:
                session.delete(tramite)
            self._add_box(db.TramiteInbox, protocolo_id, area_id_auth)
            self._del_box(db.TramiteOutbox, protocolo_id, area_id_auth)
            # propaga tramitação nos apensos
            for apenso in protocolo.apenso:
                ret.extend(self._TramiteRecuperacao([apenso.id], apenso=True))
        return ret

    def _getProtocolosData(self, protocolos):
        ret = []
        for i in protocolos:
            ret.append({
               'id': i.id,
               'numero': i.numero,
               'data_protocolo': i.data_protocolo,
               'assunto': i.assunto,
               'tipodocumento': i.tipodocumento.nome,
               'situacao': i.situacao.nome,
               'url': url('show-protocolo', id=i.id),
               })
        return ret

    def getProtocolosCriadosRecebidos(self):
        """Consulta os protocolos criados ou recebidos pela área.
        """
        session = Session()
        area_id_auth = self.getAuthPessoa().area_id
        items = session.query(db.TramiteInbox).\
                filter_by(area_id=area_id_auth).\
                join(db.Protocolo).\
                filter(db.Protocolo.apenso_id == None).\
                join(db.Situacao).\
                filter(db.Situacao.final == False).all()
        return self._getProtocolosData([i.protocolo for i in items])

    def getProtocolosNaoRecebidos(self):
        """Consulta os protocolos não recebidos pela área.
        """
        session = Session()
        area_id_auth = self.getAuthPessoa().area_id
        items = session.query(db.Tramite).\
                filter_by(area_id=area_id_auth).\
                filter_by(data_recebimento=None).\
                join(db.Protocolo).\
                filter(db.Protocolo.apenso_id == None).\
                join(db.Situacao).\
                filter(db.Situacao.final == False).all()
        return self._getProtocolosData([i.protocolo for i in items])

    def getProtocolosEnviados(self):
        """Consulta os protocolos enviados pela área.
        """
        session = Session()
        area_id_auth = self.getAuthPessoa().area_id
        items = session.query(db.TramiteOutbox).\
                filter_by(area_id=area_id_auth).\
                join(db.Protocolo).\
                filter(db.Protocolo.apenso_id == None).\
                join(db.Situacao).\
                filter(db.Situacao.final == False).all()
        return self._getProtocolosData([i.protocolo for i in items])

    def pesquisaProtocolos(self):
        """Pesquisa protocolos.
        """
        session = Session()
        items = session.query(db.Protocolo)

        tipoprotocolo = getTipoProtocolo()
        if tipoprotocolo is not None:
            items = items.filter_by(tipoprotocolo=tipoprotocolo)

        tipodocumento_id = getTipoDocumento()
        if tipodocumento_id is not None:
            items = items.filter_by(tipodocumento_id=tipodocumento_id)

        assunto = getAssunto()
        if assunto is not None:
            clause = rdb.or_(db.Protocolo.assunto.contains(assunto),
                             db.Protocolo.assunto.ilike(assunto))
            items = items.filter(clause)

        situacao_id = getSituacao()
        if situacao_id is not None:
            items = items.filter_by(situacao_id=situacao_id)

        origem = getOrigem()
        if origem is not None:
            pessoa1 = aliased(db.Pessoa)
            items = items.join(db.PessoaOrigem).join(pessoa1)
            clause = rdb.or_(pessoa1.nome.contains(origem),
                             pessoa1.nome.ilike(origem))
            items = items.filter(clause)

        destino = getDestino()
        if destino is not None:
            pessoa2 = aliased(db.Pessoa)
            items = items.join(db.PessoaDestino).join(pessoa2)
            clause = rdb.or_(pessoa2.nome.contains(destino),
                             pessoa2.nome.ilike(destino))
            items = items.filter(clause)

        area_id = getArea()
        if area_id is not None:
            inbox1 = aliased(db.TramiteInbox)
            items = items.join(inbox1).filter_by(area_id=area_id)

        tempo_inativo = getTempoInativo()
        if tempo_inativo is not None:
            d = datetime.datetime.now() - datetime.timedelta(days=tempo_inativo)
            inbox2 = aliased(db.TramiteInbox)
            items = items.join(inbox2).filter(inbox2.version_date < d)

        return self._getProtocolosData(items.limit(SEARCH_LIMIT).all())

    def _EnviaNotificacoes(self, protocolos):
        """Envia emails de notificação, avisando as pessoas
        interessadas que os protocolos tramitaram.
        """
        protocolos = list(set(protocolos))
        pu = getToolByName(getSite(), 'portal_url')
        portal = pu.getPortalObject()
        mh = portal.MailHost
        session = Session()
        for protocolo_id in protocolos:
            notificacoes = session.query(db.Notificacao).\
                           filter_by(protocolo_id=protocolo_id).all()
            for notificacao in notificacoes:
                logger(_(u'Notificando ') + notificacao.pessoa.email)

                # TODO: refatorar. Essa lista de tramites pode vir
                # pronta do método TramiteEnvio, evitando notificações
                # desnecessárias nas tramitações por cópia.

                tramites = session.query(db.Tramite).\
                           filter_by(protocolo_id=protocolo_id).\
                           filter_by(data_recebimento=None).all()
                for tramite in tramites:
                    d = {'numero': notificacao.protocolo.numero,
                         'data_tramitacao': tramite.data_disponibilizacao,
                         'assunto': notificacao.protocolo.assunto,
                         'area_origem': tramite.area_anterior.nome,
                         'responsavel_origem': tramite.area_anterior.responsavel[-1].pessoa.nome,
                         'area_destino': tramite.area.nome,
                         'responsavel_destino': tramite.responsavel.pessoa.nome,
                         'situacao': notificacao.protocolo.situacao.nome,
                         'url_protocolo': url('show-protocolo', id=notificacao.protocolo.id),
                         'url_notificacoes': url('list-notificacao')}
                    mfrom=unicode(portal.getProperty('email_from_address'), 'utf-8')
                    mto=notificacao.pessoa.email
                    subject=NOTIFICACAO_ASSUNTO % d
                    body=NOTIFICACAO_MSG % d
                    text = u"From: %s\nTo: %s\nSubject: %s\n\n%s" % (mfrom, mto, subject, body)
                    try:
                        mh.send(text, immediate=True, charset='utf8')
                    except:
                        logger(_(u'Erro ao enviar a mensagem de notificação.'))
