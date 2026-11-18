"""Desenha gráficos em SVG (imagem vetorial que o navegador mostra direto, sem bibliotecas).

As cores não ficam aqui: cada elemento recebe uma classe CSS (marca, grade, eixo...)
e a página define as cores, com versões para o modo claro e o escuro.
Elementos com o atributo data-dica mostram um balão com o valor ao passar o mouse.
"""

import math
from html import escape

LARGURA = 640
ESPESSURA_MAXIMA = 24  # barras finas: o espaço que sobra separa uma da outra
RAIO = 4  # ponta arredondada das barras


def escala(maximo: float, divisoes: int = 4) -> list[float]:
    """Marcações "redondas" do eixo, de 0 até um pouco acima do máximo: 0, 5, 10, 15, 20."""
    if maximo <= 0:
        return [0, 1]
    bruto = maximo / divisoes
    potencia = 10 ** math.floor(math.log10(bruto))
    passo = next(m * potencia for m in (1, 2, 2.5, 5, 10) if m * potencia >= bruto)
    return [i * passo for i in range(math.ceil(maximo / passo - 1e-9) + 1)]


def coluna(x: float, topo: float, largura: float, base: float) -> str:
    """Caminho de uma coluna com o topo arredondado e a base reta."""
    r = min(RAIO, largura / 2, base - topo)
    return (f"M{x:.1f},{base:.1f}V{topo + r:.1f}Q{x:.1f},{topo:.1f} {x + r:.1f},{topo:.1f}"
            f"H{x + largura - r:.1f}Q{x + largura:.1f},{topo:.1f} {x + largura:.1f},{topo + r:.1f}"
            f"V{base:.1f}Z")


def barra(x: float, y: float, comprimento: float, espessura: float) -> str:
    """Caminho de uma barra horizontal com a ponta direita arredondada."""
    r = min(RAIO, espessura / 2, comprimento)
    fim = x + comprimento
    return (f"M{x:.1f},{y:.1f}H{fim - r:.1f}Q{fim:.1f},{y:.1f} {fim:.1f},{y + r:.1f}"
            f"V{y + espessura - r:.1f}Q{fim:.1f},{y + espessura:.1f} {fim - r:.1f},{y + espessura:.1f}"
            f"H{x:.1f}Z")


def texto(x: float, y: float, conteudo: str, classe: str, ancora: str = "middle") -> str:
    return f'<text x="{x:.1f}" y="{y:.1f}" class="{classe}" text-anchor="{ancora}">{escape(conteudo)}</text>'


def svg(altura: float, descricao: str, conteudo: list[str]) -> str:
    return (f'<svg viewBox="0 0 {LARGURA} {altura:.0f}" role="img" aria-label="{escape(descricao)}">'
            + "".join(conteudo) + "</svg>")


def eixo_y(marcas: list[float], esquerda: float, direita: float, y_de, formatar) -> list[str]:
    partes = []
    for valor in marcas:
        y = y_de(valor)
        classe = "base" if valor == 0 else "grade"
        partes.append(f'<line x1="{esquerda}" x2="{direita}" y1="{y:.1f}" y2="{y:.1f}" class="{classe}"/>')
        partes.append(texto(esquerda - 8, y + 4, formatar(valor), "eixo", "end"))
    return partes


def colunas(rotulos: list[str], valores: list[float], dicas: list[str], formatar, descricao: str,
            altura: float = 260) -> str:
    """Gráfico de colunas verticais. O maior valor ganha um rótulo em cima da coluna."""
    esquerda, direita, topo, base = 52, LARGURA - 8, 24, altura - 28
    marcas = escala(max(valores))
    y_de = lambda v: base - (v / marcas[-1]) * (base - topo)
    faixa = (direita - esquerda) / len(valores)
    espessura = min(ESPESSURA_MAXIMA, faixa * 0.6)
    maior = valores.index(max(valores))

    partes = eixo_y(marcas, esquerda, direita, y_de, formatar)
    for i, (rotulo, valor, dica) in enumerate(zip(rotulos, valores, dicas)):
        x = esquerda + i * faixa
        partes.append(
            f'<g class="alvo" data-dica="{escape(dica)}">'
            f'<rect x="{x:.1f}" y="{topo}" width="{faixa:.1f}" height="{base - topo}" class="area-alvo"/>'
            f'<path d="{coluna(x + (faixa - espessura) / 2, y_de(valor), espessura, base)}" class="marca"/>'
            "</g>")
        partes.append(texto(x + faixa / 2, base + 18, rotulo, "eixo"))
        if i == maior:
            partes.append(texto(x + faixa / 2, y_de(valor) - 8, formatar(valor), "valor"))
    return svg(altura, descricao, partes)


