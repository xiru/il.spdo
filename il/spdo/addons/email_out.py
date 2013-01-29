# -*- coding: utf-8 -*-

import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.Utils import COMMASPACE
from email.MIMEText import MIMEText
from email.MIMEBase import MIMEBase
from email import Encoders
import os
import json
import sys

from config import SMTP, SPDO_MAILBOX

def enviaEmail(remetente, destinatarios, assunto, dados, anexos=[]):
    assert type(destinatarios)==type([])

    msg = MIMEMultipart()
    msg['From'] = remetente
    msg['To'] = COMMASPACE.join(destinatarios)
    msg['Subject'] = assunto
    msg.attach(MIMEText(dados))

    for anexo in anexos:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(anexo.read())
        Encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(anexo.name))
        msg.attach(part)

    if SMTP['PORT'] == 465:
        server = smtplib.SMTP_SSL(SMTP['SERVER'], SMTP['PORT'])
    else:
        server = smtplib.SMTP(SMTP['SERVER'], SMTP['PORT'])
        if SMTP.get('TLS', None):
            server.starttls()
    if SMTP['USER'] and SMTP['PASS']:
        server.login(SMTP['USER'], SMTP['PASS'])
    server.sendmail(remetente, destinatarios, msg.as_string())
    server.close()

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
    enviaEmail(SPDO_MAILBOX, [SPDO_MAILBOX], '[SPDO] Novo Protocolo', dados, anexos)
