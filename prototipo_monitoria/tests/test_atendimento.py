"""Testes da frente A: horários, atendimentos e exceções."""

import unittest
from datetime import date

from monitorias.dominio.atendimento import (
    Atendimento,
    AtendimentoOnline,
    AtendimentoPresencial,
)
from monitorias.dominio.excecoes import (
    ConflitoDeHorario,
    DadosInvalidos,
    ErroMonitorias,
)
from monitorias.dominio.horario import para_minutos, validar_codigo, validar_dia

DATA_FIXA = date(2026, 10, 20)


class TestHorario(unittest.TestCase):
    """Funções de horario.py."""

    def test_validar_dia_normaliza(self):
        self.assertEqual(validar_dia(" Terça "), "terça")

    def test_validar_dia_rejeita_dia_invalido(self):
        for dia in ("domingo", "terca-feira", ""):
            with self.subTest(dia=dia):
                with self.assertRaises(DadosInvalidos):
                    validar_dia(dia)

    def test_para_minutos_converte(self):
        self.assertEqual(para_minutos("14:30"), 870)
        self.assertEqual(para_minutos("9:05"), 545)
        self.assertEqual(para_minutos(" 00:00 "), 0)

    def test_para_minutos_rejeita_formato_e_valor_invalidos(self):
        for texto in ("14h30", "", "abc", "24:00", "10:60", "10:5"):
            with self.subTest(texto=texto):
                with self.assertRaises(DadosInvalidos):
                    para_minutos(texto)

    def test_validar_codigo_normaliza(self):
        self.assertEqual(validar_codigo(" dcc203 "), "DCC203")

    def test_validar_codigo_rejeita_formato_errado(self):
        for codigo in ("DC203", "DCC2033", "203DCC", ""):
            with self.subTest(codigo=codigo):
                with self.assertRaises(DadosInvalidos):
                    validar_codigo(codigo)


class TestCriacao(unittest.TestCase):
    """Validação feita pelos construtores."""

    def test_cria_presencial_valido_e_normaliza(self):
        a = AtendimentoPresencial(" Terça ", "9:00", "11:00", "CAD 3", "204",
                                  registrado_em=DATA_FIXA)
        self.assertEqual(a.dia, "terça")
        self.assertEqual(a.inicio, "09:00")
        self.assertEqual(a.fim, "11:00")
        self.assertEqual(a.registrado_em, DATA_FIXA)

    def test_data_de_registro_padrao_e_hoje(self):
        a = AtendimentoPresencial("segunda", "10:00", "11:00", "CAD 3", "204")
        self.assertEqual(a.registrado_em, date.today())

    def test_cria_online_com_parametros_nomeados(self):
        a = AtendimentoOnline("quinta", "19:00", "20:00",
                              plataforma="Google Meet", link="https://meet.exemplo/abc")
        self.assertEqual(a.plataforma, "Google Meet")
        self.assertEqual(a.link, "https://meet.exemplo/abc")

    def test_fim_antes_do_inicio_e_rejeitado(self):
        with self.assertRaises(DadosInvalidos):
            AtendimentoPresencial("terça", "16:00", "14:00", "CAD 3", "204")

    def test_inicio_igual_ao_fim_e_rejeitado(self):
        with self.assertRaises(DadosInvalidos):
            AtendimentoPresencial("terça", "14:00", "14:00", "CAD 3", "204")

    def test_dia_invalido_e_rejeitado(self):
        with self.assertRaises(DadosInvalidos):
            AtendimentoPresencial("domingo", "14:00", "16:00", "CAD 3", "204")

    def test_local_vazio_e_rejeitado(self):
        with self.assertRaises(DadosInvalidos):
            AtendimentoPresencial("terça", "14:00", "16:00", "   ", "204")
        with self.assertRaises(DadosInvalidos):
            AtendimentoOnline("terça", "14:00", "16:00", "", "https://meet.exemplo/abc")

    def test_link_sem_https_e_rejeitado(self):
        for link in ("http://meet.exemplo/abc", "meet.exemplo/abc"):
            with self.subTest(link=link):
                with self.assertRaises(DadosInvalidos):
                    AtendimentoOnline("terça", "14:00", "16:00", "Google Meet", link)

    def test_classe_abstrata_nao_pode_ser_criada(self):
        with self.assertRaises(TypeError):
            Atendimento("terça", "14:00", "16:00")

    def test_atributos_sao_somente_leitura(self):
        a = AtendimentoPresencial("terça", "14:00", "16:00", "CAD 3", "204")
        with self.assertRaises(AttributeError):
            a.inicio = "15:00"
        self.assertEqual(a.inicio, "14:00")


