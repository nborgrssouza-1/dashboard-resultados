"""Lê o arquivo CSV de pedidos e transforma cada linha em um objeto Pedido."""

import csv
from dataclasses import dataclass
from datetime import date
from pathlib import Path

COLUNAS = ["pedido", "data", "hora", "restaurante", "categoria", "bairro", "pagamento",
           "valor", "status", "tempo_entrega_min", "avaliacao"]
STATUS_VALIDOS = {"entregue", "cancelado"}


@dataclass
class Pedido:
    id: str
    data: date
    hora: int
    restaurante: str
    categoria: str
    bairro: str
    pagamento: str
    valor: float
    status: str
    tempo_entrega: int | None
    avaliacao: int | None

    @property
    def entregue(self) -> bool:
        return self.status == "entregue"


def inteiro_ou_vazio(texto: str) -> int | None:
    return int(texto) if texto.strip() else None


def converter(linha: dict) -> Pedido:
    status = linha["status"].strip().lower()
    if status not in STATUS_VALIDOS:
        raise ValueError(f"status desconhecido: {linha['status']!r}")
    return Pedido(
        id=linha["pedido"],
        data=date.fromisoformat(linha["data"]),
        hora=int(linha["hora"].split(":")[0]),
        restaurante=linha["restaurante"],
        categoria=linha["categoria"],
        bairro=linha["bairro"],
        pagamento=linha["pagamento"],
        valor=float(linha["valor"]),
        status=status,
        tempo_entrega=inteiro_ou_vazio(linha["tempo_entrega_min"]),
        avaliacao=inteiro_ou_vazio(linha["avaliacao"]),
    )


def ler_pedidos(arquivo: Path) -> list[Pedido]:
    with open(arquivo, newline="", encoding="utf-8") as f:
        leitor = csv.DictReader(f)
        faltando = set(COLUNAS) - set(leitor.fieldnames or [])
        if faltando:
            raise ValueError(f"colunas faltando no arquivo: {', '.join(sorted(faltando))}")
        pedidos = []
        for numero_linha, linha in enumerate(leitor, start=2):
            try:
                pedidos.append(converter(linha))
            except ValueError as erro:
                raise ValueError(f"linha {numero_linha}: {erro}") from erro
    return pedidos
