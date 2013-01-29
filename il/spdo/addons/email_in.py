# -*- coding: utf-8 -*-

import imaplib
import email
import mimetypes
import tempfile
import os
import shutil

from config import IMAP, REST, SPDO_MAILBOX
from ws import callWS
from email_out import enviaEmail

def _parse(msg):
    dados = None
    anexos = []
    temp_dir = tempfile.mkdtemp()
    cont = 1
    for p in msg.walk():
        if p.is_multipart():
            continue
        if p.get_content_maintype() == 'text':
            dados = p.get_payload(decode=True).strip()
        else:
            att_name = p.get_filename(None)
            if not att_name:
                ext = mimetypes.guess_extension(p.get_content_type())
                ext = ext is not None and ext or ''
                att_name = 'anexo-%d%s' % (cont, ext)
                cont += 1
            pl = p.get_payload(decode=True)       
            temp_file = os.path.join(temp_dir, att_name)
            open(temp_file, 'wb').write(pl)
            anexos.append(open(temp_file, 'rb'))
    return dados, anexos

if __name__ == '__main__':

    print "Conectando em %s:%d" % (IMAP['SERVER'], IMAP['PORT'])
    c = imaplib.IMAP4_SSL(IMAP['SERVER'], IMAP['PORT'])

    print "Login: %s" % IMAP['USER']
    c.login(IMAP['USER'], IMAP['PASS'])

    try:
        typ, data = c.select(IMAP['MAILBOX'])
        typ, [msg_ids] = c.search(None, '(SUBJECT "[SPDO]")')
        for msg_id in msg_ids.split():

            typ, msg_data = c.fetch(msg_id, '(RFC822)')
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_string(response_part[1])
                    dados, anexos = _parse(msg)

                    try:
                        print ".",
                        ret = callWS(REST['URL'], REST['USER'], REST['PASS'], dados, anexos)
                    except:
                        raise
                    else:
                        enviaEmail(SPDO_MAILBOX, [SPDO_MAILBOX], ret, dados)
                        typ, resp = c.store(msg_id, '+FLAGS', r'(\Deleted)')
                    finally:
                        if anexos:
                            temp_dir = os.path.dirname(anexos[0].name)
                            shutil.rmtree(temp_dir)

        if msg_ids:
            typ, resp = c.expunge()

    finally:
        try:
            c.close()
        except:
            pass
        c.logout()
