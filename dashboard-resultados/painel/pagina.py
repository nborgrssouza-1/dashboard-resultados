"""Monta a página HTML do painel: indicadores, recomendações e gráficos."""

from html import escape

from . import graficos
from . import indicadores as ind
from .decisoes import recomendacoes
from .formato import compacto, moeda, nome_mes, numero, porcentagem
from .leitura import Pedido

ESTILO = """
:root {
  color-scheme: light;
  --pagina: #f9f9f7; --superficie: #fcfcfb; --borda: rgba(11,11,11,0.10);
  --texto: #0b0b0b; --texto-2: #52514e; --texto-suave: #898781;
  --grade: #e1e0d9; --eixo: #c3c2b7; --serie: #2a78d6; --referencia: #52514e;
  --bom: #006300; --ruim: #d03b3b;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    color-scheme: dark;
    --pagina: #0d0d0d; --superficie: #1a1a19; --borda: rgba(255,255,255,0.10);
    --texto: #f0efec; --texto-2: #c3c2b7; --texto-suave: #898781;
    --grade: #2c2c2a; --eixo: #383835; --serie: #3987e5; --referencia: #c3c2b7;
    --bom: #0ca30c; --ruim: #e66767;
  }
}
:root[data-theme="dark"] {
  color-scheme: dark;
  --pagina: #0d0d0d; --superficie: #1a1a19; --borda: rgba(255,255,255,0.10);
  --texto: #f0efec; --texto-2: #c3c2b7; --texto-suave: #898781;
  --grade: #2c2c2a; --eixo: #383835; --serie: #3987e5; --referencia: #c3c2b7;
  --bom: #0ca30c; --ruim: #e66767;
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--pagina); color: var(--texto);
       font: 15px/1.5 system-ui, -apple-system, "Segoe UI", sans-serif; }
main { max-width: 1120px; margin: 0 auto; padding: 32px 16px 48px; }
h1 { font-size: 26px; margin: 0; }
h2 { font-size: 18px; margin: 40px 0 4px; }
h3 { font-size: 15px; margin: 0; }
.sub { color: var(--texto-2); margin: 4px 0 16px; }
.cartao { background: var(--superficie); border: 1px solid var(--borda); border-radius: 12px; padding: 20px; }
.numeros { display: grid; gap: 12px; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); }
.numeros .destaque { grid-column: 1 / -1; }
.indicador .rotulo { color: var(--texto-2); font-size: 13px; }
.indicador .valor { font-size: 24px; font-weight: 600; margin: 2px 0; }
.indicador.destaque .valor { font-size: 48px; line-height: 1.1; }
.variacao { font-size: 13px; color: var(--texto-2); }
.variacao.bom { color: var(--bom); } .variacao.ruim { color: var(--ruim); }
.decisoes { display: grid; gap: 12px; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            padding: 0; margin: 0; list-style: none; counter-reset: decisao; }
.decisoes li { counter-increment: decisao; }
.decisoes h3::before { content: counter(decisao) ". "; color: var(--texto-suave); }
.decisoes p { margin: 8px 0 0; font-size: 14px; color: var(--texto-2); }
.decisoes strong { color: var(--texto); }
.graficos { display: grid; gap: 12px; grid-template-columns: repeat(auto-fit, minmax(min(100%, 480px), 1fr)); }
.graficos .sub { font-size: 13px; margin-bottom: 8px; }
svg { width: 100%; height: auto; display: block; overflow: visible; }
svg text { font: 11px system-ui, -apple-system, "Segoe UI", sans-serif; }
.eixo { fill: var(--texto-suave); font-variant-numeric: tabular-nums; }
.rotulo { fill: var(--texto-2); font-size: 12px; }
.valor { fill: var(--texto); font-weight: 600; paint-order: stroke; stroke: var(--superficie); stroke-width: 4px; }
.grade { stroke: var(--grade); stroke-width: 1; }
.base { stroke: var(--eixo); stroke-width: 1; }
.referencia { stroke: var(--referencia); stroke-width: 1.5; }
.marca { fill: var(--serie); }
.alvo:hover .marca { opacity: 0.75; }
.area-alvo { fill: transparent; }
.linha { fill: none; stroke: var(--serie); stroke-width: 2; stroke-linejoin: round; stroke-linecap: round; }
.area { fill: var(--serie); opacity: 0.1; }
.ponto { fill: var(--serie); stroke: var(--superficie); stroke-width: 2; }
.guia { stroke: var(--eixo); stroke-width: 1; }
details { margin-top: 8px; font-size: 13px; }
summary { cursor: pointer; color: var(--texto-2); }
table { border-collapse: collapse; margin-top: 8px; width: 100%; font-variant-numeric: tabular-nums; }
th, td { text-align: left; padding: 4px 8px; border-bottom: 1px solid var(--grade); }
td + td, th + th { text-align: right; }
#dica { position: fixed; pointer-events: none; background: var(--superficie); color: var(--texto);
        border: 1px solid var(--borda); border-radius: 8px; padding: 6px 10px; font-size: 13px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.12); white-space: pre-line; z-index: 10; }
.sr { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); }
footer { margin-top: 40px; color: var(--texto-suave); font-size: 13px; }
"""

