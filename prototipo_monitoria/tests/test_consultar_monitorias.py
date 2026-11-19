"""Testes da F2 (consultar monitorias de uma disciplina)."""

import dataclasses
import unittest
from datetime import date

from monitorias.dominio.atendimento import AtendimentoOnline, AtendimentoPresencial
from monitorias.dominio.cadastro import CadastroMonitorias
from monitorias.dominio.consulta import SituacaoConsulta
from monitorias.dominio.disciplina import Disciplina
from monitorias.dominio.excecoes import DadosInvalidos, DisciplinaForaDoEscopo
from monitorias.dominio.monitor import Monitor

DATA = date(2026, 10, 1)


class TestConsultarMonitorias(unittest.TestCase):
    def setUp(self):
        self.cadastro = CadastroMonitorias()
        for codigo, nome in [
            ("AAA111", "Disciplina A"),
            ("BBB222", "Disciplina B"),
            ("CCC333", "Disciplina C"),
            ("DDD444", "Disciplina D"),
        ]:
            self.cadastro.adicionar_disciplina(Disciplina(codigo, nome))
        for matricula, nome, email in [
            ("1", "Bia Teste", "bia.teste@ufmg.br"),
            ("2", "Davi Teste", "davi.teste@ufmg.br"),
            ("3", "Eva Teste", "eva.teste@ufmg.br"),
            ("4", "Fabio Teste", "fabio.teste@ufmg.br"),
            ("5", "Gabi Teste", "gabi.teste@ufmg.br"),
        ]:
            self.cadastro.adicionar_monitor(Monitor(matricula, nome, email))

        self.v_bia = self.cadastro.vincular("1", "AAA111")
        self.v_davi = self.cadastro.vincular("2", "AAA111")
        self.v_eva = self.cadastro.vincular("3", "BBB222")
        self.v_fabio = self.cadastro.vincular("4", "CCC333")
        self.v_gabi = self.cadastro.vincular("5", "CCC333")

        self.h_bia_quinta = AtendimentoPresencial(
            "quinta", "14:00", "16:00", "Predio X", "10", registrado_em=DATA
        )
        self.h_bia_terca = AtendimentoOnline(
            "terça", "09:00", "10:00", "Meet", "https://meet.exemplo/bia", registrado_em=DATA
        )
        self.v_bia.adicionar_atendimento(self.h_bia_quinta)
        self.v_bia.adicionar_atendimento(self.h_bia_terca)

        self.h_davi = AtendimentoPresencial(
            "segunda", "08:00", "10:00", "Predio Y", "20", registrado_em=DATA
        )
        self.v_davi.adicionar_atendimento(self.h_davi)

        self.h_fabio = AtendimentoPresencial(
            "sexta", "10:00", "11:00", "Predio Z", "30", registrado_em=DATA
        )
        self.v_fabio.adicionar_atendimento(self.h_fabio)

        self.todos_vinculos = [self.v_bia, self.v_davi, self.v_eva, self.v_fabio, self.v_gabi]

    def _foto(self):
        return (
            [v.atendimentos for v in self.todos_vinculos],
            [d.codigo for d in self.cadastro.listar_disciplinas()],
        )

    def _assert_nao_alterou(self, antes):
        self.assertEqual(antes, self._foto())

    def test_f2_01_sem_filtro_lista_monitores_e_horarios_ordenados(self):
        antes = self._foto()
        r = self.cadastro.consultar_monitorias("AAA111")

        self.assertEqual(r.disciplina.codigo, "AAA111")
        self.assertEqual(r.situacao, SituacaoConsulta.COM_HORARIOS)
        self.assertIsNone(r.modalidade)
        self.assertEqual([i.monitor.nome for i in r.itens], ["Bia Teste", "Davi Teste"])
        self.assertEqual(r.itens[0].atendimentos, (self.h_bia_terca, self.h_bia_quinta))
        self.assertEqual(r.itens[1].atendimentos, (self.h_davi,))
        self._assert_nao_alterou(antes)

    def test_f2_02_filtro_online_mostra_so_horarios_online(self):
        r = self.cadastro.consultar_monitorias("AAA111", "online")

        self.assertEqual(r.situacao, SituacaoConsulta.COM_HORARIOS)
        self.assertEqual([i.monitor.nome for i in r.itens], ["Bia Teste"])
        self.assertEqual(r.itens[0].atendimentos, (self.h_bia_terca,))

    def test_f2_03_filtro_por_dia_mostra_so_horarios_do_dia(self):
        antes = self._foto()
        r = self.cadastro.consultar_monitorias("AAA111", dia="terça")

        self.assertEqual(r.situacao, SituacaoConsulta.COM_HORARIOS)
        self.assertEqual(r.dia, "terça")
        self.assertEqual([i.monitor.nome for i in r.itens], ["Bia Teste"])
        self.assertEqual(r.itens[0].atendimentos, (self.h_bia_terca,))
        self._assert_nao_alterou(antes)

    def test_f2_04_filtro_por_dia_sem_atendimento_nesse_dia(self):
        antes = self._foto()
        r = self.cadastro.consultar_monitorias("AAA111", dia="sexta")

        self.assertEqual(r.situacao, SituacaoConsulta.SEM_HORARIOS_NA_MODALIDADE)
        self.assertEqual(r.dia, "sexta")
        self.assertEqual(r.itens, ())
        self._assert_nao_alterou(antes)

    def test_f2_05_modalidade_e_dia_combinados(self):
        antes = self._foto()
        r = self.cadastro.consultar_monitorias("AAA111", "presencial", "quinta")
        self.assertEqual(r.situacao, SituacaoConsulta.COM_HORARIOS)
        self.assertEqual([i.monitor.nome for i in r.itens], ["Bia Teste"])
        self.assertEqual(r.itens[0].atendimentos, (self.h_bia_quinta,))

        r = self.cadastro.consultar_monitorias("AAA111", "online", "quinta")
        self.assertEqual(r.situacao, SituacaoConsulta.SEM_HORARIOS_NA_MODALIDADE)
        self.assertEqual((r.modalidade, r.dia), ("online", "quinta"))
        self._assert_nao_alterou(antes)

    def test_f2_06_sem_filtro_monitor_sem_horario_tambem_aparece(self):
        antes = self._foto()
        r = self.cadastro.consultar_monitorias("CCC333")

        self.assertEqual(r.situacao, SituacaoConsulta.COM_HORARIOS)
        self.assertEqual([i.monitor.nome for i in r.itens], ["Fabio Teste", "Gabi Teste"])
        self.assertEqual(r.itens[0].atendimentos, (self.h_fabio,))
        self.assertEqual(r.itens[1].atendimentos, ())
        self._assert_nao_alterou(antes)

    def test_f2_07_monitores_sem_nenhum_horario(self):
        antes = self._foto()
        r = self.cadastro.consultar_monitorias("BBB222")

        self.assertEqual(r.situacao, SituacaoConsulta.MONITOR_SEM_HORARIOS)
        self.assertEqual(len(r.itens), 1)
        self.assertEqual(r.itens[0].monitor.email, "eva.teste@ufmg.br")
        self.assertEqual(r.itens[0].atendimentos, ())
        self._assert_nao_alterou(antes)

    def test_f2_08_modalidade_sem_horarios(self):
        antes = self._foto()
        r = self.cadastro.consultar_monitorias("CCC333", "online")

        self.assertEqual(r.situacao, SituacaoConsulta.SEM_HORARIOS_NA_MODALIDADE)
        self.assertEqual(r.modalidade, "online")
        self.assertEqual(r.itens, ())
        self._assert_nao_alterou(antes)

    def test_f2_09_nenhuma_monitoria_cadastrada(self):
        antes = self._foto()
        r = self.cadastro.consultar_monitorias("DDD444")

        self.assertEqual(r.situacao, SituacaoConsulta.NENHUMA_MONITORIA_CADASTRADA)
        self.assertEqual(r.itens, ())
        self.assertEqual(r.disciplina.codigo, "DDD444")
        self._assert_nao_alterou(antes)

    def test_f2_10_codigo_fora_do_catalogo_e_rejeitado_sem_alterar_nada(self):
        antes = self._foto()
        with self.assertRaises(DisciplinaForaDoEscopo):
            self.cadastro.consultar_monitorias("DCC999")
        self._assert_nao_alterou(antes)

    def test_f2_11_codigo_mal_formatado_e_rejeitado_sem_alterar_nada(self):
        antes = self._foto()
        for ruim in ["", "AA111", "AAAA111", "AAA11", "123ABC", "AAA 111"]:
            with self.subTest(codigo=ruim):
                with self.assertRaises(DadosInvalidos):
                    self.cadastro.consultar_monitorias(ruim)
        self._assert_nao_alterou(antes)

    def test_f2_12_modalidade_desconhecida_e_rejeitada_sem_alterar_nada(self):
        antes = self._foto()
        with self.assertRaises(DadosInvalidos):
            self.cadastro.consultar_monitorias("AAA111", "hibrida")
        self._assert_nao_alterou(antes)

    def test_f2_13_dia_invalido_e_rejeitado_sem_alterar_nada(self):
        antes = self._foto()
        for ruim in ["domingo", "xyz", "13"]:
            with self.subTest(dia=ruim):
                with self.assertRaises(DadosInvalidos):
                    self.cadastro.consultar_monitorias("AAA111", dia=ruim)
        self._assert_nao_alterou(antes)

    def test_f2_14_formato_e_checado_antes_do_catalogo(self):
        with self.assertRaises(DadosInvalidos):
            self.cadastro.consultar_monitorias("DCC999", "hibrida")
        with self.assertRaises(DadosInvalidos):
            self.cadastro.consultar_monitorias("DCC999", dia="domingo")

    def test_f2_15_consultar_varias_vezes_nao_muda_dados(self):
        antes = self._foto()
        for codigo in ["AAA111", "BBB222", "CCC333", "DDD444"]:
            for modalidade in [None, "online", "presencial"]:
                for dia in [None, "terça", "sexta"]:
                    self.cadastro.consultar_monitorias(codigo, modalidade, dia)
        self._assert_nao_alterou(antes)

    def test_local_e_modalidade_vem_de_cada_subclasse(self):
        r = self.cadastro.consultar_monitorias("AAA111")
        terca, quinta = r.itens[0].atendimentos
        self.assertEqual(terca.modalidade(), "online")
        self.assertEqual(terca.local(), "Meet: https://meet.exemplo/bia")
        self.assertEqual(quinta.modalidade(), "presencial")
        self.assertEqual(quinta.local(), "Predio X, sala 10")

    def test_com_filtro_monitor_sem_horario_na_modalidade_nao_aparece(self):
        r = self.cadastro.consultar_monitorias("CCC333", "presencial")
        self.assertEqual([i.monitor.nome for i in r.itens], ["Fabio Teste"])

    def test_filtro_presencial_mostra_so_horarios_presenciais(self):
        r = self.cadastro.consultar_monitorias("AAA111", "presencial")

        self.assertEqual(r.situacao, SituacaoConsulta.COM_HORARIOS)
        self.assertEqual(r.itens[0].atendimentos, (self.h_bia_quinta,))
        self.assertEqual(r.itens[1].atendimentos, (self.h_davi,))

    def test_modalidade_vazia_ou_none_equivale_a_todas(self):
        sem_filtro = self.cadastro.consultar_monitorias("AAA111")
        for vazio in ("", "  ", None):
            with self.subTest(modalidade=vazio):
                self.assertEqual(
                    self.cadastro.consultar_monitorias("AAA111", vazio), sem_filtro
                )

    def test_modalidade_aceita_maiusculas_e_espacos(self):
        r = self.cadastro.consultar_monitorias("AAA111", "  ONLINE ")
        self.assertEqual(r.modalidade, "online")
        self.assertEqual(r.itens[0].atendimentos, (self.h_bia_terca,))

    def test_dia_aceita_maiusculas_espacos_e_vazio(self):
        r = self.cadastro.consultar_monitorias("AAA111", dia="  TERÇA ")
        self.assertEqual(r.dia, "terça")
        self.assertEqual(r.itens[0].atendimentos, (self.h_bia_terca,))

        sem_filtro = self.cadastro.consultar_monitorias("AAA111")
        for vazio in ("", "  ", None):
            with self.subTest(dia=vazio):
                self.assertEqual(
                    self.cadastro.consultar_monitorias("AAA111", dia=vazio), sem_filtro
                )

    def test_codigo_em_minusculas_e_com_espacos_e_aceito(self):
        r = self.cadastro.consultar_monitorias("  aaa111 ")
        self.assertEqual(r.disciplina.codigo, "AAA111")
        self.assertEqual(r.situacao, SituacaoConsulta.COM_HORARIOS)

    def test_resultado_e_imutavel(self):
        r = self.cadastro.consultar_monitorias("AAA111")
        with self.assertRaises(dataclasses.FrozenInstanceError):
            r.situacao = SituacaoConsulta.MONITOR_SEM_HORARIOS
        self.assertIsInstance(r.itens, tuple)
        self.assertIsInstance(r.itens[0].atendimentos, tuple)

    def test_listar_disciplinas_ordenado_por_codigo(self):
        codigos = [d.codigo for d in self.cadastro.listar_disciplinas()]
        self.assertEqual(codigos, ["AAA111", "BBB222", "CCC333", "DDD444"])
        self.assertIsInstance(self.cadastro.listar_disciplinas(), tuple)


if __name__ == "__main__":
    unittest.main()
