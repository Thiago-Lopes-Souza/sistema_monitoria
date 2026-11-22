"""Testes de A1, A2 e A3 integrados ao SQLite e às permissões do administrador.
Testes para cadastrar_disciplina(), cadastrar_monitor() e vincular(), além de
cenários de persistência, login, validações e proibição de operações por monitores.

Executar dentro de prototipo_monitoria/:
    python -m unittest discover -s tests -p 'test_admin.py' -v
"""

import unittest
from unittest import mock

from monitorias.dominio import senha
from monitorias.dominio.cadastro import CadastroMonitorias
from monitorias.dominio.disciplina import Disciplina
from monitorias.dominio.excecoes import (
    CredenciaisInvalidas,
    DadosInvalidos,
    DisciplinaForaDoEscopo,
    MatriculaNaoCadastrada,
    PermissaoNegada,
    RegistroDuplicado,
)
from monitorias.dominio.monitor import Monitor
from monitorias.persistencia.conexao import EM_MEMORIA, abrir_base
from monitorias.persistencia.repositorio import RepositorioMonitorias
from monitorias.persistencia.seed_demo import carregar_demo


class TestAdministracao(unittest.TestCase):
    """Cada caso usa um banco próprio; as alterações não vazam entre testes."""

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
        self.ana = self.cadastro.entrar("2026000001", "ana123")

    # ---- Os seis cenários administrativos do protótipo, agora com SQLite. ----

    def test_a1_disciplina_duplicada_e_rejeitada(self):
        antes = self.repositorio.buscar_disciplina("DCC203")

        with self.assertRaises(RegistroDuplicado):
            self.cadastro.cadastrar_disciplina(
                self.admin, "dcc203", "Outro nome"
            )

        depois = self.repositorio.buscar_disciplina("DCC203")
        self.assertEqual(depois.nome, antes.nome)

    def test_a2_matricula_duplicada_e_rejeitada(self):
        existente = self.repositorio.buscar_usuario("2026000001")

        with self.assertRaises(RegistroDuplicado):
            self.cadastro.cadastrar_monitor(
                self.admin,
                "2026000001", "Outra Ana", "outra@ufmg.br", "nova123",
            )

        gravado = self.repositorio.buscar_usuario("2026000001")
        self.assertEqual(gravado.nome, existente.nome)
        self.assertEqual(gravado.email, existente.email)
        # Uma matrícula duplicada não deve alterar a senha existente.
        self.assertEqual(
            self.cadastro.entrar("2026000001", "ana123").matricula,
            "2026000001",
        )

    def test_a3_criar_vinculo_e_persistir(self):
        # Ana está vinculada a DCC203 e MAT002, mas não a MAT001.
        vinculo = self.cadastro.vincular(self.admin, "2026000001", "MAT001")

        self.assertEqual(vinculo.monitor.matricula, "2026000001")
        self.assertEqual(vinculo.disciplina.codigo, "MAT001")
        self.assertEqual(vinculo.atendimentos, ())

        gravado = self.repositorio.buscar_vinculo("2026000001", "MAT001")
        self.assertIsNotNone(gravado)
        self.assertEqual(gravado.disciplina.codigo, "MAT001")

    def test_a3_vinculo_duplicado_e_rejeitado(self):
        # Ana já está vinculada a DCC203.
        with self.assertRaises(RegistroDuplicado):
            self.cadastro.vincular(self.admin, "2026000001", "dcc203")

        vinculos = self.repositorio.vinculos_do_monitor("2026000001")
        self.assertEqual(
            sum(v.disciplina.codigo == "DCC203" for v in vinculos), 1
        )

    def test_a3_monitor_nao_cadastrado(self):
        with self.assertRaises(MatriculaNaoCadastrada):
            self.cadastro.vincular(self.admin, "2099999999", "DCC203")

        self.assertIsNone(
            self.repositorio.buscar_vinculo("2099999999", "DCC203")
        )

    def test_a3_disciplina_fora_do_catalogo(self):
        with self.assertRaises(DisciplinaForaDoEscopo):
            self.cadastro.vincular(self.admin, "2026000001", "DCC999")

        self.assertIsNone(
            self.repositorio.buscar_vinculo("2026000001", "DCC999")
        )

    # ---- Novos testes necessários ao contrato final. ----

    def test_a1_cadastro_valido_persiste_e_normaliza(self):
        criada = self.cadastro.cadastrar_disciplina(
            self.admin, " inf123 ", "  Introdução à Computação  "
        )
        self.assertIsInstance(criada, Disciplina)
        self.assertEqual(criada.codigo, "INF123")
        self.assertEqual(criada.nome, "Introdução à Computação")

        salva = self.repositorio.buscar_disciplina("INF123")
        self.assertIsNotNone(salva)
        self.assertEqual(salva.nome, criada.nome)

    def test_a2_cadastro_valido_persiste_e_permite_login(self):
        criado = self.cadastro.cadastrar_monitor(
            self.admin, "2026999999", "  Pedro Teste  ",
            "  PEDRO@UFMG.BR  ", "pedro123",
        )
        self.assertIsInstance(criado, Monitor)
        self.assertEqual(criado.nome, "Pedro Teste")
        self.assertEqual(criado.email, "pedro@ufmg.br")

        gravado = self.repositorio.buscar_usuario("2026999999")
        self.assertIsInstance(gravado, Monitor)
        self.assertEqual(gravado.email, "pedro@ufmg.br")
        self.assertEqual(
            self.cadastro.entrar("2026999999", "pedro123").matricula,
            "2026999999",
        )
        with self.assertRaises(CredenciaisInvalidas):
            self.cadastro.entrar("2026999999", "senha_errada")

        hash_senha, sal = self.repositorio.buscar_credenciais("2026999999")
        self.assertIsInstance(hash_senha, bytes)
        self.assertIsInstance(sal, bytes)
        self.assertNotEqual(hash_senha, b"pedro123")
        self.assertTrue(sal)

    def test_a3_aceita_dados_normalizados(self):
        vinculo = self.cadastro.vincular(
            self.admin, " 2026000001 ", " mat001 "
        )
        self.assertEqual(vinculo.monitor.matricula, "2026000001")
        self.assertEqual(vinculo.disciplina.codigo, "MAT001")

    def test_a1_codigo_invalido_nao_grava(self):
        antes = self.repositorio.listar_disciplinas()
        with self.assertRaises(DadosInvalidos):
            self.cadastro.cadastrar_disciplina(
                self.admin, "codigo-errado", "Disciplina"
            )
        self.assertEqual(self.repositorio.listar_disciplinas(), antes)

    def test_a2_email_invalido_nao_grava(self):
        with self.assertRaises(DadosInvalidos):
            self.cadastro.cadastrar_monitor(
                self.admin, "2026999999", "Pedro", "pedro@gmail.com", "pedro123"
            )
        self.assertIsNone(self.repositorio.buscar_usuario("2026999999"))

    def test_a2_senha_vazia_nao_grava(self):
        with self.assertRaises(DadosInvalidos):
            self.cadastro.cadastrar_monitor(
                self.admin, "2026999999", "Pedro", "pedro@ufmg.br", ""
            )
        self.assertIsNone(self.repositorio.buscar_usuario("2026999999"))

    def test_a1_monitor_sem_permissao(self):
        with self.assertRaises(PermissaoNegada):
            self.cadastro.cadastrar_disciplina(
                self.ana, "INF123", "Introdução à Computação"
            )
        self.assertIsNone(self.repositorio.buscar_disciplina("INF123"))

    def test_a2_monitor_sem_permissao(self):
        with self.assertRaises(PermissaoNegada):
            self.cadastro.cadastrar_monitor(
                self.ana, "2026999999", "Pedro", "pedro@ufmg.br", "pedro123"
            )
        self.assertIsNone(self.repositorio.buscar_usuario("2026999999"))

    def test_a3_monitor_sem_permissao(self):
        with self.assertRaises(PermissaoNegada):
            self.cadastro.vincular(self.ana, "2026000001", "MAT001")
        self.assertIsNone(
            self.repositorio.buscar_vinculo("2026000001", "MAT001")
        )


if __name__ == "__main__":
    unittest.main()
