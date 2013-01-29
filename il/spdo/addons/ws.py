# -*- coding: utf-8 -*-

"""
Para acessar uma URL com autenticação no Plone, utilizando o urllib2,
é necessário seguir o seguinte procedimento: Primeiramente, deve-se
acessar por POST a URL /login_form, passando nos parâmetros __ac_name
e __ac_password o usuário e senha, respectivamente. No response dessa
requisição deve-se capturar o valor do header Set-Cookie. Nos requests
posteriores esse valor deve ser passado no header Cookie.

Recomenda-se o uso de criptografia HTTPS para evitar que um sniffer de
rede capture essa informação. 
"""

import urllib
import urllib2
import json
import MultipartPostHandler
import sys

from config import REST

def _getAuthCookie(url, usuario, senha):
    values = {'__ac_name': usuario,
              '__ac_password': senha,
              'form.submitted': '1'}
    data = urllib.urlencode(values)
    req = urllib2.Request(url, data)
    resp = urllib2.urlopen(req)
    cookie = resp.headers['Set-Cookie']
    return cookie

def callWS(url, usuario, senha, dados, anexos = []):
    url_login = url.split('@@ws-')[0] + 'login_form'
    auth_cookie = _getAuthCookie(url_login, usuario, senha)
    opener = urllib2.build_opener(MultipartPostHandler.MultipartPostHandler)
    opener.addheaders = [('Cookie', auth_cookie)]
    params = {"dados": dados}
    cont = 1
    for anexo in anexos:
        params['anexo%d' % cont] = anexo
        cont += 1
    return opener.open(url, params).read()

if __name__ == "__main__":
    dados = {'origens': [{'email': 'email@origem.net', 'nome': 'Nome da Pessoa de Origem'}],
             'destinos': [{'email': 'email@destino.net', 'nome': 'Nome da Pessoa de Destino'}],
             'assunto': 'Assunto...',
             'observacao': '',
             'numero_documento': '12345',
             'data_emissao': '2011-11-23',
             'situacao': 'Tramitando',
             'tipodocumento': 'Carta',
             'tipoprotocolo': 'E'}
    dados = json.dumps(dados)
    anexos = sys.argv[1:]
    if not anexos:
        anexos = ['teste1.txt', 'teste2.txt']
    anexos = [open(a, 'rb') for a in anexos]
    ret = callWS(REST['URL'], REST['USER'], REST['PASS'], dados, anexos)
    print json.loads(ret)