def linha(rotulos: list[str], valores: list[float], dicas: list[str], formatar, descricao: str,
          altura: float = 260) -> str:
    """Gráfico de linha com área suave. Ao passar o mouse, uma guia vertical marca o ponto."""
    esquerda, direita, topo, base = 52, LARGURA - 16, 24, altura - 28
    marcas = escala(max(valores))
    y_de = lambda v: base - (v / marcas[-1]) * (base - topo)
    passo = (direita - esquerda) / (len(valores) - 1)
    pontos = [(esquerda + i * passo, y_de(v)) for i, v in enumerate(valores)]
    trajeto = " ".join(f"{x:.1f},{y:.1f}" for x, y in pontos)

    partes = eixo_y(marcas, esquerda, direita, y_de, formatar)
    partes.append(f'<polygon points="{esquerda},{base} {trajeto} {direita},{base}" class="area"/>')
    partes.append(f'<polyline points="{trajeto}" class="linha"/>')
    for i, rotulo in enumerate(rotulos):
        partes.append(texto(pontos[i][0], base + 18, rotulo, "eixo"))
    fim_x, fim_y = pontos[-1]
    partes.append(f'<circle cx="{fim_x:.1f}" cy="{fim_y:.1f}" r="4" class="ponto"/>')
    partes.append(texto(fim_x, fim_y - 12, formatar(valores[-1]), "valor", "end"))
    partes.append(f'<line class="guia" y1="{topo}" y2="{base}" x1="0" x2="0" visibility="hidden"/>')
    partes.append('<circle class="ponto ponto-guia" r="4" visibility="hidden"/>')
    for (x, y), dica in zip(pontos, dicas):
        partes.append(
            f'<rect x="{x - passo / 2:.1f}" y="{topo}" width="{passo:.1f}" height="{base - topo}" '
            f'class="area-alvo alvo-linha" data-dica="{escape(dica)}" data-x="{x:.1f}" data-y="{y:.1f}"/>')
    return svg(altura, descricao, partes)


def barras(rotulos: list[str], valores: list[float], dicas: list[str], formatar, descricao: str,
           referencia: float | None = None, rotulo_referencia: str = "") -> str:
    """Barras horizontais, cada uma com o valor na ponta. Pode ter uma linha de meta."""
    linha_altura, espessura = 36, 18
    esquerda, direita, topo = 112, LARGURA - 16, 8
    base = topo + linha_altura * len(valores)
    altura = base + (28 if referencia is not None else 8)
    maximo = max(valores + [referencia or 0]) * 1.18  # folga para o valor na ponta
    x_de = lambda v: esquerda + (v / maximo) * (direita - esquerda)

    partes = [f'<line x1="{esquerda}" x2="{esquerda}" y1="{topo}" y2="{base}" class="base"/>']
    for i, (rotulo, valor, dica) in enumerate(zip(rotulos, valores, dicas)):
        y = topo + i * linha_altura
        meio = y + linha_altura / 2
        partes.append(
            f'<g class="alvo" data-dica="{escape(dica)}">'
            f'<rect x="0" y="{y}" width="{LARGURA}" height="{linha_altura}" class="area-alvo"/>'
            f'<path d="{barra(esquerda, meio - espessura / 2, x_de(valor) - esquerda, espessura)}" class="marca"/>'
            "</g>")
        partes.append(texto(esquerda - 10, meio + 4, rotulo, "rotulo", "end"))
        partes.append(texto(x_de(valor) + 6, meio + 4, formatar(valor), "valor", "start"))
    if referencia is not None:
        x = x_de(referencia)
        partes.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{topo}" y2="{base + 4}" class="referencia"/>')
        partes.append(texto(x, base + 20, rotulo_referencia, "eixo"))
    return svg(altura, descricao, partes)
