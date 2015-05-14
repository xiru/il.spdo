# -*- coding: utf-8 -*-

import json
import datetime
import sqlalchemy as rdb
from sqlalchemy.orm import aliased

from five import grok
from zope.component import getUtility, getMultiAdapter

from plone.app.layout.navigation.interfaces import INavigationRoot
from plone.namedfile.file import NamedFile

from il.spdo.config import Session, SEARCH_LIMIT
from il.spdo import db
from il.spdo.config import MessageFactory as _
from il.spdo.log import log
from il.spdo.interfaces import ISPDOAPI, ISecurityChecker
from il.spdo.nav import url
from il.spdo.browser.views import ProtocoloShowView


class ProtocoloShowWSView(grok.View):

    grok.name('ws-show-protocolo')
    grok.context(INavigationRoot)
    grok.require('zope2.View')

    def update(self):
        self.api = getUtility(ISPDOAPI)
        self.protocolo_view = getMultiAdapter((self.context, self.request), name=u'show-protocolo')

    def _json_error(self, error_code):
        ERROS = {
            1: _(u'Parâmetro dados não informado.'),
            2: _(u'Estrutura de dados inválida.'),
        }
        return json.dumps(ERROS[error_code])

    def _valida_dados(self, dados):
        """
        Valida o parâmetro 'dados', que deve ser uma estrutura como a demonstrada a seguir:

        import json
        dados = {'protocolo': 'E-00000023/2015-97'}
        print json.dumps(dados)
        """

        # dados precisa ser um dicionário
        if not isinstance(dados, dict):
            return False

        # dados deve conter o protocolo
        for k in ('protocolo',):
            if dados.get(k, None) is None:
                return False

        # os valores de “protocolo” deve ser valido
        if not self._protocolo(dados.get('protocolo')):
            return False

        return True

    def _protocolo(self, numero):
        session = Session()
        return session.query(db.Protocolo).filter_by(numero=numero).first()

    def _busca_protocolo(self, dados):
        protocolo = self.api.getProtocolo(self._protocolo(dados['protocolo']).id)
        self.protocolo_view._protocolo = protocolo
        tramites = self.protocolo_view._tramites()
        ntramites = []
        for i in tramites:
            if i['data_recebimento']:
                i['data_recebimento'] = i['data_recebimento'].strftime('%d/%m%/%Y')
            if i['data_disponibilizacao']:
                i['data_disponibilizacao'] = i['data_disponibilizacao'].strftime('%d/%m%/%Y')
            ntramites.append(i)

        dados_prot = {
            'protocolo_id': protocolo.id,
            'tipoprotocolo': self.protocolo_view._tipo_protocolo(),
            'tipodocumento': protocolo.tipodocumento.nome,
            'numero': protocolo.numero,
            'data_protocolo': protocolo.data_protocolo.strftime('%d/%m%/%Y'),
            'numero_documento': protocolo.numero_documento,
            'data_emissao': protocolo.data_emissao.strftime('%d/%m%/%Y'),
            'assunto': protocolo.assunto,
            'situacao': protocolo.situacao.nome,
            'referencias': self.protocolo_view._referencias(),
            'referenciado_por': self.protocolo_view._referenciado_por(),
            'apensado': self.protocolo_view._apensado(),
            'apensos': self.protocolo_view._apensos(),
            'origens': self.protocolo_view._origens(),
            'destinos': self.protocolo_view._destinos(),
            'observacoes': self.protocolo_view._observacoes(),
            'anexos': self.protocolo_view._anexos(),
            'tramites': ntramites,
        }

        return dados_prot

    @log
    def render(self):
        r = self.request

        dados = r.get('dados', '')
        if not dados:
            return self._json_error(1)

        dados = json.loads(dados)
        if not self._valida_dados(dados):
            return self._json_error(2)

        resultado = self._busca_protocolo(dados)
        return json.dumps(resultado)