SCRIPT = """
const dica = document.getElementById('dica');
function mostrar(evento, texto) {
  dica.textContent = texto;
  dica.hidden = false;
  const x = Math.min(evento.clientX + 14, window.innerWidth - dica.offsetWidth - 8);
  dica.style.left = x + 'px';
  dica.style.top = (evento.clientY + 14) + 'px';
}
document.querySelectorAll('[data-dica]').forEach(el => {
  el.addEventListener('pointermove', e => mostrar(e, el.dataset.dica));
  el.addEventListener('pointerleave', () => { dica.hidden = true; });
});
document.querySelectorAll('.alvo-linha').forEach(el => {
  const svg = el.ownerSVGElement, guia = svg.querySelector('.guia'), ponto = svg.querySelector('.ponto-guia');
  el.addEventListener('pointerenter', () => {
    guia.setAttribute('x1', el.dataset.x); guia.setAttribute('x2', el.dataset.x);
    ponto.setAttribute('cx', el.dataset.x); ponto.setAttribute('cy', el.dataset.y);
    guia.setAttribute('visibility', 'visible'); ponto.setAttribute('visibility', 'visible');
  });
  el.addEventListener('pointerleave', () => {
    guia.setAttribute('visibility', 'hidden'); ponto.setAttribute('visibility', 'hidden');
  });
});
"""


def variacao(atual: float, anterior: float, modo: str, maior_e_melhor: bool, mes_anterior: str) -> str:
    """Texto e cor da comparação com o mês anterior. Verde quando melhorou, vermelho quando piorou."""
    if modo == "relativo":
        diferenca = (atual - anterior) / anterior if anterior else 0.0
        quanto = porcentagem(abs(diferenca))
    elif modo == "pontos":  # indicadores que já são porcentagem: diferença em pontos percentuais
        diferenca = atual - anterior
        quanto = numero(abs(diferenca) * 100, 1) + " p.p."
    else:  # diferença simples, com unidade (ex.: "min")
        diferenca = atual - anterior
        quanto = numero(abs(diferenca), 2 if modo == "" else 1) + modo
    if not any(c in "123456789" for c in quanto):  # a diferença aparece como zero
        diferenca = 0.0
    if diferenca == 0:
        return f'<div class="variacao">= igual a {mes_anterior}</div>'
    seta = "▲" if diferenca > 0 else "▼"
    classe = "bom" if (diferenca > 0) == maior_e_melhor else "ruim"
    situacao = "melhorou" if classe == "bom" else "piorou"
    return (f'<div class="variacao {classe}" title="{situacao}">{seta} {quanto} vs {mes_anterior}'
            f' <span class="sr">({situacao})</span></div>')


