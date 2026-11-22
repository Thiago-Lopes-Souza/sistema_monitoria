"""Testes dos perfis de usuário e das permissões."""

import unittest

from monitorias.dominio.excecoes import DadosInvalidos
from monitorias.dominio.monitor import Monitor
from monitorias.dominio.usuario import (
    OPERACOES_ADMINISTRADOR,
    OPERACOES_ALUNO,
    OPERACOES_MONITOR,
    Administrador,
    Aluno,
    Operacao,
    Usuario,
    UsuarioCadastrado,
)


class TestPermissoes(unittest.TestCase):

    def setUp(self):
        self.aluno = Aluno()
        self.monitor = Monitor(
            "1", "Monitor Teste", "monitor.teste@ufmg.br"
        )
        self.admin = Administrador(
            "2", "Admin Teste", "admin.teste@ufmg.br"
        )

    def test_aluno_so_pode_consultar(self):
        for operacao in Operacao:
            with self.subTest(operacao=operacao):
                esperado = operacao is Operacao.CONSULTAR_MONITORIAS
                self.assertEqual(
                    self.aluno.pode(operacao), esperado
                )

    def test_monitor_pode_consultar_e_cuidar_dos_proprios_horarios(self):
        permitidas = {
            Operacao.CONSULTAR_MONITORIAS,
            Operacao.CADASTRAR_HORARIO,
            Operacao.VISUALIZAR_HORARIOS,
            Operacao.ALTERAR_HORARIO,
            Operacao.REMOVER_ATENDIMENTO,
        }

        for operacao in Operacao:
            with self.subTest(operacao=operacao):
                self.assertEqual(
                    self.monitor.pode(operacao),
                    operacao in permitidas
                )

    def test_administrador_pode_consultar_e_administrar(self):
        permitidas = {
            Operacao.CONSULTAR_MONITORIAS,
            Operacao.CADASTRAR_DISCIPLINA,
            Operacao.CADASTRAR_MONITOR,
            Operacao.VINCULAR,
            Operacao.DESVINCULAR,
        }

        for operacao in Operacao:
            with self.subTest(operacao=operacao):
                self.assertEqual(
                    self.admin.pode(operacao),
                    operacao in permitidas
                )

    def test_administrador_nao_gerencia_horarios_de_terceiros(self):
        for operacao in (
            Operacao.CADASTRAR_HORARIO,
            Operacao.VISUALIZAR_HORARIOS,
            Operacao.ALTERAR_HORARIO,
            Operacao.REMOVER_ATENDIMENTO,
        ):
            with self.subTest(operacao=operacao):
                self.assertFalse(self.admin.pode(operacao))

    def test_todo_perfil_pode_consultar(self):
        for usuario in (
            self.aluno, self.monitor, self.admin
        ):
            with self.subTest(perfil=type(usuario).__name__):
                self.assertTrue(
                    usuario.pode(Operacao.CONSULTAR_MONITORIAS)
                )

    def test_mesma_chamada_responde_diferente_em_cada_perfil(self):
        usuarios = [
            self.aluno, self.monitor, self.admin
        ]

        self.assertEqual(
            [u.pode(Operacao.VINCULAR) for u in usuarios],
            [False, False, True]
        )

        self.assertEqual(
            [
                u.pode(Operacao.CADASTRAR_HORARIO)
                for u in usuarios
            ],
            [False, True, False]
        )

    def test_valor_que_nao_e_operacao_nunca_e_permitido(self):
        for usuario in (
            self.aluno, self.monitor, self.admin
        ):
            with self.subTest(perfil=type(usuario).__name__):
                self.assertFalse(usuario.pode("vincular"))
                self.assertFalse(usuario.pode(None))

    def test_opcoes_do_menu_batem_com_as_permissoes(self):
        for usuario in (
            self.aluno, self.monitor, self.admin
        ):
            opcoes = usuario.opcoes_menu()

            for operacao in Operacao:
                with self.subTest(
                    perfil=type(usuario).__name__,
                    operacao=operacao
                ):
                    self.assertEqual(
                        operacao in opcoes,
                        usuario.pode(operacao)
                    )

    def test_opcoes_do_menu_na_ordem_da_tabela(self):
        self.assertEqual(
            self.aluno.opcoes_menu(), OPERACOES_ALUNO
        )
        self.assertEqual(
            self.monitor.opcoes_menu(), OPERACOES_MONITOR
        )
        self.assertEqual(
            self.admin.opcoes_menu(),
            OPERACOES_ADMINISTRADOR
        )

    def test_opcoes_do_menu_sao_somente_leitura(self):
        opcoes = self.admin.opcoes_menu()

        self.assertIsInstance(opcoes, tuple)

        with self.assertRaises(AttributeError):
            opcoes.append(Operacao.CADASTRAR_HORARIO)

        self.assertEqual(
            self.admin.opcoes_menu(),
            OPERACOES_ADMINISTRADOR
        )

    def test_usuario_e_usuario_cadastrado_sao_abstratas(self):
        with self.assertRaises(TypeError):
            Usuario()

        with self.assertRaises(TypeError):
            UsuarioCadastrado(
                "1", "Fulano", "fulano@ufmg.br"
            )

    def test_perfis_concretos_sao_usuarios(self):
        for usuario in (
            self.aluno, self.monitor, self.admin
        ):
            self.assertIsInstance(usuario, Usuario)

        # Monitor e Administrador são usuários cadastrados.
        self.assertIsInstance(
            self.monitor, UsuarioCadastrado
        )
        self.assertIsInstance(
            self.admin, UsuarioCadastrado
        )

        # Aluno não precisa de cadastro.
        self.assertNotIsInstance(
            self.aluno, UsuarioCadastrado
        )


