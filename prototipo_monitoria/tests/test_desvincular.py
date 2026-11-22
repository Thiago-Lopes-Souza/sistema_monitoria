"""Testes da A4: desvincular monitor de disciplina."""

import unittest
from unittest import mock

from monitorias.dominio import senha
from monitorias.dominio.cadastro import CadastroMonitorias
from monitorias.dominio.consulta import SituacaoConsulta
from monitorias.dominio.excecoes import (
    DadosInvalidos, DisciplinaForaDoEscopo, MatriculaNaoCadastrada,
    PermissaoNegada, VinculoInexistente)
from monitorias.dominio.usuario import Aluno
from monitorias.persistencia.conexao import EM_MEMORIA, abrir_base
from monitorias.persistencia.repositorio import RepositorioMonitorias
from monitorias.persistencia.seed_demo import carregar_demo

ANA = "2026000001"
CAIO = "2026000002"


class TestDesvincular(unittest.TestCase):

    def setUp(self):
        patch = mock.patch.object(senha, "ITERACOES", 1_000)
        patch.start()
        self.addCleanup(patch.stop)

        self.conexao = abrir_base(EM_MEMORIA)
        self.addCleanup(self.conexao.close)
        self.repositorio = RepositorioMonitorias(self.conexao)
        carregar_demo(self.repositorio)
        self.cadastro = CadastroMonitorias(self.repositorio)

        self.admin = self.cadastro.entrar("2026900001", "admin123")
        self.ana = self.cadastro.entrar(ANA, "ana123")

    def _foto(self):
        vinculos = self.conexao.execute(
            "SELECT * FROM vinculos ORDER BY matricula, codigo").fetchall()
        atendimentos = self.conexao.execute(
            "SELECT * FROM atendimentos ORDER BY id").fetchall()
        return ([tuple(v) for v in vinculos], [tuple(a) for a in atendimentos])

    def _dias(self, matricula, codigo):
        vinculo = self.repositorio.buscar_vinculo(matricula, codigo)
        return [a.dia for a in vinculo.atendimentos]

    def test_a4_01_desvincula_quem_atende_em_duas_disciplinas(self):
        antes = self._foto()

        removidos = self.cadastro.desvincular(self.admin, ANA, "MAT002")

        self.assertEqual(removidos, 1)
        self.assertIsNone(self.repositorio.buscar_vinculo(ANA, "MAT002"))
        self.assertEqual(self._dias(ANA, "DCC203"), ["terça"])
        depois_v, depois_a = self._foto()
        self.assertEqual(depois_v, [v for v in antes[0] if v[:2] != (ANA, "MAT002")])
        self.assertEqual(depois_a, [a for a in antes[1] if a[1:3] != (ANA, "MAT002")])

    def test_a4_02_so_apaga_os_horarios_daquele_vinculo(self):
        antes = self._foto()
        removidos = self.cadastro.desvincular(self.admin, CAIO, "MAT001")

        self.assertEqual(removidos, 2)
        self.assertIsNone(self.repositorio.buscar_vinculo(CAIO, "MAT001"))
        self.assertIsNotNone(self.repositorio.buscar_vinculo(CAIO, "DCC203"))
        self.assertEqual(self._dias(ANA, "DCC203"), ["terça"])
        self.assertEqual(self._dias(ANA, "MAT002"), ["quarta"])
        self.assertEqual(len(self._foto()[1]), len(antes[1]) - 2)

    def test_a4_03_vinculo_sem_horarios(self):
        removidos = self.cadastro.desvincular(self.admin, CAIO, "DCC203")

        self.assertEqual(removidos, 0)
        self.assertIsNone(self.repositorio.buscar_vinculo(CAIO, "DCC203"))
        self.assertIsNotNone(self.repositorio.buscar_vinculo(CAIO, "MAT001"))

    def test_a4_04_vinculo_inexistente_e_rejeitado(self):
        antes = self._foto()
        with self.assertRaises(VinculoInexistente):
            self.cadastro.desvincular(self.admin, ANA, "MAT001")
        self.assertEqual(self._foto(), antes)

    def test_a4_05_monitor_nao_cadastrado_e_rejeitado(self):
        antes = self._foto()
        with self.assertRaises(MatriculaNaoCadastrada):
            self.cadastro.desvincular(self.admin, "2099999999", "DCC203")
        with self.assertRaises(MatriculaNaoCadastrada):
            self.cadastro.desvincular(self.admin, "2026900001", "DCC203")
        self.assertEqual(self._foto(), antes)

    def test_a4_06_disciplina_fora_do_catalogo_e_rejeitada(self):
        antes = self._foto()
        with self.assertRaises(DisciplinaForaDoEscopo):
            self.cadastro.desvincular(self.admin, ANA, "DCC999")
        self.assertEqual(self._foto(), antes)

    def test_a4_07_entradas_mal_formatadas_sao_rejeitadas(self):
        antes = self._foto()
        for codigo in ["", "AA111", "AAA 111", None, 7]:
            with self.subTest(codigo=codigo):
                with self.assertRaises(DadosInvalidos):
                    self.cadastro.desvincular(self.admin, ANA, codigo)
        for matricula in [None, 2026000001]:
            with self.subTest(matricula=matricula):
                with self.assertRaises(DadosInvalidos):
                    self.cadastro.desvincular(self.admin, matricula, "DCC203")
        self.assertEqual(self._foto(), antes)

    def test_a4_08_monitor_nao_pode_desvincular(self):
        antes = self._foto()
        with self.assertRaises(PermissaoNegada):
            self.cadastro.desvincular(self.ana, ANA, "MAT002")
        self.assertEqual(self._foto(), antes)

    def test_a4_09_quem_nao_e_administrador_e_recusado(self):
        antes = self._foto()
        for usuario in [Aluno(), None, "2026900001"]:
            with self.subTest(usuario=usuario):
                with self.assertRaises(PermissaoNegada):
                    self.cadastro.desvincular(usuario, ANA, "MAT002")
        self.assertEqual(self._foto(), antes)

    def test_a4_10_falha_no_meio_desfaz_tudo(self):
        antes = self._foto()
        real = self.repositorio.excluir_vinculo

        def apaga_e_falha(matricula, codigo):
            real(matricula, codigo)
            raise RuntimeError("falha simulada")

        with mock.patch.object(self.repositorio, "excluir_vinculo", apaga_e_falha):
            with self.assertRaises(RuntimeError):
                self.cadastro.desvincular(self.admin, CAIO, "MAT001")
        self.assertEqual(self._foto(), antes)

    def test_a4_11_matricula_e_codigo_sao_normalizados(self):
        removidos = self.cadastro.desvincular(self.admin, f"  {ANA} ", " mat002 ")
        self.assertEqual(removidos, 1)
        self.assertIsNone(self.repositorio.buscar_vinculo(ANA, "MAT002"))

    def test_a4_12_desvincular_duas_vezes_rejeita_a_segunda(self):
        self.cadastro.desvincular(self.admin, ANA, "MAT002")
        antes = self._foto()
        with self.assertRaises(VinculoInexistente):
            self.cadastro.desvincular(self.admin, ANA, "MAT002")
        self.assertEqual(self._foto(), antes)

    def test_a4_13_monitor_desvinculado_nao_cadastra_horario_na_disciplina(self):
        self.cadastro.desvincular(self.admin, ANA, "MAT002")
        antes = self._foto()
        with self.assertRaises(VinculoInexistente):
            self.cadastro.cadastrar_presencial(
                self.ana, "MAT002", "sexta", "08:00", "10:00", "ICEx", "1")
        self.assertEqual(self._foto(), antes)

    def test_a4_14_vincular_de_novo_nao_traz_os_horarios_de_volta(self):
        self.cadastro.desvincular(self.admin, ANA, "MAT002")
        vinculo = self.cadastro.vincular(self.admin, ANA, "MAT002")
        self.assertEqual(vinculo.atendimentos, ())

    def test_a4_15_consulta_reflete_o_desvinculo(self):
        antes = self.cadastro.consultar_monitorias("MAT002")
        self.assertEqual(antes.situacao, SituacaoConsulta.COM_HORARIOS)

        self.cadastro.desvincular(self.admin, ANA, "MAT002")

        depois = self.cadastro.consultar_monitorias("MAT002")
        self.assertEqual(depois.situacao, SituacaoConsulta.NENHUMA_MONITORIA_CADASTRADA)
        dcc = self.cadastro.consultar_monitorias("DCC203")
        self.assertIn(ANA, [i.monitor.matricula for i in dcc.itens])


if __name__ == "__main__":
    unittest.main()