def cartoes_de_indicadores(atual: ind.Resumo, anterior: ind.Resumo, mes_anterior: str) -> str:
    # (rótulo, valor atual, valor anterior, formatação, modo da variação, maior é melhor?)
    itens = [
        ("Faturamento", atual.faturamento, anterior.faturamento, moeda, "relativo", True),
        ("Pedidos", atual.pedidos, anterior.pedidos, numero, "relativo", True),
        ("Ticket médio", atual.ticket_medio, anterior.ticket_medio, moeda, "relativo", True),
        ("Tempo médio de entrega", atual.tempo_medio, anterior.tempo_medio,
         lambda v: numero(v, 1) + " min", " min", False),
        (f"Entregas acima de {ind.META_ENTREGA_MIN} min", atual.pct_atrasados, anterior.pct_atrasados,
         porcentagem, "pontos", False),
        ("Nota média", atual.nota_media, anterior.nota_media, lambda v: numero(v, 2), "", True),
        ("Cancelamentos", atual.taxa_cancelamento, anterior.taxa_cancelamento, porcentagem, "pontos", False),
    ]
    cartoes = []
    for i, (rotulo, valor, antes, formatar, modo, maior_e_melhor) in enumerate(itens):
        classe = "cartao indicador destaque" if i == 0 else "cartao indicador"
        cartoes.append(
            f'<div class="{classe}"><div class="rotulo">{escape(rotulo)}</div>'
            f'<div class="valor">{escape(formatar(valor))}</div>'
            f"{variacao(valor, antes, modo, maior_e_melhor, mes_anterior)}</div>")
    return '<div class="numeros">' + "".join(cartoes) + "</div>"


def tabela(cabecalho: list[str], linhas: list[list[str]]) -> str:
    topo = "".join(f"<th>{escape(c)}</th>" for c in cabecalho)
    corpo = "".join("<tr>" + "".join(f"<td>{escape(c)}</td>" for c in linha) + "</tr>" for linha in linhas)
    return f"<details><summary>Ver tabela</summary><table><tr>{topo}</tr>{corpo}</table></details>"


def cartao_grafico(titulo: str, subtitulo: str, desenho: str, tabela_html: str) -> str:
    return (f'<section class="cartao"><h3>{escape(titulo)}</h3><p class="sub">{escape(subtitulo)}</p>'
            f"{desenho}{tabela_html}</section>")


def secao_graficos(pedidos: list[Pedido]) -> str:
    cartoes = []

    semanas = ind.faturamento_semanal(pedidos)
    rotulos = [s.strftime("%d/%m") for s, _ in semanas]
    valores = [v for _, v in semanas]
    cartoes.append(cartao_grafico(
        "Faturamento por semana", "Semanas de segunda a domingo, só pedidos entregues",
        graficos.linha(rotulos, valores, [f"Semana de {r}\n{moeda(v)}" for r, v in zip(rotulos, valores)],
                       compacto, "Faturamento semanal em reais"),
        tabela(["Semana", "Faturamento"], [[r, moeda(v)] for r, v in zip(rotulos, valores)])))

    horas = ind.media_por_hora(pedidos)
    cartoes.append(cartao_grafico(
        "Pedidos por horário", "Média de pedidos por dia em cada hora",
        graficos.colunas([f"{h}h" for h, _ in horas], [m for _, m in horas],
                         [f"{h}h às {h + 1}h\n{numero(m, 1)} pedidos por dia" for h, m in horas],
                         compacto, "Média de pedidos por hora do dia"),
        tabela(["Horário", "Pedidos por dia"], [[f"{h}h", numero(m, 1)] for h, m in horas])))

    dias = ind.media_por_dia_semana(pedidos)
    cartoes.append(cartao_grafico(
        "Pedidos por dia da semana", "Média de pedidos em cada dia",
        graficos.colunas([d[:3] for d, _ in dias], [m for _, m in dias],
                         [f"{d}\n{numero(m)} pedidos em média" for d, m in dias],
                         compacto, "Média de pedidos por dia da semana"),
        tabela(["Dia", "Pedidos por dia"], [[d, numero(m)] for d, m in dias])))

    categorias = ind.faturamento_por_categoria(pedidos)
    total = sum(v for _, v in categorias)
    cartoes.append(cartao_grafico(
        "Faturamento por categoria", "Total do período, da maior para a menor",
        graficos.barras([c for c, _ in categorias], [v for _, v in categorias],
                        [f"{c}\n{moeda(v)} ({porcentagem(v / total)} do total)" for c, v in categorias],
                        lambda v: "R$ " + compacto(v), "Faturamento por categoria de restaurante"),
        tabela(["Categoria", "Faturamento", "Participação"],
               [[c, moeda(v), porcentagem(v / total)] for c, v in categorias])))

    bairros = ind.entrega_por_bairro(pedidos)
    cartoes.append(cartao_grafico(
        "Tempo médio de entrega por bairro", f"A linha marca a meta de {ind.META_ENTREGA_MIN} minutos",
        graficos.barras([b.bairro for b in bairros], [b.tempo_medio for b in bairros],
                        [f"{b.bairro}\n{numero(b.tempo_medio, 1)} min em média\n"
                         f"{porcentagem(b.pct_atrasados)} atrasados · {porcentagem(b.taxa_cancelamento)} cancelados"
                         for b in bairros],
                        lambda v: numero(v) + " min", "Tempo médio de entrega por bairro",
                        referencia=ind.META_ENTREGA_MIN, rotulo_referencia=f"Meta: {ind.META_ENTREGA_MIN} min"),
        tabela(["Bairro", "Tempo médio", "Atrasados", "Cancelados"],
               [[b.bairro, numero(b.tempo_medio, 1) + " min", porcentagem(b.pct_atrasados),
                 porcentagem(b.taxa_cancelamento)] for b in bairros])))

    faixas = ind.nota_por_faixa_entrega(pedidos)
    cartoes.append(cartao_grafico(
        "Nota do cliente por tempo de entrega", "Nota média (de 1 a 5) conforme a demora",
        graficos.barras([f for f, _, _ in faixas], [n for _, n, _ in faixas],
                        [f"Entrega {f}\nnota {numero(n, 2)} ({numero(q)} avaliações)" for f, n, q in faixas],
                        lambda v: numero(v, 1), "Nota média por faixa de tempo de entrega"),
        tabela(["Tempo de entrega", "Nota média", "Avaliações"],
               [[f, numero(n, 2), numero(q)] for f, n, q in faixas])))

    return '<div class="graficos">' + "".join(cartoes) + "</div>"


