# -*- coding: utf-8 -*-

import os
import json
import datetime

from five import grok
from zope.component import getUtility
from zope.schema.interfaces import IVocabularyFactory
from zope.interface import implements
from plone.app.layout.navigation.interfaces import INavigationRoot
from plone.namedfile.utils import set_headers, stream_data
from plone.namedfile.file import NamedFile
from Products.statusmessages.interfaces import IStatusMessage
from Products.Five import BrowserView

from il.spdo.config import Session, PATH_ANEXOS
from il.spdo.saconfig import ScopeID
from il.spdo import db
from il.spdo.config import MessageFactory as _
from il.spdo.log import log
from il.spdo.nav import go, url
from il.spdo.interfaces import ISPDOAPI, ISecurityChecker

class BaseListView(object):
    
    def show_url(self, id, vs=None):
        vs = self.view_sufix if vs is None else vs
        return url('show-'+vs, id=id)

    def add_url(self, vs=None):
        vs = self.view_sufix if vs is None else vs
        return url('add-'+vs)

class AreaListView(grok.View, BaseListView):

    grok.name('list-area')
    grok.context(INavigationRoot)
    grok.require('cmf.ManagePortal')

    dados = []
    view_sufix = 'area'

    @log
    def update(self):
        self.request.set('disable_border', True)
        self.dados = []
        session = Session()
        items = session.query(db.Area).all()
        for i in items:
            self.dados.append({
               'id': i.id,
               'sigla': i.sigla,
               'nome': i.nome,
               'chefia_id': i.chefia_id,
               'chefia_sigla': getattr(i.area,'sigla',''),
               'chefia_nome': getattr(i.area,'nome',''),
               })

class UFListView(grok.View, BaseListView):

    grok.name('list-uf')
    grok.context(INavigationRoot)
    grok.require('cmf.ManagePortal')

    dados = []
    view_sufix = 'uf'

    @log
    def update(self):
        self.request.set('disable_border', True)
        self.dados = []
        session = Session()
        items = session.query(db.UF).all()
        for i in items:
            self.dados.append({
               'id': i.id,
               'sigla': i.sigla,
               'nome': i.nome,
               })

class PessoaListView(grok.View, BaseListView):
    
    grok.name('list-pessoa')
    grok.context(INavigationRoot)
    grok.require('zope2.View')

    dados = []
    view_sufix = 'pessoa'

    @log
    def update(self):
        sc = getUtility(ISecurityChecker)
        sc.enforce('acessar_list_pessoa')
        self.request.set('disable_border', True)
        self.dados = []
        session = Session()
        items = session.query(db.Pessoa).all()
        for i in items:
            self.dados.append({
               'id': i.id,
               'nome': i.nome,
               'email': i.email,
               })

class ResponsavelListView(grok.View, BaseListView):

    grok.name('list-responsavel')
    grok.context(INavigationRoot)
    grok.require('cmf.ManagePortal')

    dados = []
    view_sufix = 'responsavel'

    @log
    def update(self):
        self.request.set('disable_border', True)
        self.dados = []
        session = Session()
        items = session.query(db.Responsavel).all()
        for i in items:
            self.dados.append({
                'id': i.id,
                'area_id': i.area_id,
                'area_sigla': i.area.sigla,
                'area_nome': i.area.nome,
                'pessoa_id': i.pessoa_id,
                'pessoa_nome': i.pessoa.nome,
                'pessoa_email': i.pessoa.email,
                'data_responsavel': i.data_responsavel,
                'url-area': url('show-area', id=i.area_id),
                'url-pessoa': url('show-pessoa', id=i.pessoa_id),
               })

class TipoDocumentoListView(grok.View, BaseListView):

    grok.name('list-tipodocumento')
    grok.context(INavigationRoot)
    grok.require('cmf.ManagePortal')

    dados = []
    view_sufix = 'tipodocumento'

    @log
    def update(self):
        self.request.set('disable_border', True)
        self.dados = []
        session = Session()
        items = session.query(db.TipoDocumento).all()
        for i in items:
            self.dados.append({
               'id': i.id,
               'nome': i.nome,
               })

