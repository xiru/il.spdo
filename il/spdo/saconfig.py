# -*- coding: utf-8 -*-

from zope.component import provideUtility
from zope.component.interfaces import ComponentLookupError
from zope.app.component.hooks import getSite
from z3c.saconfig import EngineFactory, GloballyScopedSession, SiteScopedSession
from z3c.saconfig.interfaces import IEngineFactory, IScopedSession
from collective.saconnect.interfaces import ISQLAlchemyConnectionStrings
from Products.CMFCore.utils import getToolByName

from il.spdo.config import DEFAULT_DSN
from il.spdo.log import logger
from il.spdo.history_meta import ZopeVersionedExtension


class SPDOEngineFactory(EngineFactory):

    def configuration(self):
        urltool = getToolByName(getSite(), 'portal_url')
        portal = urltool.getPortalObject()
        try:
            saconnect = ISQLAlchemyConnectionStrings(portal)
            dsn = saconnect['spdo']
            logger(u"Utilizando configuração local: " + unicode(dsn, 'utf-8'))
        except (ComponentLookupError, KeyError), e:
            dsn = DEFAULT_DSN
            logger(u"Utilizando configuração padrão: " + unicode(dsn, 'utf-8'))
        return (dsn,),{}

SPDOEngineGlobalUtility = EngineFactory(DEFAULT_DSN)
provideUtility(SPDOEngineGlobalUtility, provides=IEngineFactory, name=u'spdo_engine')

## GloballyScopedSession - um banco de dados por instancia
#SPDOGloballyScopedSession = GloballyScopedSession(u'spdo_engine', extension=ZopeVersionedExtension())
#provideUtility(SPDOGloballyScopedSession, provides=IScopedSession, name=u'spdo_session')


def ScopeID():
    urltool = getToolByName(getSite(), 'portal_url')
    obj = urltool.getPortalObject()
    return '-'.join(obj.getPhysicalPath()[1:])


# SiteScopedSession - um banco de dados por site
class SPDOSiteScopedSession(SiteScopedSession):
    def siteScopeFunc(self):
        return ScopeID()
provideUtility(SPDOSiteScopedSession(u'spdo_engine', extension=ZopeVersionedExtension()), provides=IScopedSession, name=u'spdo_session')