def secao_decisoes(pedidos: list[Pedido]) -> str:
    itens = []
    for r in recomendacoes(pedidos):
        itens.append(
            f'<li class="cartao"><h3>{escape(r.titulo)}</h3>'
            f"<p><strong>O que os dados mostram:</strong> {escape(r.evidencia)}</p>"
            f"<p><strong>Decisão sugerida:</strong> {escape(r.acao)}</p></li>")
    return '<ol class="decisoes">' + "".join(itens) + "</ol>"


def montar(pedidos: list[Pedido]) -> str:
    meses = ind.por_mes(pedidos)
    if len(meses) < 2:
        raise ValueError("o painel precisa de pelo menos 2 meses de dados para comparar")
    chaves = list(meses)
    mes_atual, mes_anterior = chaves[-1], chaves[-2]
    atual, anterior = ind.resumir(meses[mes_atual]), ind.resumir(meses[mes_anterior])
    primeiro, ultimo = min(p.data for p in pedidos), max(p.data for p in pedidos)
    periodo = f"{primeiro:%d/%m/%Y} a {ultimo:%d/%m/%Y}"

    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Painel de Resultados</title>
<style>{ESTILO}</style>
</head>
<body>
<main>
  <h1>Painel de Resultados · Rangô</h1>
  <p class="sub">{numero(len(pedidos))} pedidos de {periodo} · dados fictícios</p>

  <h2>{nome_mes(mes_atual).capitalize()} em números</h2>
  <p class="sub">Comparação com {nome_mes(mes_anterior)}. Verde: melhorou; vermelho: piorou.</p>
  {cartoes_de_indicadores(atual, anterior, nome_mes(mes_anterior))}

  <h2>Decisões recomendadas</h2>
  <p class="sub">Geradas automaticamente a partir dos dados do período todo.</p>
  {secao_decisoes(pedidos)}

  <h2>Análise do período</h2>
  <p class="sub">Passe o mouse nos gráficos para ver os valores, ou abra a tabela de cada um.</p>
  {secao_graficos(pedidos)}

  <footer>Rangô é um app de delivery fictício. Dados gerados por gerar_dados.py.</footer>
</main>
<div id="dica" hidden></div>
<script>{SCRIPT}</script>
</body>
</html>
"""