class SituacaoListView(grok.View, BaseListView):

    grok.name('list-situacao')
    grok.context(INavigationRoot)
    grok.require('cmf.ManagePortal')

    dados = []
    view_sufix = 'situacao'

    @log
    def update(self):
        self.request.set('disable_border', True)
        self.dados = []
        session = Session()
        items = session.query(db.Situacao).all()
        for i in items:
            self.dados.append({
               'id': i.id,
               'nome': i.nome,
               'inicial': i.inicial,
               'final': i.final,
               })

class TipoEntregaListView(grok.View, BaseListView):

    grok.name('list-tipoentrega')
    grok.context(INavigationRoot)
    grok.require('cmf.ManagePortal')

    dados = []
    view_sufix = 'tipoentrega'

    @log
    def update(self):
        self.request.set('disable_border', True)
        self.dados = []
        session = Session()
        items = session.query(db.TipoEntrega).all()
        for i in items:
            self.dados.append({
               'id': i.id,
               'nome': i.nome,
               })

class FluxoListView(grok.View, BaseListView):

    grok.name('list-fluxo')
    grok.context(INavigationRoot)
    grok.require('cmf.ManagePortal')

    dados = []
    view_sufix = 'fluxo'

    def _tipo_protocolo(self, tipoprotocolo):
        tpvf = getUtility(IVocabularyFactory, 'il.spdo.tipoprotocolo-vocab')
        tpv = tpvf(self.context)
        return tpv.getTerm(tipoprotocolo).title

    @log
    def update(self):
        self.request.set('disable_border', True)
        self.dados = []
        session = Session()
        items = session.query(db.Fluxo).all()
        for i in items:
            self.dados.append({
               'id': i.id,
               'nome': i.nome,
               'tipoprotocolo': self._tipo_protocolo(i.tipoprotocolo),
               'tipodocumento': i.tipodocumento.nome,
               'flexivel': i.flexivel,
               'url-transicao': url('list-transicao', fluxo_id=i.id),
               })

class TransicaoRemoveView(grok.View):

    grok.name('remove-transicao')
    grok.context(INavigationRoot)
    grok.require('cmf.ManagePortal')

    @log
    def render(self):
        session = Session()
        content = session.query(db.Transicao).get(self.request.id)
        fluxo_id = content.fluxo_id
        session.delete(content)
        session.flush()
        status = IStatusMessage(self.request)
        status.add(_(u'Registro removido.'), 'info')
        go('list-transicao', fluxo_id=fluxo_id)

class TransicaoListView(grok.View, BaseListView):

    grok.name('list-transicao')
    grok.context(INavigationRoot)
    grok.require('cmf.ManagePortal')
    
    dados = []
    dados_fluxo = {}
    view_sufix = 'transicao'

    @log
    def update(self):
        self.request.set('disable_border', True)
        self.dados = []
        api = getUtility(ISPDOAPI)
        fluxo = api.getFluxo()
        self.request.response.setCookie('fluxo_id', fluxo.id)
        self.dados_fluxo = {
            'nome':fluxo.nome,
            'url': url('show-fluxo', id=fluxo.id),
            }
        for i in fluxo.transicao:
            self.dados.append({
                'fluxo_id': i.fluxo_id,
                'inicial': i.inicial,
                'area_origem': i.area_origem.nome,
                'url-area-origem': url('show-area', id=i.area_origem_id),
                'area_destino': i.area_destino.nome,
                'url-area-destino': url('show-area', id=i.area_destino_id),
                'url-remove': url('remove-transicao', id=i.id),
                })

