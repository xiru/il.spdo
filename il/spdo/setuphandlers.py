from StringIO import StringIO

from Products.PlonePAS.Extensions.Install import activatePluginInterfaces
from Products.CMFCore.utils import getToolByName

from il.spdo.pas import SPDOPASPlugin


def installPASPlugin(portal, name='spdo_plugin'):
    out=StringIO()
    acl = portal['acl_users']
    if name not in acl:
        plugin = SPDOPASPlugin(name, title="SPDO PAS Plugin")
        acl[name] = plugin
        activatePluginInterfaces(portal, name, out)
        plugins = acl['plugins']
        for info in plugins.listPluginTypeInfo():
            interface = info['interface']
            if plugin.testImplements(interface):
                active = list(plugins.listPluginIds(interface))
                if name in active:
                    active.remove(name)
                    active.insert(0, name)
                    plugins._plugins[interface] = tuple(active)
        return out.getvalue()


def setupVarious(context):
    if context.readDataFile('il.spdo_various.txt') is None:
        return
    portal = context.getSite()
    installPASPlugin(portal)
    for obj in portal.objectIds():
        if obj in ['news', 'events', 'Members']:
            portal.manage_delObjects([obj,])
    wft = getToolByName(portal, 'portal_workflow')
    obj = getattr(portal, 'front-page')
    wft.doActionFor(obj, action='publish')
