import unittest

from src.rateio import calcular_rateio


class TestRateio(unittest.TestCase):
    def test_calculo_com_taxa_fixa_e_percentual(self):
        resultado = calcular_rateio(18.4, 0.92, 2.0, 0.12, 0, "fechada")
        self.assertEqual(float(resultado.valor_energia), 16.93)
        self.assertEqual(float(resultado.valor_percentual), 2.03)
        self.assertEqual(float(resultado.valor_taxa), 4.03)
        self.assertEqual(float(resultado.valor_total), 20.96)

    def test_arredondamento_financeiro(self):
        resultado = calcular_rateio(6.1, 1.35, 3.0, 0.15, 0, "fechada")
        self.assertEqual(float(resultado.valor_energia), 8.24)
        self.assertEqual(float(resultado.valor_total), 12.48)

    def test_sessao_pendente_nao_e_cobrada(self):
        resultado = calcular_rateio(12, 0.92, 2, 0.12, 0, "pendente")
        self.assertFalse(resultado.faturavel)
        self.assertEqual(float(resultado.valor_total), 0)

    def test_desconto_nao_cria_total_negativo(self):
        resultado = calcular_rateio(1, 1, 0, 0, 50, "fechada")
        self.assertEqual(float(resultado.valor_total), 0)

    def test_percentual_deve_ser_decimal(self):
        with self.assertRaises(ValueError):
            calcular_rateio(10, 1, 0, 12, 0, "fechada")


if __name__ == "__main__":
    unittest.main()

