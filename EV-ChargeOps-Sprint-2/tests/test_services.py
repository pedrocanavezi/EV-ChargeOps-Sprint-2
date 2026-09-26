import tempfile
import unittest
from pathlib import Path

from src.database import Banco
from src.services import importar_csv_texto, processar_sessao


class TestServices(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory()
        self.banco = Banco(Path(self.pasta.name) / "teste.db")
        self.banco.criar_tabelas()

    def tearDown(self):
        self.pasta.cleanup()

    def test_registro_recalcula_total(self):
        sessao = processar_sessao(
            self.banco,
            {
                "sessao_id": "T-001",
                "local": "Condominio",
                "carregador": "EVSE-01",
                "usuario": "Teste",
                "inicio": "2026-09-19T10:00:00",
                "fim": "2026-09-19T12:00:00",
                "kwh_consumido": 18.4,
                "tarifa_kwh": 0.92,
                "taxa_fixa": 2,
                "percentual_operacional": 0.12,
                "status": "fechada",
            },
        )
        self.assertEqual(sessao["valor_total"], 20.96)
        self.assertEqual(self.banco.quantidade(), 1)

    def test_csv_ignora_total_informado_e_recalcula(self):
        conteudo = """sessao_id,local,carregador,usuario,inicio,fim,kwh_consumido,tarifa_kwh,taxa_fixa,percentual_operacional,desconto,total_calculado,status
T-CSV,Condominio,EVSE-01,Ana,2026-09-19T10:00:00,2026-09-19T12:00:00,6.1,1.35,3,0.15,0,9999,fechada
"""
        resultado = importar_csv_texto(self.banco, conteudo)
        self.assertEqual(resultado["erros"], [])
        salva = self.banco.buscar_sessao("T-CSV")
        self.assertEqual(salva["valor_total"], 12.48)


if __name__ == "__main__":
    unittest.main()