class PessoaOrigemRemoveView(grok.View):

    grok.name('remove-pessoaorigem')
    grok.context(INavigationRoot)
    grok.require('zope2.View')

    def update(self):
        sc = getUtility(ISecurityChecker)
        sc.enforce('acessar_remove_pessoaorigem')
        super(PessoaOrigemRemoveView, self).update()

    @log
    def render(self):
        session = Session()
        r = self.request
        content = session.query(db.PessoaOrigem).get((r.protocolo_id, r.pessoa_id))
        session.delete(content)
        session.flush()
        status = IStatusMessage(self.request)
        status.add(_(u'Registro removido.'), 'info')
        go('show-protocolo', id=r.protocolo_id)

class PessoaDestinoRemoveView(grok.View):

    grok.name('remove-pessoadestino')
    grok.context(INavigationRoot)
    grok.require('zope2.View')

    def update(self):
        sc = getUtility(ISecurityChecker)
        sc.enforce('acessar_remove_pessoadestino')
        super(PessoaDestinoRemoveView, self).update()

    @log
    def render(self):
        session = Session()
        r = self.request
        content = session.query(db.PessoaDestino).get((r.protocolo_id, r.pessoa_id))
        session.delete(content)
        session.flush()
        status = IStatusMessage(self.request)
        status.add(_(u'Registro removido.'), 'info')
        go('show-protocolo', id=r.protocolo_id)

class NotificacaoRemoveView(grok.View):

    grok.name('remove-notificacao')
    grok.context(INavigationRoot)
    grok.require('zope2.View')

    def update(self):
        sc = getUtility(ISecurityChecker)
        sc.enforce('acessar_remove_notificacao')
        super(NotificacaoRemoveView, self).update()

    @log
    def render(self):
        session = Session()
        api = getUtility(ISPDOAPI)
        pessoa_id = api.getAuthPessoa().id
        content = session.query(db.Notificacao).get((pessoa_id, self.request.protocolo_id))
        session.delete(content)
        session.flush()
        status = IStatusMessage(self.request)
        status.add(_(u'Registro removido.'), 'info')
        go('list-notificacao')

class NotificacaoListView(grok.View, BaseListView):

    grok.name('list-notificacao')
    grok.context(INavigationRoot)
    grok.require('zope2.View')
    
    dados = []
    dados_pessoa = {}
    view_sufix = 'notificacao'

    @log
    def update(self):
        sc = getUtility(ISecurityChecker)
        sc.enforce('acessar_list_notificacao')
        self.request.set('disable_border', True)
        self.dados = []
        self.dados_pessoa = {}
        api = getUtility(ISPDOAPI)
        pessoa = api.getAuthPessoa()
        self.dados_pessoa = {
            'pessoa_id': pessoa.id,
            'nome': pessoa.nome,
            'email': pessoa.email,
            'url': url('show-pessoa', id=pessoa.id)
            }
        for i in pessoa.notificacao:
            self.dados.append({
                'protocolo_id': i.protocolo.id,
                'numero': i.protocolo.numero,
                'data_protocolo': i.protocolo.data_protocolo,
                'assunto': i.protocolo.assunto,
                'tipodocumento': i.protocolo.tipodocumento.nome,
                'situacao': i.protocolo.situacao.nome,
                'url-remove': url('remove-notificacao', protocolo_id=i.protocolo.id),
                })

