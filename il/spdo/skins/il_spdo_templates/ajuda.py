## Script (Python) "ajuda"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=
##title=
##
def crud(x):
  return ['/@@list-'+x,'/@@show-'+x,'/@@add-'+x,'/@@edit-'+x]

r = context.REQUEST

parametrizacao = (crud('area') + crud('pessoa') + crud('responsavel') + crud('fluxo') + crud('transicao') + 
                  crud('tipodocumento') + crud('situacao') + crud('tipoentrega'), '/manual_online_parametrizacao')
protocolo = (crud('protocolo'), '/manual_online_protocolo')
tramitacao = (['/@@envio-tramite', '/@@recebimento-tramite', '/@@recuperacao-tramite'], '/manual_online_tramitacao')
etiquetas = (['@@print-etiquetas', '/@@search-protocolo-barra', '/@@recebimento-tramite-barra'], '/manual_online_etiquetas')
pesquisa = (['/@@search-protocolo'], '/manual_online_pesquisa')
referencias_apensos = (crud('referencia') + crud('apenso'), '/manual_online_referencias_apensos')

portal = context.portal_url.getPortalObject()
raiz = portal.absolute_url()
ref = context.REQUEST.get('HTTP_REFERER', '').strip()
if not ref:
  return r.RESPONSE.redirect(raiz + '/manual_online')

for url, menu in (parametrizacao, protocolo, tramitacao, etiquetas, pesquisa, referencias_apensos):
  for u in url:
    if ref.find(u) != -1:
      return r.RESPONSE.redirect(raiz + menu)

return r.RESPONSE.redirect(raiz + '/manual_online')
