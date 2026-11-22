
"""Testes da funcionalidade S1: autenticação de usuários."""

import unittest
from unittest import mock

from monitorias.dominio import senha
from monitorias.dominio.cadastro import CadastroMonitorias
from monitorias.dominio.excecoes import CredenciaisInvalidas
from monitorias.dominio.monitor import Monitor
from monitorias.dominio.usuario import Administrador, Operacao
from monitorias.persistencia.conexao import abrir_base, EM_MEMORIA
from monitorias.persistencia.repositorio import RepositorioMonitorias


class TestEntrar(unittest.TestCase):

    def setUp(self):
        """Prepara um banco temporário com um monitor e um administrador."""

        # Reduz as iterações apenas nos testes para acelerar a execução.
        alteracao = mock.patch.object(senha, "ITERACOES", 1000)
        alteracao.start()
        self.addCleanup(alteracao.stop)

        self.conexao = abrir_base(EM_MEMORIA)
        self.addCleanup(self.conexao.close)

        self.repositorio = RepositorioMonitorias(self.conexao)
        self.cadastro = CadastroMonitorias(self.repositorio)

        monitor = Monitor(
            "2026000001", "Ana", "ana@ufmg.br"
        )
        administrador = Administrador(
            "2026900001", "Admin", "admin@ufmg.br"
        )

        # Só o administrador é gravado pelo repositório: nenhuma operação do
        # sistema cadastra administradores. O monitor entra pelo A2.
        with self.repositorio.transacao():
            self.repositorio.inserir_administrador(
                administrador,
                *senha.gerar_hash_senha("admin123")
            )
        admin = self.repositorio.buscar_usuario(administrador.matricula)
        self.cadastro.cadastrar_monitor(
            admin, monitor.matricula, monitor.nome, monitor.email, "ana123")

    def test_s1_01_login_monitor_valido(self):
        usuario = self.cadastro.entrar(
            "2026000001", "ana123"
        )

        self.assertIsInstance(usuario, Monitor)
        self.assertEqual(usuario.nome, "Ana")
        self.assertEqual(usuario.matricula, "2026000001")

    def test_s1_02_login_administrador_valido(self):
        usuario = self.cadastro.entrar(
            "2026900001", "admin123"
        )

        self.assertIsInstance(usuario, Administrador)
        self.assertEqual(usuario.nome, "Admin")

    def test_s1_03_senha_incorreta(self):
        with self.assertRaises(CredenciaisInvalidas):
            self.cadastro.entrar(
                "2026000001", "senhaerrada"
            )

    def test_s1_04_matricula_inexistente(self):
        with self.assertRaises(CredenciaisInvalidas):
            self.cadastro.entrar(
                "9999999999", "ana123"
            )

    def test_s1_05_matricula_com_espacos(self):
        usuario = self.cadastro.entrar(
            " 2026000001 ", "ana123"
        )

        self.assertIsInstance(usuario, Monitor)
        self.assertEqual(usuario.matricula, "2026000001")

    def test_s1_06_entradas_vazias(self):
        entradas = [
            ("", "ana123"),
            ("2026000001", ""),
            ("", ""),
            ("   ", "ana123"),
        ]

        for matricula, senha_digitada in entradas:
            with self.subTest(matricula=matricula):
                with self.assertRaises(CredenciaisInvalidas):
                    self.cadastro.entrar(
                        matricula, senha_digitada
                    )

    def test_s1_07_senha_diferencia_maiusculas(self):
        with self.assertRaises(CredenciaisInvalidas):
            self.cadastro.entrar(
                "2026000001", "ANA123"
            )

    def test_s1_08_permissoes_do_usuario_autenticado(self):
        monitor = self.cadastro.entrar(
            "2026000001", "ana123"
        )
        admin = self.cadastro.entrar(
            "2026900001", "admin123"
        )

        self.assertTrue(
            monitor.pode(Operacao.CADASTRAR_HORARIO)
        )
        self.assertFalse(
            monitor.pode(Operacao.CADASTRAR_DISCIPLINA)
        )

        self.assertTrue(
            admin.pode(Operacao.CADASTRAR_DISCIPLINA)
        )
        self.assertFalse(
            admin.pode(Operacao.CADASTRAR_HORARIO)
        )

    def test_s1_09_mensagem_generica_para_login_invalido(self):
        with self.assertRaises(CredenciaisInvalidas) as erro1:
            self.cadastro.entrar(
                "9999999999", "ana123"
            )

        with self.assertRaises(CredenciaisInvalidas) as erro2:
            self.cadastro.entrar(
                "2026000001", "errada"
            )

        self.assertEqual(str(erro1.exception),
                         str(erro2.exception))


if __name__ == "__main__":
    unittest.main()