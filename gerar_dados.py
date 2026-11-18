"""Gera dados fictícios de pedidos do Rangô (app de delivery fictício).

Os dados são aleatórios, mas com padrões realistas embutidos para o painel ter o que mostrar:
- picos no almoço e no jantar, e mais pedidos no fim de semana;
- crescimento leve mês a mês;
- bairros mais distantes com entregas mais demoradas e mais cancelamentos;
- entregas atrasadas recebem notas piores.

Uso:
    python3 gerar_dados.py              # cria dados/pedidos.csv
"""

import csv
import random
from datetime import date, timedelta
from pathlib import Path

ARQUIVO = Path(__file__).parent / "dados" / "pedidos.csv"
INICIO = date(2026, 7, 1)
FIM = date(2026, 9, 30)
PEDIDOS_POR_DIA = 52
CRESCIMENTO_POR_DIA = 0.003  # cerca de 9% ao mês

# segunda a domingo
PESO_DIA_SEMANA = [0.9, 0.7, 0.85, 0.95, 1.25, 1.4, 1.3]

PESO_HORA = {10: 1, 11: 4, 12: 9, 13: 7, 14: 3, 15: 2, 16: 2, 17: 3,
             18: 6, 19: 11, 20: 12, 21: 8, 22: 4, 23: 2}

# categoria: (peso, ticket médio, restaurantes)
CATEGORIAS = {
    "Lanches": (28, 42, ["Burger do Zé", "Lanchonete Central"]),
    "Pizza": (22, 68, ["Pizzaria Bella Massa", "Forno a Lenha"]),
    "Brasileira": (18, 35, ["Cantina da Vó", "Marmitaria Sabor Caseiro"]),
    "Japonesa": (12, 95, ["Sushi Kento"]),
    "Açaí": (8, 28, ["Açaí da Praia"]),
    "Saudável": (6, 38, ["Verde Vida"]),
    "Doces": (6, 30, ["Doce Encanto"]),
}

# bairro: (peso, tempo médio de entrega em minutos)
BAIRROS = {
    "Centro": (25, 28),
    "Bela Vista": (20, 32),
    "Vila Nova": (18, 35),
    "Jardim Norte": (15, 38),
    "Parque Sul": (12, 40),
    "Alto da Serra": (10, 50),
}

PAGAMENTOS = {"Cartão de crédito": 40, "Pix": 35, "Cartão de débito": 12, "Vale-refeição": 10, "Dinheiro": 3}
NOTAS = {5: 55, 4: 30, 3: 10, 2: 3, 1: 2}


def sortear(rng: random.Random, pesos: dict):
    return rng.choices(list(pesos), weights=list(pesos.values()))[0]


def gerar_pedido(rng: random.Random, numero: int, dia: date) -> dict:
    hora = sortear(rng, PESO_HORA)
    categoria = sortear(rng, {c: dados[0] for c, dados in CATEGORIAS.items()})
    _, ticket, restaurantes = CATEGORIAS[categoria]
    bairro = sortear(rng, {b: dados[0] for b, dados in BAIRROS.items()})
    tempo_esperado = BAIRROS[bairro][1] + (8 if 19 <= hora <= 21 else 0) + (4 if dia.weekday() == 5 else 0)

    # Quanto maior o tempo esperado, maior a chance de o cliente desistir.
    chance_cancelar = 0.015 + max(0, tempo_esperado - 30) * 0.004
    cancelado = rng.random() < chance_cancelar

    tempo = avaliacao = ""
    if not cancelado:
        tempo = max(12, round(rng.gauss(tempo_esperado, 8)))
        if rng.random() < 0.6:  # nem todo cliente avalia
            nota = sortear(rng, NOTAS)
            if tempo > 60:
                nota -= 2
            elif tempo > 45 and rng.random() < 0.6:
                nota -= 1
            avaliacao = max(1, nota)

    return {
        "pedido": f"P{numero:05d}",
        "data": dia.isoformat(),
        "hora": f"{hora:02d}:{rng.randint(0, 59):02d}",
        "restaurante": rng.choice(restaurantes),
        "categoria": categoria,
        "bairro": bairro,
        "pagamento": sortear(rng, PAGAMENTOS),
        "valor": f"{max(15.0, rng.gauss(ticket, ticket * 0.25)):.2f}",
        "status": "cancelado" if cancelado else "entregue",
        "tempo_entrega_min": tempo,
        "avaliacao": avaliacao,
    }


def gerar(semente: int = 42) -> list[dict]:
    rng = random.Random(semente)
    pedidos = []
    dia, indice = INICIO, 0
    while dia <= FIM:
        esperado = PEDIDOS_POR_DIA * PESO_DIA_SEMANA[dia.weekday()] * (1 + CRESCIMENTO_POR_DIA * indice)
        do_dia = [gerar_pedido(rng, 0, dia) for _ in range(round(rng.gauss(esperado, esperado * 0.08)))]
        pedidos.extend(sorted(do_dia, key=lambda p: p["hora"]))
        dia += timedelta(days=1)
        indice += 1
    for numero, pedido in enumerate(pedidos, start=1):
        pedido["pedido"] = f"P{numero:05d}"
    return pedidos


def salvar(pedidos: list[dict], arquivo: Path = ARQUIVO):
    arquivo.parent.mkdir(parents=True, exist_ok=True)
    with open(arquivo, "w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=list(pedidos[0]))
        escritor.writeheader()
        escritor.writerows(pedidos)


if __name__ == "__main__":
    pedidos = gerar()
    salvar(pedidos)
    print(f"{len(pedidos)} pedidos gerados em {ARQUIVO}")
