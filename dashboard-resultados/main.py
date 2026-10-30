"""Gera o painel de resultados a partir do arquivo de pedidos.

Uso:
    python3 main.py                                  # lê dados/pedidos.csv e cria saida/dashboard.html
    python3 main.py --dados outro.csv --saida painel.html
"""

import argparse
from pathlib import Path

from painel import indicadores as ind
from painel.decisoes import recomendacoes
from painel.formato import moeda, nome_mes, numero, porcentagem
from painel.leitura import ler_pedidos
from painel.pagina import montar

PASTA = Path(__file__).parent


def mostrar_resumo(pedidos):
    meses = ind.por_mes(pedidos)
    mes = list(meses)[-1]
    r = ind.resumir(meses[mes])
    print(f"\n{nome_mes(mes).capitalize()} em números")
    print(f"  Faturamento ........... {moeda(r.faturamento)}")
    print(f"  Pedidos ............... {numero(r.pedidos)}")
    print(f"  Ticket médio .......... {moeda(r.ticket_medio)}")
    print(f"  Tempo médio de entrega  {numero(r.tempo_medio, 1)} min")
    print(f"  Entregas atrasadas .... {porcentagem(r.pct_atrasados)}")
    print(f"  Nota média ............ {numero(r.nota_media, 2)}")
    print(f"  Cancelamentos ......... {porcentagem(r.taxa_cancelamento)}")

    print("\nDecisões recomendadas")
    for i, rec in enumerate(recomendacoes(pedidos), start=1):
        print(f"  {i}. {rec.titulo}")
        print(f"     {rec.evidencia}")
        print(f"     -> {rec.acao}")


def main():
    parser = argparse.ArgumentParser(description="Gera o painel de resultados do Rangô.")
    parser.add_argument("--dados", type=Path, default=PASTA / "dados" / "pedidos.csv")
    parser.add_argument("--saida", type=Path, default=PASTA / "saida" / "dashboard.html")
    args = parser.parse_args()

    pedidos = ler_pedidos(args.dados)
    print(f"{numero(len(pedidos))} pedidos lidos de {args.dados.name}")
    mostrar_resumo(pedidos)

    args.saida.parent.mkdir(parents=True, exist_ok=True)
    args.saida.write_text(montar(pedidos), encoding="utf-8")
    print(f"\nPainel salvo em {args.saida}")
    print("Abra o arquivo no navegador (dois cliques) para ver os gráficos.")


if __name__ == "__main__":
    main()
