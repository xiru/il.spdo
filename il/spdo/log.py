import logging

from zope.globalrequest import getRequest

from il.spdo.db import Log
from il.spdo.config import Session

def log(fn):
    def f(*args, **kwargs):
        ret = fn(*args, **kwargs)
        l = Log()
        request = getRequest()
        l.usuario = str(request.other.get('AUTHENTICATED_USER', 'Anonymous'))
        l.url = request.other.get('ACTUAL_URL')
        l.modulo = fn.__module__
        l.classe = args[0].__class__.__name__
        l.funcao = fn.__name__
        l.args = repr(list(args)[1:])
        l.kwargs = repr(kwargs)
        session = Session()
        session.add(l)
        return ret
    return f

def logger(msg):
    logger = logging.getLogger('SPDO')
    logger.warning(msg)