class TestUsuarioCadastrado(unittest.TestCase):

    def setUp(self):
        self.admin = Administrador(
            "  2026999  ",
            "  Admin Teste ",
            "  Admin.Teste@UFMG.br "
        )

    def test_dados_sao_normalizados(self):
        self.assertEqual(
            self.admin.matricula, "2026999"
        )
        self.assertEqual(
            self.admin.nome, "Admin Teste"
        )
        self.assertEqual(
            self.admin.email, "admin.teste@ufmg.br"
        )

    def test_matricula_vazia_e_rejeitada(self):
        for ruim in ("", "   "):
            with self.subTest(matricula=ruim):
                with self.assertRaises(DadosInvalidos):
                    Administrador(
                        ruim, "Nome", "nome@ufmg.br"
                    )

    def test_nome_vazio_e_rejeitado(self):
        for ruim in ("", "   "):
            with self.subTest(nome=ruim):
                with self.assertRaises(DadosInvalidos):
                    Administrador(
                        "1", ruim, "nome@ufmg.br"
                    )

    def test_email_nao_institucional_e_rejeitado_na_criacao(self):
        for ruim in (
            "",
            "   ",
            "nome@gmail.com",
            "nome@ufmg.com",
            "ufmg.br",
        ):
            with self.subTest(email=ruim):
                with self.assertRaises(DadosInvalidos):
                    Administrador(
                        "1", "Nome", ruim
                    )

    def test_setter_troca_o_email_quando_valido(self):
        self.admin.email = "Novo.Email@ufmg.br"

        self.assertEqual(
            self.admin.email, "novo.email@ufmg.br"
        )

    def test_setter_rejeitado_mantem_o_email_anterior(self):
        antes = self.admin.email

        for ruim in (
            "", "x@gmail.com", "x@ufmg.com"
        ):
            with self.subTest(email=ruim):
                with self.assertRaises(DadosInvalidos):
                    self.admin.email = ruim

                self.assertEqual(
                    self.admin.email, antes
                )

    def test_matricula_e_nome_sao_somente_leitura(self):
        with self.assertRaises(AttributeError):
            self.admin.matricula = "outra"

        with self.assertRaises(AttributeError):
            self.admin.nome = "Outro"

        self.assertEqual(
            self.admin.matricula, "2026999"
        )
        self.assertEqual(
            self.admin.nome, "Admin Teste"
        )


if __name__ == "__main__":
    unittest.main()