class ProtocoloShowView(grok.View):

    grok.name('show-protocolo')
    grok.context(INavigationRoot)
    grok.require('zope2.View')
    
    dados = {}

    @log
    def update(self):
        sc = getUtility(ISecurityChecker)
        sc.enforce('acessar_show_protocolo')
        self.request.set('disable_border', True)
        api = getUtility(ISPDOAPI)
        self._protocolo = api.getProtocolo(self.request.id)
        self.request.response.setCookie('protocolo_id', self._protocolo.id)
        self.dados = {
            'protocolo_id': self._protocolo.id,
            'tipoprotocolo': self._tipo_protocolo(),
            'tipodocumento': self._protocolo.tipodocumento.nome,
            'numero': self._protocolo.numero,
            'data_protocolo': self._protocolo.data_protocolo,
            'numero_documento': self._protocolo.numero_documento,
            'data_emissao': self._protocolo.data_emissao,
            'assunto': self._protocolo.assunto,
            'situacao': self._protocolo.situacao.nome,
            'referencias': self._referencias(),
            'referenciado_por': self._referenciado_por(),
            'apensado': self._apensado(),
            'apensos': self._apensos(),
            'origens': self._origens(),
            'destinos': self._destinos(),
            'observacoes': self._observacoes(),
            'anexos': self._anexos(),
            'tramites': self._tramites(),
            'menu': self._menu(),
        }

    def _tipo_protocolo(self):
        tpvf = getUtility(IVocabularyFactory, 'il.spdo.tipoprotocolo-vocab')
        tpv = tpvf(self.context)
        return tpv.getTerm(self._protocolo.tipoprotocolo).title

    def _referencias(self):
        ret = []
        sc = getUtility(ISecurityChecker)
        if not sc.check('acessar_list_referencia'):
            return ret
        for i in self._protocolo.protocolo:
            ret.append({
                'numero': i.referencia.numero,
                'url': url('show-protocolo', id=i.referencia_id),
                })
        return ret
    
    def _referenciado_por(self):
        ret = []
        sc = getUtility(ISecurityChecker)
        if not sc.check('acessar_list_referencia'):
            return ret
        for i in self._protocolo.referencia:
            ret.append({
                'numero': i.protocolo.numero,
                'url': url('show-protocolo', id=i.protocolo_id),
                })
        return ret

    def _apensado(self):
        i = self._protocolo.apensado
        if i is not None:
            return {
                'numero': i.numero,
                'url': url('show-protocolo', id=i.id)
                }

    def _apensos(self):
        ret = []
        for i in self._protocolo.apenso:
            ret.append({
                'numero': i.numero,
                'url': url('show-protocolo', id=i.id),
                })
        return ret
    
    def _origens(self):
        sc = getUtility(ISecurityChecker)
        show_pessoa = sc.check('acessar_show_pessoa')
        remove_pessoaorigem = sc.check('acessar_remove_pessoaorigem', protocolo_id=self._protocolo.id)
        ret = []
        for p in self._protocolo.pessoa_origem:
            i = p.pessoa
            url_pessoa = show_pessoa and url('show-pessoa', id=i.id) or None
            url_remove = remove_pessoaorigem and url('remove-pessoaorigem', protocolo_id=self._protocolo.id, pessoa_id=i.id) or None
            ret.append({
                'nome': i.nome,
                'email': i.email,
                'url': url_pessoa,
                'url-remove': url_remove,
                })
        return ret
    
    def _destinos(self):
        sc = getUtility(ISecurityChecker)
        show_pessoa = sc.check('acessar_show_pessoa')
        edit_pessoadestino = sc.check('acessar_edit_pessoadestino', protocolo_id=self._protocolo.id)
        remove_pessoadestino = sc.check('acessar_remove_pessoadestino', protocolo_id=self._protocolo.id)
        ret = []
        for p in self._protocolo.pessoa_destino:
            i = p.pessoa
            url_pessoa = show_pessoa and url('show-pessoa', id=i.id) or None
            url_edit = edit_pessoadestino and url('edit-pessoadestino', protocolo_id=self._protocolo.id, pessoa_id=i.id) or None
            url_remove = remove_pessoadestino and url('remove-pessoadestino', protocolo_id=self._protocolo.id, pessoa_id=i.id) or None
            ret.append({
                'nome': i.nome,
                'email': i.email,
                'tipoentrega': p.tipoentrega.nome if p.tipoentrega is not None else '',
                'data_entrega': p.data_entrega,
                'objeto_correios': p.objeto_correios,
                'url': url_pessoa,
                'url-edit': url_edit,
                'url-remove': url_remove,
                })
        return ret
    
    def _observacoes(self):
        ret = []
        sc = getUtility(ISecurityChecker)
        if not sc.check('visualizar_observacoes', protocolo_id=self._protocolo.id):
            return ret
        for i in self._protocolo.observacao:
            edit_observacao = sc.check('acessar_edit_observacao', protocolo_id=self._protocolo.id, observacao_id=i.id)
            url_edit = edit_observacao and url('edit-observacao', id=i.id) or None
            remove_observacao = sc.check('acessar_remove_observacao', protocolo_id=self._protocolo.id, observacao_id=i.id)
            url_remove = remove_observacao and url('remove-observacao', id=i.id) or None
            ret.append({
                'texto': i.texto,
                'data_observacao': i.data_observacao,
                'url-edit': url_edit,
                'url-remove': url_remove,
                })
        return ret
    
    def _anexos(self):
        ret = []
        sc = getUtility(ISecurityChecker)
        if not sc.check('visualizar_anexos', protocolo_id=self._protocolo.id):
            return ret
        for i in self._protocolo.anexo:
            remove_anexo = sc.check('acessar_remove_anexo', protocolo_id=self._protocolo.id, anexo_id=i.id)
            url_remove = remove_anexo and url('remove-anexo', id=i.id) or None
            ret.append({
                'arquivo': i.arquivo,
                'tamanho': i.tamanho,
                'data_anexo': i.data_anexo,
                'download_url': url('download-anexo', id=i.id),
                'url-remove': url_remove,
                })
        return ret
    
    def _tramites(self):
        sc = getUtility(ISecurityChecker)
        show_pessoa = sc.check('acessar_show_pessoa')
        visualizar_despachos = sc.check('visualizar_despachos', protocolo_id=self._protocolo.id)
        ret = []
        for i in self._protocolo.tramite:
            url_responsavel = show_pessoa and url('show-pessoa', id=i.responsavel.pessoa.id) or None
            despacho = visualizar_despachos and i.despacho or None
            ret.append({
                'data_disponibilizacao': i.data_disponibilizacao,
                'data_recebimento': i.data_recebimento,
                'area': i.area.sigla,
                'nome_responsavel': i.responsavel.pessoa.nome,
                'url-responsavel': url_responsavel,
                'despacho': despacho,
                })
        return ret

    def _menu(self):
        sc = getUtility(ISecurityChecker)
        protocolo_id = self._protocolo.id
        apenso_id = self._protocolo.apenso_id
        ret = []
        
        if sc.check('acessar_edit_protocolo', protocolo_id=protocolo_id):
            ret.append({'url': url('edit-protocolo', id=protocolo_id),
                        'titulo': _(u'Atualizar Protocolo'),
                        'id': 'overlay-edit-protocolo'})

        if sc.check('acessar_add_observacao', protocolo_id=protocolo_id):
            ret.append({'url': url('add-observacao', protocolo_id=protocolo_id),
                        'titulo': _(u'Adicionar Observação'),
                        'class': 'overlay-add-edit-observacao'})

        if sc.check('acessar_add_anexo', protocolo_id=protocolo_id):
            ret.append({'url': url('add-anexo', protocolo_id=protocolo_id),
                        'titulo': _(u'Adicionar Anexo')})

        if sc.check('acessar_list_referencia', protocolo_id=protocolo_id):
            ret.append({'url': url('list-referencia', protocolo_id=protocolo_id),
                        'titulo': _(u'Referências')})

        if sc.check('acessar_add_apenso', protocolo_id=protocolo_id, apenso_id=apenso_id):
            ret.append({'url': url('add-apenso', protocolo_id=protocolo_id),
                        'titulo': _(u'Apenso')})

        if sc.check('acessar_add_tramite', protocolo_id=protocolo_id):
            ret.append({'url': url('add-tramite', protocolo_id=protocolo_id),
                        'titulo': _(u'Tramitar')})

        return ret

