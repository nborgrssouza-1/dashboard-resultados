"""Testes automatizados.

Rodar a partir da pasta do projeto:
    python3 -m unittest discover -v
"""

import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

import gerar_dados
from painel import decisoes, graficos
from painel import indicadores as ind
from painel.formato import compacto, moeda, porcentagem
from painel.leitura import Pedido, ler_pedidos
from painel.pagina import montar


def pedido(dia=date(2026, 9, 1), hora=12, valor=50.0, status="entregue", tempo=30, nota=5,
           bairro="Centro", categoria="Lanches"):
    return Pedido("P1", dia, hora, "Restaurante", categoria, bairro, "Pix", valor, status,
                  tempo if status == "entregue" else None, nota if status == "entregue" else None)


class TestFormato(unittest.TestCase):
    def test_padrao_brasileiro(self):
        self.assertEqual(moeda(1234.5), "R$ 1.234,50")
        self.assertEqual(porcentagem(0.256), "25,6%")
        self.assertEqual(compacto(12000), "12 mil")
        self.assertEqual(compacto(1500), "1,5 mil")


class TestLeitura(unittest.TestCase):
    def test_le_o_arquivo_gerado(self):
        with tempfile.TemporaryDirectory() as pasta:
            arquivo = Path(pasta) / "pedidos.csv"
            gerar_dados.salvar(gerar_dados.gerar()[:50], arquivo)
            pedidos = ler_pedidos(arquivo)
        self.assertEqual(len(pedidos), 50)
        self.assertIsInstance(pedidos[0].data, date)

    def test_valor_invalido_informa_a_linha(self):
        with tempfile.TemporaryDirectory() as pasta:
            arquivo = Path(pasta) / "pedidos.csv"
            linhas = gerar_dados.gerar()[:3]
            linhas[1]["valor"] = "abc"
            gerar_dados.salvar(linhas, arquivo)
            with self.assertRaisesRegex(ValueError, "linha 3"):
                ler_pedidos(arquivo)

    def test_dados_gerados_sao_sempre_os_mesmos(self):
        self.assertEqual(gerar_dados.gerar()[:20], gerar_dados.gerar()[:20])


class TestIndicadores(unittest.TestCase):
    def test_resumo(self):
        pedidos = [pedido(valor=40, tempo=30, nota=5), pedido(valor=60, tempo=50, nota=3),
                   pedido(status="cancelado")]
        r = ind.resumir(pedidos)
        self.assertEqual(r.pedidos, 3)
        self.assertEqual(r.faturamento, 100)  # cancelado não entra no faturamento
        self.assertEqual(r.ticket_medio, 50)
        self.assertEqual(r.tempo_medio, 40)
        self.assertEqual(r.pct_atrasados, 0.5)
        self.assertEqual(r.nota_media, 4)
        self.assertAlmostEqual(r.taxa_cancelamento, 1 / 3)

    def test_resumo_vazio_nao_quebra(self):
        self.assertEqual(ind.resumir([]).ticket_medio, 0)

    def test_semana_incompleta_fica_de_fora(self):
        segunda = date(2026, 9, 7)
        pedidos = [pedido(dia=segunda + timedelta(days=i)) for i in range(7)] + [pedido(dia=date(2026, 9, 14))]
        semanas = ind.faturamento_semanal(pedidos)
        self.assertEqual(semanas, [(segunda, 350.0)])

    def test_media_por_hora_divide_pelo_numero_de_dias(self):
        pedidos = [pedido(dia=date(2026, 9, 1), hora=12), pedido(dia=date(2026, 9, 1), hora=12),
                   pedido(dia=date(2026, 9, 2), hora=14)]
        self.assertEqual(ind.media_por_hora(pedidos), [(12, 1.0), (13, 0.0), (14, 0.5)])

    def test_faixas_de_entrega(self):
        self.assertEqual(ind.faixa_de_entrega(30), "até 30 min")
        self.assertEqual(ind.faixa_de_entrega(45), "31 a 45 min")
        self.assertEqual(ind.faixa_de_entrega(46), "46 a 60 min")
        self.assertEqual(ind.faixa_de_entrega(90), "mais de 60 min")

    def test_bairros_do_mais_lento_ao_mais_rapido(self):
        pedidos = [pedido(bairro="Perto", tempo=20), pedido(bairro="Longe", tempo=60)]
        self.assertEqual([b.bairro for b in ind.entrega_por_bairro(pedidos)], ["Longe", "Perto"])


class TestDecisoes(unittest.TestCase):
    def test_aponta_o_bairro_com_mais_atraso(self):
        pedidos = [pedido(bairro="Centro", tempo=25)] * 5 + [pedido(bairro="Longe", tempo=55)] * 5
        self.assertIn("Longe", decisoes.bairro_critico(pedidos).titulo)

    def test_nao_inventa_problema_quando_tudo_esta_no_prazo(self):
        pedidos = [pedido(bairro="A", tempo=25), pedido(bairro="B", tempo=30)]
        self.assertIsNone(decisoes.bairro_critico(pedidos))
        self.assertIsNone(decisoes.atraso_derruba_nota(pedidos))

    def test_recomendacoes_com_os_dados_ficticios(self):
        with tempfile.TemporaryDirectory() as pasta:
            arquivo = Path(pasta) / "pedidos.csv"
            gerar_dados.salvar(gerar_dados.gerar(), arquivo)
            pedidos = ler_pedidos(arquivo)
        titulos = [r.titulo for r in decisoes.recomendacoes(pedidos)]
        self.assertIn("Reforçar a operação das 19h às 22h", titulos)
        self.assertIn("Atacar os atrasos em Alto da Serra", titulos)
        self.assertIn("Criar uma campanha para a terça", titulos)


class TestGraficos(unittest.TestCase):
    def test_escala_com_numeros_redondos(self):
        self.assertEqual(graficos.escala(83), [0, 25, 50, 75, 100])
        self.assertEqual(graficos.escala(10.4), [0, 5, 10, 15])

    def test_grafico_tem_uma_marca_por_valor(self):
        desenho = graficos.colunas(["a", "b", "c"], [1, 2, 3], ["1", "2", "3"], str, "teste")
        self.assertTrue(desenho.startswith("<svg"))
        self.assertEqual(desenho.count('class="marca"'), 3)

    def test_texto_e_escapado(self):
        desenho = graficos.barras(["<b>"], [1], ["x"], str, "teste")
        self.assertIn("&lt;b&gt;", desenho)


class TestPagina(unittest.TestCase):
    def test_precisa_de_dois_meses(self):
        with self.assertRaises(ValueError):
            montar([pedido()])

    def test_pagina_completa(self):
        pedidos = [pedido(dia=date(2026, 8, d), hora=h, tempo=20 + h, bairro=b)
                   for d in range(1, 29) for h in (12, 20) for b in ("Centro", "Serra")]
        pedidos += [pedido(dia=date(2026, 9, d), hora=20, tempo=55, bairro="Serra") for d in range(1, 29)]
        html = montar(pedidos)
        self.assertIn("Setembro em números", html)
        self.assertIn("Decisões recomendadas", html)
        self.assertEqual(html.count("<svg"), 6)


if __name__ == "__main__":
    unittest.main()
