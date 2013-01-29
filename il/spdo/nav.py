from zope.app.component.hooks import getSite
from Products.CMFCore.utils import getToolByName
from zope.globalrequest import getRequest

def url(viewname, **kw):
    site = getSite()
    urltool = getToolByName(site, 'portal_url')
    urlbase = urltool.getPortalObject().absolute_url()
    url = urlbase + '/@@' + viewname
    if kw:
        params = "&".join(["%s=%s" % (k, str(v)) for k, v in kw.items()])
        url += "?" + params
    return url

def go(viewname, **kw):
    request = getRequest()
    u = url(viewname, **kw)
    request.response.redirect(u)