class ProtocoloListView(grok.View, BaseListView):

    grok.name('list-protocolo')
    grok.context(INavigationRoot)
    grok.require('zope2.View')

    dados = []
    view_sufix = 'protocolo'

    @log
    def update(self):
        sc = getUtility(ISecurityChecker)
        sc.enforce('acessar_list_protocolo')
        self.request.set('disable_border', True)
        api = getUtility(ISPDOAPI)
        self.dados = api.getProtocolosCriadosRecebidos()

class AnexoRemoveView(grok.View):

    grok.name('remove-anexo')
    grok.context(INavigationRoot)
    grok.require('zope2.View')

    @log
    def render(self):
        session = Session()
        content = session.query(db.Anexo).get(self.request.id)
        protocolo_id = content.protocolo_id
        sc = getUtility(ISecurityChecker)
        sc.enforce('acessar_remove_anexo', protocolo_id=protocolo_id, anexo_id=self.request.id)
        session.delete(content)
        session.flush()
        status = IStatusMessage(self.request)
        status.add(_(u'Registro removido.'), 'info')
        go('show-protocolo', id=protocolo_id)
    
class AnexoDownloadView(grok.View):

    grok.name('download-anexo')
    grok.context(INavigationRoot)
    grok.require('zope2.View')

    def update(self):
        sc = getUtility(ISecurityChecker)
        sc.enforce('visualizar_anexos')
        super(AnexoDownloadView, self).update()

    @log
    def render(self):
        session = Session()
        anexo = session.query(db.Anexo).get(self.request.id)
        p = anexo.protocolo
        path_anexo = os.path.join(PATH_ANEXOS, ScopeID(), str(p.ano), str(p.id), str(anexo.id))
        file_anexo = NamedFile(open(path_anexo, 'r'), filename=anexo.arquivo)
        cd = 'inline; filename="%s"' % anexo.arquivo.encode('utf-8')
        self.request.response.setHeader('Content-Disposition', cd)
        set_headers(file_anexo, self.request.response)
        return stream_data(file_anexo)

