"""Transforma os indicadores em recomendações de decisão.

Cada regra olha um aspecto dos dados, mostra a evidência com números e sugere uma ação.
Se os dados não mostram um problema claro, a regra não gera recomendação.
"""

from dataclasses import dataclass

from . import indicadores as ind
from .formato import moeda, numero, porcentagem
from .leitura import Pedido

HORAS_DE_PICO = 3  # tamanho da janela de pico, em horas


@dataclass
class Recomendacao:
    titulo: str
    evidencia: str
    acao: str


def horario_de_pico(pedidos: list[Pedido]) -> Recomendacao | None:
    por_hora = ind.media_por_hora(pedidos)
    if len(por_hora) < HORAS_DE_PICO:
        return None
    janelas = [por_hora[i:i + HORAS_DE_PICO] for i in range(len(por_hora) - HORAS_DE_PICO + 1)]
    pico = max(janelas, key=lambda janela: sum(media for _, media in janela))
    inicio, fim = pico[0][0], pico[-1][0] + 1
    participacao = sum(m for _, m in pico) / sum(m for _, m in por_hora)

    no_pico = [p for p in ind.entregues(pedidos) if inicio <= p.hora < fim]
    fora = [p for p in ind.entregues(pedidos) if not inicio <= p.hora < fim]
    tempo_pico = ind.media(p.tempo_entrega for p in no_pico)
    tempo_fora = ind.media(p.tempo_entrega for p in fora)
    return Recomendacao(
        titulo=f"Reforçar a operação das {inicio}h às {fim}h",
        evidencia=(f"{porcentagem(participacao, 0)} dos pedidos do dia acontecem nessas {HORAS_DE_PICO} horas, "
                   f"e a entrega leva em média {numero(tempo_pico)} min, contra {numero(tempo_fora)} min "
                   "no resto do dia."),
        acao=("Escalar mais entregadores nesse horário e avisar os restaurantes parceiros "
              "para reforçar a cozinha antes do pico."),
    )


def bairro_critico(pedidos: list[Pedido]) -> Recomendacao | None:
    bairros = ind.entrega_por_bairro(pedidos)
    if len(bairros) < 2:
        return None
    pior, melhor = bairros[0], bairros[-1]
    if pior.tempo_medio <= ind.META_ENTREGA_MIN * 0.9:
        return None
    return Recomendacao(
        titulo=f"Atacar os atrasos em {pior.bairro}",
        evidencia=(f"{pior.bairro} tem entrega média de {numero(pior.tempo_medio)} min, "
                   f"{porcentagem(pior.pct_atrasados, 0)} dos pedidos atrasados e "
                   f"{porcentagem(pior.taxa_cancelamento)} cancelados. No bairro mais rápido "
                   f"({melhor.bairro}), são {numero(melhor.tempo_medio)} min e "
                   f"{porcentagem(melhor.taxa_cancelamento)} cancelados."),
        acao=(f"Trazer restaurantes parceiros mais próximos de {pior.bairro} e mostrar uma previsão "
              "de entrega realista no app, para o cliente não desistir no meio da espera."),
    )


def atraso_derruba_nota(pedidos: list[Pedido]) -> Recomendacao | None:
    avaliados = [p for p in ind.entregues(pedidos) if p.avaliacao is not None]
    no_prazo = ind.media(p.avaliacao for p in avaliados if not ind.atrasado(p))
    atrasados = ind.media(p.avaliacao for p in avaliados if ind.atrasado(p))
    if not atrasados or no_prazo - atrasados < 0.3:
        return None
    return Recomendacao(
        titulo="Tratar a pontualidade como prioridade",
        evidencia=(f"Pedidos entregues em até {ind.META_ENTREGA_MIN} min recebem nota média "
                   f"{numero(no_prazo, 1)}; os atrasados, {numero(atrasados, 1)}."),
        acao=(f"Enviar um cupom automático quando a entrega passar de {ind.META_ENTREGA_MIN} min, "
              "para recuperar a experiência do cliente, e acompanhar a meta de atraso toda semana."),
    )


def dia_mais_fraco(pedidos: list[Pedido]) -> Recomendacao | None:
    por_dia = ind.media_por_dia_semana(pedidos)
    if len(por_dia) < 7:
        return None
    dia, pedidos_dia = min(por_dia, key=lambda item: item[1])
    media_semana = ind.media(m for _, m in por_dia)
    return Recomendacao(
        titulo=f"Criar uma campanha para a {dia}",
        evidencia=(f"A {dia} tem em média {numero(pedidos_dia)} pedidos, "
                   f"{porcentagem(1 - pedidos_dia / media_semana, 0)} abaixo da média da semana "
                   f"({numero(media_semana)} pedidos por dia)."),
        acao=(f"Oferecer cupons ou frete grátis às {dia}s para ocupar entregadores e "
              "restaurantes que ficam ociosos nesse dia."),
    )


def categoria_principal(pedidos: list[Pedido]) -> Recomendacao | None:
    categorias = ind.faturamento_por_categoria(pedidos)
    if not categorias:
        return None
    total = sum(valor for _, valor in categorias)
    nome, valor = categorias[0]
    da_categoria = [p for p in ind.entregues(pedidos) if p.categoria == nome]
    return Recomendacao(
        titulo=f"Dar destaque para {nome}",
        evidencia=(f"{nome} gera {porcentagem(valor / total, 0)} do faturamento, com ticket médio "
                   f"de {moeda(valor / len(da_categoria))}."),
        acao=(f"Colocar restaurantes de {nome} em destaque na tela inicial nos horários de pico "
              "e negociar combos com os parceiros dessa categoria."),
    )


REGRAS = [horario_de_pico, bairro_critico, atraso_derruba_nota, dia_mais_fraco, categoria_principal]


def recomendacoes(pedidos: list[Pedido]) -> list[Recomendacao]:
    return [r for r in (regra(pedidos) for regra in REGRAS) if r is not None]
