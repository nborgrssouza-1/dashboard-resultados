"""Formata números no padrão brasileiro (1.234,56)."""

MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
         "agosto", "setembro", "outubro", "novembro", "dezembro"]


def numero(valor: float, casas: int = 0) -> str:
    texto = f"{valor:,.{casas}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def moeda(valor: float) -> str:
    return "R$ " + numero(valor, 2)


def porcentagem(fracao: float, casas: int = 1) -> str:
    return numero(fracao * 100, casas) + "%"


def compacto(valor: float) -> str:
    """Versão curta para eixos de gráfico: 12000 -> "12 mil"."""
    if abs(valor) >= 1000:
        milhares = valor / 1000
        return numero(milhares, 0 if milhares == int(milhares) else 1) + " mil"
    return numero(valor, 0 if valor == int(valor) else 1)


def nome_mes(chave: str) -> str:
    """'2026-09' -> 'setembro'"""
    return MESES[int(chave[5:7]) - 1]