class ObservacaoRemoveView(grok.View):

    grok.name('remove-observacao')
    grok.context(INavigationRoot)
    grok.require('zope2.View')

    @log
    def render(self):
        session = Session()
        content = session.query(db.Observacao).get(self.request.id)
        protocolo_id = content.protocolo_id
        sc = getUtility(ISecurityChecker)
        sc.enforce('acessar_remove_observacao', protocolo_id=protocolo_id, observacao_id=self.request.id)
        session.delete(content)
        session.flush()
        status = IStatusMessage(self.request)
        status.add(_(u'Registro removido.'), 'info')
        go('show-protocolo', id=protocolo_id)

class ReferenciaRemoveView(grok.View):

    grok.name('remove-referencia')
    grok.context(INavigationRoot)
    grok.require('zope2.View')

    def update(self):
        sc = getUtility(ISecurityChecker)
        sc.enforce('acessar_remove_referencia')
        super(ReferenciaRemoveView, self).update()

    @log
    def render(self):
        session = Session()
        r = self.request
        content = session.query(db.Referencia).get((r.protocolo_id, r.referencia_id))
        session.delete(content)
        session.flush()
        status = IStatusMessage(self.request)
        status.add(_(u'Registro removido.'), 'info')
        go('list-referencia', protocolo_id=r.protocolo_id)

class ReferenciaListView(grok.View, BaseListView):

    grok.name('list-referencia')
    grok.context(INavigationRoot)
    grok.require('zope2.View')
    
    dados = []
    dados_protocolo = {}
    view_sufix = 'referencia'

    @log
    def update(self):
        sc = getUtility(ISecurityChecker)
        sc.enforce('acessar_list_referencia')
        self.request.set('disable_border', True)
        self.dados = []
        self.dados_protocolo = {}
        api = getUtility(ISPDOAPI)
        protocolo = api.getProtocolo()
        self.dados_protocolo = {
            'protocolo_id': protocolo.id,
            'numero': protocolo.numero,
            'data_protocolo': protocolo.data_protocolo,
            'assunto': protocolo.assunto,
            'tipodocumento': protocolo.tipodocumento.nome,
            'situacao': protocolo.situacao.nome,
            'url': url('show-protocolo', id=protocolo.id)
            }
        for i in protocolo.protocolo:
            self.dados.append({
                'protocolo_id': i.protocolo_id,
                'referencia_id': i.referencia_id,
                'numero': i.referencia.numero,
                'data_protocolo': i.referencia.data_protocolo,
                'assunto': i.referencia.assunto,
                'tipodocumento': i.referencia.tipodocumento.nome,
                'situacao': i.referencia.situacao.nome,
                'url-remove': url('remove-referencia', protocolo_id=i.protocolo_id, referencia_id=i.referencia_id),
                })