class TramiteAddWSView(grok.View):

    grok.name('ws-tramite')
    grok.context(INavigationRoot)
    grok.require('zope2.View')

    def update(self):
        self.api = getUtility(ISPDOAPI)

    def _json_error(self, error_code):
        ERROS = {
            1: _(u'Parâmetro dados não informado.'),
            2: _(u'Estrutura de dados inválida.'),
        }
        return json.dumps(ERROS[error_code])

    def _valida_dados(self, dados):
        """
        Valida o parâmetro 'dados', que deve ser uma estrutura como a demonstrada a seguir:

        import json
        dados = {'area': 'Nome da Pessoa de Destino',
                 'despacho': 'Tramitação...',
                 'protocolo': 'E-00000023/2015-97'}
        print json.dumps(dados)
        """

        # dados precisa ser um dicionário
        if not isinstance(dados, dict):
            return False

        # dados deve conter todas as chaves
        for k in ('area', 'despacho', 'protocolo'):
            if dados.get(k, None) is None:
                return False

        # valida o destino e o protoclo
        if dados.get('area', None):
            if not self._area(dados.get('area')):
                return False
        if dados.get('protocolo', None):
            if not self._protocolo(dados.get('protocolo')):
                return False

        return True

    def _area(self, nome):
        session = Session()
        return session.query(db.Area).filter_by(nome=nome).first()

    def _protocolo(self, numero):
        session = Session()
        return session.query(db.Protocolo).filter_by(numero=numero).first()

    def _tramite(self, dados, apenso=False):
        protocolo_id = self._protocolo(dados['protocolo']).id
        area_id = self._area(dados['area']).id
        session = Session()
        area_id_auth = self.api.getAuthPessoa().area_id
        copia = len([area_id]) > 1
        ret = []
        ret.append(protocolo_id)
        protocolo = self.api.getProtocolo(protocolo_id)
        tramite = db.Tramite(
            protocolo_id=protocolo_id,
            area_id=area_id,
            data_disponibilizacao=datetime.datetime.now(),
            data_recebimento=None,
            despacho=dados['despacho'],
            usuario=self.api.getAuthId(),
            copia=copia,
            area_id_anterior=area_id_auth,
        )
        session.add(tramite)
        self.api._add_box(db.TramiteOutbox, protocolo_id, area_id_auth)
        self.api._del_box(db.TramiteInbox, protocolo_id, area_id_auth)
        session.flush()
        # propaga tramitação nos apensos
        for apenso in protocolo.apenso:
            ret.extend(self._tramite([apenso.id], area_id, dados['despacho'], apenso=True))
        return ret

    @log
    def render(self):
        r = self.request

        dados = r.get('dados', '')
        if not dados:
            return self._json_error(1)

        dados = json.loads(dados)
        if not self._valida_dados(dados):
            return self._json_error(2)

        resultado = self._tramite(dados)
        return json.dumps(resultado)


class ProtocoloSearchWSView(grok.View):

    grok.name('ws-search-protocolo')
    grok.context(INavigationRoot)
    grok.require('zope2.View')

    @log
    def update(self):
        self.api = getUtility(ISPDOAPI)

    def _json_error(self, error_code):
        ERROS = {
            1: _(u'Parâmetro dados não informado.'),
            2: _(u'Estrutura de dados inválida.'),
        }
        return json.dumps(ERROS[error_code])

    def _valida_dados(self, dados):
        """
        Valida o parâmetro 'dados', que deve ser uma estrutura como a demonstrada a seguir:

        import json
        dados = {'origem': 'Nome da Pessoa de Origem',
                 'destino': 'Nome da Pessoa de Destino',
                 'assunto': 'Assunto...',
                 'situacao': 'Tramitando',
                 'tipodocumento': 'Carta',
                 'tipoprotocolo': 'E',
                 'inativo': '4',
                 'area': 'Comissão'}
        print json.dumps(dados)
        """

        # dados precisa ser um dicionário
        if not isinstance(dados, dict):
            return False

        # os valores de “situacao”, “tipodocumento” e ”area” devem estar cadastrados
        if dados.get('situacao', None):
            session = Session()
            if not session.query(db.Situacao).filter_by(nome=dados.get('situacao')).filter_by(inicial=True).first():
                return False
        if dados.get('tipodocumento', None):
            if not self._tipodocumento(dados.get('tipodocumento')):
                return False
        if dados.get('area', None):
            if not self._area(dados.get('area')):
                return False

        return True

    def _area(self, nome):
        session = Session()
        return session.query(db.Area).filter_by(nome=nome).first()

    def _tipodocumento(self, nome):
        session = Session()
        return session.query(db.TipoDocumento).filter_by(nome=nome).first()

    def _consulta_protocolos(self, dados):
        session = Session()
        items = session.query(db.Protocolo)

        tipoprotocolo = dados.get('tipoprotocolo', None)
        if tipoprotocolo is not None:
            items = items.filter_by(tipoprotocolo=tipoprotocolo)

        tipodocumento = dados.get('tipodocumento', None)
        if tipodocumento is not None:
            tipodocumento_id = session.query(db.TipoDocumento).filter_by(nome=tipodocumento).first().id
            items = items.filter_by(tipodocumento_id=tipodocumento_id)

        situacao = dados.get('situacao', None)
        if situacao is not None:
            situacao_id = session.query(db.Situacao).filter_by(nome=situacao).first().id
            items = items.filter_by(situacao_id=situacao_id)

        origem = dados.get('origem', None)
        if origem is not None:
            pessoa1 = aliased(db.Pessoa)
            items = items.join(db.PessoaOrigem).join(pessoa1)
            clause = rdb.or_(pessoa1.nome.contains(origem),
                             pessoa1.nome.ilike(origem))
            items = items.filter(clause)

        destino = dados.get('destino', None)
        if destino is not None:
            pessoa2 = aliased(db.Pessoa)
            items = items.join(db.PessoaDestino).join(pessoa2)
            clause = rdb.or_(pessoa2.nome.contains(destino),
                             pessoa2.nome.ilike(destino))
            items = items.filter(clause)

        assunto = dados.get('assunto', None)
        if assunto is not None:
            clause = rdb.or_(db.Protocolo.assunto.contains(assunto),
                             db.Protocolo.assunto.ilike(assunto))
            items = items.filter(clause)

        area = dados.get('area', None)
        if area is not None:
            area_tb = aliased(db.Area)
            area_id = area_tb.id
            inbox1 = aliased(db.TramiteInbox)
            items = items.join(inbox1).filter_by(area_id=area_id)

        tempo_inativo = dados.get('inativo', None)
        if tempo_inativo is not None:
            tempo_inativo = int(tempo_inativo)
            d = datetime.datetime.now() - datetime.timedelta(days=tempo_inativo)
            inbox2 = aliased(db.TramiteInbox)
            items = items.join(inbox2).filter(inbox2.version_date < d)

        ret = []
        resultado = items.limit(SEARCH_LIMIT).all()
        for i in resultado:
            ret.append({
               'id': i.id,
               'numero': i.numero,
               'data_protocolo': i.data_protocolo.strftime('%d/%m/%Y'),
               'assunto': i.assunto,
               'tipodocumento': i.tipodocumento.nome,
               'situacao': i.situacao.nome,
               'url': url('show-protocolo', id=i.id),
               })
        return ret

    @log
    def render(self):
        r = self.request

        dados = r.get('dados', '')
        if not dados:
            return self._json_error(1)

        dados = json.loads(dados)
        if not self._valida_dados(dados):
            return self._json_error(2)

        resultado = self._consulta_protocolos(dados)
        return json.dumps(resultado)