class TestSobreposicao(unittest.TestCase):
    """Regra sobrepoe(), herdada da classe abstrata."""

    def setUp(self):
        self.terca_14_16 = AtendimentoPresencial("terça", "14:00", "16:00", "ICEx", "1010")

    def test_horarios_que_se_cruzam_se_sobrepoem(self):
        terca_15_17 = AtendimentoPresencial("terça", "15:00", "17:00", "CAD 3", "204")
        self.assertTrue(self.terca_14_16.sobrepoe(terca_15_17))
        self.assertTrue(terca_15_17.sobrepoe(self.terca_14_16))

    def test_horario_contido_em_outro_se_sobrepoe(self):
        terca_14h30_15 = AtendimentoPresencial("terça", "14:30", "15:00", "CAD 3", "204")
        self.assertTrue(self.terca_14_16.sobrepoe(terca_14h30_15))

    def test_horarios_encostados_nao_se_sobrepoem(self):
        terca_16_18 = AtendimentoPresencial("terça", "16:00", "18:00", "CAD 3", "204")
        self.assertFalse(self.terca_14_16.sobrepoe(terca_16_18))
        self.assertFalse(terca_16_18.sobrepoe(self.terca_14_16))

    def test_dias_diferentes_nao_se_sobrepoem(self):
        quarta_14_16 = AtendimentoPresencial("quarta", "14:00", "16:00", "ICEx", "1010")
        self.assertFalse(self.terca_14_16.sobrepoe(quarta_14_16))

    def test_modalidades_diferentes_tambem_se_sobrepoem(self):
        online = AtendimentoOnline("terça", "15:00", "17:00", "Google Meet",
                                   "https://meet.exemplo/abc")
        self.assertTrue(self.terca_14_16.sobrepoe(online))


class TestPolimorfismo(unittest.TestCase):
    """Mesma chamada (local() e modalidade()) em duas classes concretas."""

    def setUp(self):
        self.atendimentos = [
            AtendimentoPresencial("terça", "10:00", "12:00", "CAD 3", "204"),
            AtendimentoOnline("quinta", "19:00", "20:00", "Google Meet",
                              "https://meet.exemplo/abc"),
        ]

    def test_mesma_chamada_resultados_conforme_a_subclasse(self):
        resultados = [(a.modalidade(), a.local()) for a in self.atendimentos]
        self.assertEqual(resultados, [
            ("presencial", "CAD 3, sala 204"),
            ("online", "Google Meet: https://meet.exemplo/abc"),
        ])

    def test_filtro_por_modalidade_sem_isinstance(self):
        online = [a for a in self.atendimentos if a.modalidade() == "online"]
        self.assertEqual(len(online), 1)
        self.assertEqual(online[0].local(), "Google Meet: https://meet.exemplo/abc")


class TestExcecoes(unittest.TestCase):
    """Hierarquia de exceções e mensagem do conflito."""

    def test_todas_herdam_de_erro_monitorias(self):
        self.assertTrue(issubclass(DadosInvalidos, ErroMonitorias))
        self.assertTrue(issubclass(ConflitoDeHorario, ErroMonitorias))

    def test_conflito_cita_horario_e_disciplina(self):
        from types import SimpleNamespace
        vinculo_falso = SimpleNamespace(disciplina=SimpleNamespace(codigo="MAT001"))
        existente = AtendimentoPresencial("terça", "14:00", "16:00", "ICEx", "1010")
        erro = ConflitoDeHorario(vinculo_falso, existente)
        self.assertEqual(
            str(erro),
            "Conflito de horário: o monitor já atende terça 14:00–16:00 em MAT001.",
        )
        self.assertIs(erro.atendimento, existente)


class TestEmailDoMonitor(unittest.TestCase):
    """Setter que valida (Monitor.email). Depende de monitor.py, da frente B."""

    def setUp(self):
        try:
            from monitorias.dominio.monitor import Monitor
        except ImportError:
            self.skipTest("monitor.py (frente B) ainda não foi entregue")
        self.monitor = Monitor("2026000001", "Ana Fictícia", "ana.ficticia@ufmg.br")

    def test_email_valido_e_aceito(self):
        self.monitor.email = "ana.nova@ufmg.br"
        self.assertEqual(self.monitor.email, "ana.nova@ufmg.br")

    def test_email_invalido_e_recusado_e_o_anterior_continua(self):
        with self.assertRaises(DadosInvalidos):
            self.monitor.email = "ana@gmail.com"
        self.assertEqual(self.monitor.email, "ana.ficticia@ufmg.br")


if __name__ == "__main__":
    unittest.main()