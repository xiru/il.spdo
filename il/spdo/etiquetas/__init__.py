from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, letter
from reportlab.graphics.barcode import code128
from reportlab.lib.units import mm, cm

from il.spdo.etiquetas.pimaco import FORMATOS_SUPORTADOS

SHOW_BORDER = __name__ == '__main__'

def geraPagina(formato, numeros, c, pagesize):
    w, h = pagesize
    for linha in range(formato['Linhas']):
        for coluna in range(formato['Colunas']):
            try:
                numero = numeros[linha][coluna]
            except IndexError:
                return
            x = formato['Esquerda']*cm + (formato['Horizontal']*cm * coluna)
            y = h - formato['Superior']*cm - (formato['Vertical']*cm * (linha+1))
            if SHOW_BORDER:
                c.rect(x, y, formato['Largura']*cm, formato['Altura']*cm)
            barcode = code128.Code128(numero, barWidth=0.26*mm, barHeight=13*mm, 
                                      quiet=False, humanReadable=True)
            barcode.drawOn(c, x+(1*mm), y+(4*mm))

def _geraNumeros(formato):
    l = []
    for linha in range(formato['Linhas']):
        c = []
        for coluna in range(formato['Colunas']):
            c.append('E-88888888/2011-88')
        l.append(c)
    return l

if __name__ == '__main__':
    for tipo in range(1, 17):
        formato = FORMATOS_SUPORTADOS[tipo]
        numeros = _geraNumeros(formato)
        pagesize = formato['Papel'] == 'A4' and A4 or letter
        c = canvas.Canvas("etiquetas-%d.pdf" % tipo, pagesize=pagesize)
        geraPagina(formato, numeros, c, pagesize)
        c.showPage()
        c.save()
