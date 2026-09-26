import unittest

from src.ia import analisar_sessao, prever_demanda


def sessao(numero, kwh, inicio, fim):
    return {
        "sessao_id": f"S-{numero}",
        "kwh_consumido": kwh,
        "inicio": inicio,
        "fim": fim,
        "status": "fechada",
    }


class TestIA(unittest.TestCase):
    def setUp(self):
        self.historico = [
            sessao(1, 10, "2026-06-01T18:00:00", "2026-06-01T20:00:00"),
            sessao(2, 12, "2026-06-02T18:30:00", "2026-06-02T20:30:00"),
            sessao(3, 11, "2026-06-03T19:00:00", "2026-06-03T21:00:00"),
            sessao(4, 13, "2026-06-04T17:30:00", "2026-06-04T20:00:00"),
            sessao(5, 9, "2026-06-05T18:00:00", "2026-06-05T19:45:00"),
        ]

    def test_potencia_impossivel_e_sinalizada(self):
        alvo = sessao(99, 65, "2026-06-10T12:00:00", "2026-06-10T13:00:00")
        resultado = analisar_sessao(alvo, self.historico, potencia_limite_kw=22)
        self.assertTrue(resultado.anomalia)
        self.assertGreaterEqual(resultado.score, 98)
        self.assertTrue(any("potência" in motivo.lower() for motivo in resultado.motivos))

    def test_sessao_fechada_sem_fim_e_sinalizada(self):
        alvo = sessao(100, 10, "2026-06-10T12:00:00", "")
        resultado = analisar_sessao(alvo, self.historico)
        self.assertTrue(resultado.anomalia)
        self.assertTrue(any("horário final" in motivo.lower() for motivo in resultado.motivos))

    def test_previsao_retorna_sete_dias(self):
        previsao = prever_demanda(self.historico, dias=7)
        self.assertEqual(len(previsao), 7)
        self.assertTrue(all(item["kwh_previsto"] > 0 for item in previsao))


if __name__ == "__main__":
    unittest.main()
