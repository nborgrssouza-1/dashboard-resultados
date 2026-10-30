"""Calcula os indicadores do painel a partir da lista de pedidos."""

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, timedelta

from .leitura import Pedido

META_ENTREGA_MIN = 45  # acima disso, a entrega conta como atrasada
DIAS_SEMANA = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"]
FAIXAS_ENTREGA = [(None, 30, "até 30 min"), (30, 45, "31 a 45 min"),
                  (45, 60, "46 a 60 min"), (60, None, "mais de 60 min")]


def media(valores) -> float:
    valores = list(valores)
    return sum(valores) / len(valores) if valores else 0.0


def entregues(pedidos: list[Pedido]) -> list[Pedido]:
    return [p for p in pedidos if p.entregue]


def atrasado(pedido: Pedido) -> bool:
    return pedido.tempo_entrega is not None and pedido.tempo_entrega > META_ENTREGA_MIN


@dataclass
class Resumo:
    pedidos: int
    cancelados: int
    faturamento: float
    ticket_medio: float
    tempo_medio: float
    pct_atrasados: float
    nota_media: float
    taxa_cancelamento: float


def resumir(pedidos: list[Pedido]) -> Resumo:
    ok = entregues(pedidos)
    faturamento = sum(p.valor for p in ok)
    cancelados = len(pedidos) - len(ok)
    return Resumo(
        pedidos=len(pedidos),
        cancelados=cancelados,
        faturamento=faturamento,
        ticket_medio=faturamento / len(ok) if ok else 0.0,
        tempo_medio=media(p.tempo_entrega for p in ok),
        pct_atrasados=media(atrasado(p) for p in ok),
        nota_media=media(p.avaliacao for p in ok if p.avaliacao is not None),
        taxa_cancelamento=cancelados / len(pedidos) if pedidos else 0.0,
    )


def por_mes(pedidos: list[Pedido]) -> dict[str, list[Pedido]]:
    """Agrupa os pedidos por mês, em ordem: {'2026-07': [...], '2026-08': [...]}."""
    grupos = defaultdict(list)
    for p in pedidos:
        grupos[p.data.strftime("%Y-%m")].append(p)
    return dict(sorted(grupos.items()))


def faturamento_semanal(pedidos: list[Pedido]) -> list[tuple[date, float]]:
    """Faturamento por semana (segunda a domingo). Semanas incompletas ficam de fora."""
    valores = defaultdict(float)
    dias = defaultdict(set)
    for p in pedidos:
        segunda = p.data - timedelta(days=p.data.weekday())
        dias[segunda].add(p.data)
        if p.entregue:
            valores[segunda] += p.valor
    return [(semana, valores[semana]) for semana in sorted(dias) if len(dias[semana]) == 7]


def media_por_hora(pedidos: list[Pedido]) -> list[tuple[int, float]]:
    """Média de pedidos por dia em cada horário."""
    if not pedidos:
        return []
    total_dias = len({p.data for p in pedidos})
    contagem = Counter(p.hora for p in pedidos)
    return [(h, contagem[h] / total_dias) for h in range(min(contagem), max(contagem) + 1)]


def media_por_dia_semana(pedidos: list[Pedido]) -> list[tuple[str, float]]:
    """Média de pedidos em cada dia da semana (segunda a domingo)."""
    contagem = Counter(p.data.weekday() for p in pedidos)
    quantos_dias = Counter(d.weekday() for d in {p.data for p in pedidos})
    return [(DIAS_SEMANA[d], contagem[d] / quantos_dias[d]) for d in range(7) if quantos_dias[d]]


def faturamento_por_categoria(pedidos: list[Pedido]) -> list[tuple[str, float]]:
    valores = defaultdict(float)
    for p in entregues(pedidos):
        valores[p.categoria] += p.valor
    return sorted(valores.items(), key=lambda item: item[1], reverse=True)


@dataclass
class DesempenhoBairro:
    bairro: str
    tempo_medio: float
    pct_atrasados: float
    taxa_cancelamento: float


def entrega_por_bairro(pedidos: list[Pedido]) -> list[DesempenhoBairro]:
    """Do bairro mais lento para o mais rápido."""
    grupos = defaultdict(list)
    for p in pedidos:
        grupos[p.bairro].append(p)
    resultado = []
    for bairro, lista in grupos.items():
        resumo = resumir(lista)
        resultado.append(DesempenhoBairro(bairro, resumo.tempo_medio, resumo.pct_atrasados,
                                          resumo.taxa_cancelamento))
    return sorted(resultado, key=lambda b: b.tempo_medio, reverse=True)


def faixa_de_entrega(minutos: int) -> str:
    for minimo, maximo, rotulo in FAIXAS_ENTREGA:
        if (minimo is None or minutos > minimo) and (maximo is None or minutos <= maximo):
            return rotulo
    raise ValueError(minutos)


def nota_por_faixa_entrega(pedidos: list[Pedido]) -> list[tuple[str, float, int]]:
    """Nota média por faixa de tempo de entrega: (faixa, nota média, quantidade de avaliações)."""
    notas = defaultdict(list)
    for p in entregues(pedidos):
        if p.avaliacao is not None:
            notas[faixa_de_entrega(p.tempo_entrega)].append(p.avaliacao)
    return [(rotulo, media(notas[rotulo]), len(notas[rotulo]))
            for _, _, rotulo in FAIXAS_ENTREGA if notas[rotulo]]