class EtiquetasDownloadView(grok.View):

    grok.name('download-etiquetas')
    grok.context(INavigationRoot)
    grok.require('zope2.View')

    def update(self):
        sc = getUtility(ISecurityChecker)
        sc.enforce('acessar_print_etiquetas')
        super(EtiquetasDownloadView, self).update()

    @log
    def render(self):
        file_etiquetas = NamedFile(open('/tmp/%s.pdf' % self.request.SESSION.id, 'r'), filename=u'etiquetas.pdf')
        cd = 'inline; filename="etiquetas.pdf"'
        self.request.response.setHeader('Content-Disposition', cd)
        set_headers(file_etiquetas, self.request.response)
        return stream_data(file_etiquetas)

class ProtocoloAddWSView(grok.View):

    grok.name('ws-add-protocolo')
    grok.context(INavigationRoot)
    grok.require('zope2.View')

    def update(self):
        sc = getUtility(ISecurityChecker)
        sc.enforce('acessar_ws_add_protocolo')
        super(ProtocoloAddWSView, self).update()

    def _json_error(self, error_code):
        ERROS = {
            1: _(u'Parâmetro dados não informado.'),
            2: _(u'Estrutura de dados inválida.'),
            3: _(u'Esse tipo de protocolo e/ou tipo de documento não pode ser protocolado pela sua área.'),
        }
        return json.dumps(ERROS[error_code])

    def _tipodocumento(self, nome):
        session = Session()
        return session.query(db.TipoDocumento).filter_by(nome=nome).first()
    
    def _valida_dados(self, dados):
        """
        Valida o parâmetro 'dados', que deve ser uma estrutura como a demonstrada a seguir:

        import json
        dados = {'origens': [{'email': 'email@origem.net', 'nome': 'Nome da Pessoa de Origem'}],
                 'destinos': [{'email': 'email@destino.net', 'nome': 'Nome da Pessoa de Destino'}],
                 'assunto': 'Assunto...',
                 'observacao': '',
                 'numero_documento': '12345',
                 'data_emissao': '2011-11-23',
                 'situacao': 'Tramitando',
                 'tipodocumento': 'Carta',
                 'tipoprotocolo': 'E'}
        print json.dumps(dados)
        """
        
        # dados precisa ser um dicionário
        if type(dados) != type({}):
            return False

        # dados deve conter todas as chaves
        for k in ('origens', 'destinos', 'assunto', 'observacao', 'numero_documento', 
                  'data_emissao', 'situacao', 'tipodocumento', 'tipoprotocolo'):
            if dados.get(k, None) is None:
                return False
        
        # origens (e destinos) devem ser listas de dicionários não vazias
        for f in ('origens', 'destinos'):
            origens = dados.get(f)
            if type(origens) != type([]) or len(origens) < 1:
                return False
            for p in origens:
                if type(p) != type({}):
                    return False
                for k in ('email', 'nome'):
                    if p.get(k, None) is None:
                        return False
                    
        # demais campos devem ser strings unicode
        for k in ('assunto', 'observacao', 'numero_documento', 'data_emissao', 
                  'situacao', 'tipodocumento', 'tipoprotocolo'):
            if type(dados.get(k)) != type(u''):
                return False

        # assunto é obrigatório
        if not dados.get('assunto', None):
            return False

        # tipo de protocolo deve ser 'R', 'E' ou 'I'
        if dados.get('tipoprotocolo') not in ('R', 'E', 'I'):
            return False

        # a data de emissão, quando não for uma string vazia, deve ser
	# uma data válida, representada como AAAA-MM-DD e que não seja 
        # maior do que a data atual
        dt = dados.get('data_emissao')
        if dt:
            if len(dt) != 10:
                return False
            try:
                aaaa, mm, dd = dt.split('-')
                aaaa = int(aaaa)
                mm = int(mm)
                dd = int(dd)
                d1 = datetime.date(aaaa, mm, dd)
                d2 = datetime.date.today()
                if d1 > d2:
                    return False
            except ValueError, IndexError:
                return False

        # os valores de “situacao” e “tipodocumento” devem estar cadastrados
        session = Session()
        if not session.query(db.Situacao).filter_by(nome=dados.get('situacao')).filter_by(inicial=True).first():
            return False
        if not self._tipodocumento(dados.get('tipodocumento')):
            return False

        return True
    
    def _addProtocolo(self, dados, anexos=[]):

        session = Session()
        api = getUtility(ISPDOAPI)

        # origens (e destinos)
        pessoas_origens = []
        pessoas_destinos = []
        for f in ('origens', 'destinos'):
            for origem in dados[f]:
                pessoa = session.query(db.Pessoa).filter_by(email=origem['email']).first()
                if not pessoa:
                    pessoa = db.Pessoa(origem['nome'], origem['email'])
                    session.add(pessoa)
                    session.flush()
                if f == 'origens':
                    pessoas_origens.append(pessoa.id)
                else:
                    pessoas_destinos.append(pessoa.id)

        # "situacao" e "tipodocumento"
        situacao = session.query(db.Situacao).filter_by(nome=dados.get('situacao')).filter_by(inicial=True).first()
        tipodocumento = self._tipodocumento(dados.get('tipodocumento'))

        # data de emissão
        dt = dados.get('data_emissao')
        if dt:
            aaaa, mm, dd = dt.split('-')
            aaaa = int(aaaa)
            mm = int(mm)
            dd = int(dd)
            dt = datetime.date(aaaa, mm, dd)
        else:
            dt = None

        # cria protocolo, observacao, anexos e tramite inicial, utilizando a API

        # IMPORTANTE: Por definição, exceto na criação dos protocolos,
        # os anexos e as observações são sempre adicionadas ANTES da
        # tramitação ocorrer.

        protocolo_id = api.addProtocolo(dados['tipoprotocolo'], tipodocumento.id, dados['numero_documento'], dt, 
                                        dados['assunto'], situacao.id, pessoas_origens, pessoas_destinos)

        api.TramiteInicial(protocolo_id)

        if dados['observacao'].strip():
            api.addObservacao(protocolo_id, dados['observacao'])
            
        if anexos:
            api.addAnexos(protocolo_id, anexos)

        protocolo = api.getProtocolo(protocolo_id)        
        return protocolo.numero, protocolo.data_protocolo

    @log
    def render(self):
        r = self.request

        dados = r.get('dados', '')
        if not dados:
            return self._json_error(1)

        dados = json.loads(dados)
        if not self._valida_dados(dados):
            return self._json_error(2)

        sc = getUtility(ISecurityChecker)
        if not sc.check('fluxo_rigoroso_area_inicial', tipoprotocolo=dados['tipoprotocolo'],
                        tipodocumento_id=self._tipodocumento(dados['tipodocumento']).id):
            return self._json_error(3)

        anexos = [NamedFile(r.form[a], filename=unicode(r.form[a].filename, 'utf-8')) \
                  for a in r.form.keys() if a.startswith('anexo')]
        numero, data_protocolo = self._addProtocolo(dados, anexos)
        return json.dumps(_('Protocolo: %s de %s' % (numero, str(data_protocolo))))

class SecurityCheckerView(BrowserView):
    """View de verificação de segurança, destinada a omitir nas
    portlets as opções que os usuários não podem acessar.
    """

    implements(ISecurityChecker)

    def check(self, acao, **kwargs):
        sc = getUtility(ISecurityChecker)
        return sc.check(acao, **kwargs)

    def enforce(self, acao, **kwargs):
        sc = getUtility(ISecurityChecker)
        return sc.enforce(acao, **kwargs)