class ApensoAddWSView(grok.View):

    grok.name('ws-add-apenso')
    grok.context(INavigationRoot)
    grok.require('zope2.View')

    def update(self):
        sc = getUtility(ISecurityChecker)
        sc.enforce('acessar_ws_add_apenso')
        super(ApensoAddWSView, self).update()

    def _json_error(self, error_code):
        ERROS = {
            1: _(u'Parâmetro dados não informado.'),
            2: _(u'Estrutura de dados inválida.'),
        }
        return json.dumps(ERROS[error_code])

    def _valida_dados(self, dados):
        """
        Valida o parâmetro 'dados', que deve ser uma estrutura como a demonstrada a seguir:
        add: 1 para incluir e 0 para excluir
        import json
        dados = {protocolo: 'E-00000002/2015-93'
                 'apensos': ['I-00000003/2015-98','I-00000007/2015-18'],
                 'add': '1'}
        print json.dumps(dados)
        """
        # dados precisa ser um dicionário
        if not isinstance(dados, dict):
            return False

        # dados deve conter todas as chaves
        for k in ('protocolo', 'apensos', 'add'):
            if dados.get(k, None) is None:
                return False
        return True

    @log
    def _create_and_add(self, dados):
        session = Session()
        protocolo = session.query(db.Protocolo).filter_by(numero=dados['protocolo']).first()
        for numero in dados['apensos']:
            apenso = session.query(db.Protocolo).filter_by(numero=numero).first()
            protocolo.apenso_id = apenso.id

    @log
    def render(self):
        r = self.request

        dados = r.get('dados', '')
        if not dados:
            return self._json_error(1)

        dados = json.loads(dados)
        if not self._valida_dados(dados):
            return self._json_error(2)

        resultado = self._create_and_add(dados)
        return json.dumps(resultado)


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
        if not isinstance(dados, dict):
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


class AreaListWSView(grok.View):

    grok.name('ws-list-area')
    grok.context(INavigationRoot)
    grok.require('zope2.View')

    @log
    def render(self):

        self.dados = []
        session = Session()
        items = session.query(db.Area).all()
        for i in items:
            self.dados.append({
                'id': i.id,
                'sigla': i.sigla,
                'nome': i.nome,
                'chefia_id': i.chefia_id,
                'chefia_sigla': getattr(i.area, ' sigla', ''),
                'chefia_nome': getattr(i.area, 'nome', ''),
                })

        return json.dumps(self.dados)


class TipoDocumentoListWSView(grok.View):

    grok.name('ws-list-tipodocumento')
    grok.context(INavigationRoot)
    grok.require('zope2.View')

    dados = []
    view_sufix = 'tipodocumento'

    @log
    def render(self):
        self.dados = []
        session = Session()
        items = session.query(db.TipoDocumento).all()
        for i in items:
            self.dados.append({
                'id': i.id,
                'nome': i.nome,
                })

        return json.dumps(self.dados)


class SituacaoListWSView(grok.View):

    grok.name('ws-list-situacao')
    grok.context(INavigationRoot)
    grok.require('zope2.View')

    dados = []
    view_sufix = 'situacao'

    @log
    def render(self):
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

        return json.dumps(self.dados)


class PessoasListWSView(grok.View):

    grok.name('ws-list-pessoas')
    grok.context(INavigationRoot)
    grok.require('zope2.View')

    dados = []

    @log
    def render(self):
        self.dados = []
        session = Session()
        items = session.query(db.Pessoa).order_by(db.Pessoa.nome).all()
        for i in items:
            self.dados.append({
                'email': i.email,
                'nome': i.nome
            })

        return json.dumps(self.dados)
