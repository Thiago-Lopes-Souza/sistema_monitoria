"""Testes de integração (frente D): menu + cadastro + SQLite juntos.

Cada teste cria a própria base num arquivo temporário, aplica a carga fictícia
e roda o menu (executar) com entradas simuladas em sys.stdin, capturando a
saída. Nada depende da ordem dos testes nem da base de demonstração.

O estado da base é comparado pela própria consulta pública: o texto da F2 de
todas as disciplinas, que mostra todos os horários gravados.
"""

import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from monitorias.dominio.cadastro import CadastroMonitorias
from monitorias.dominio.excecoes import PermissaoNegada
from monitorias.menu import executar, formatar_resultado
from monitorias.persistencia.conexao import abrir_base
from monitorias.persistencia.repositorio import RepositorioMonitorias
from monitorias.persistencia.seed_demo import carregar_demo


class TestIntegracao(unittest.TestCase):
    """Fluxos completos pelo menu, gravando numa base SQLite em arquivo."""

    def setUp(self):
        """Base nova, com a carga fictícia, num diretório temporário."""
        self._pasta = tempfile.TemporaryDirectory()
        self.caminho = Path(self._pasta.name) / "teste.db"
        self._abrir()
        carregar_demo(self.repositorio)

    def tearDown(self):
        """Fecha a conexão e apaga o diretório temporário."""
        self.conexao.close()
        self._pasta.cleanup()

    # ------------------------------------------------------------ utilitários
    def _abrir(self):
        """Abre (ou reabre) a conexão com o arquivo da base e monta o cadastro."""
        self.conexao = abrir_base(self.caminho)
        self.repositorio = RepositorioMonitorias(self.conexao)
        self.cadastro = CadastroMonitorias(self.repositorio)

    def rodar_menu(self, *entradas: str) -> str:
        """Roda executar() com as entradas, uma por linha, e devolve a saída."""
        saida = io.StringIO()
        texto = "\n".join(entradas) + "\n"
        with mock.patch("sys.stdin", io.StringIO(texto)), contextlib.redirect_stdout(saida):
            executar(self.cadastro)
        return saida.getvalue()

    def estado(self) -> tuple[str, ...]:
        """Fotografia dos dados: a consulta (F2) de cada disciplina, em texto."""
        return tuple(formatar_resultado(self.cadastro.consultar_monitorias(d.codigo))
                     for d in self.cadastro.listar_disciplinas())

    # ------------------------------------------------------------ cenários
    def test_int_01_f1a_pelo_menu_aparece_na_f2(self):
        saida = self.rodar_menu(
            "2", "2026000001", "ana123",                 # entra como Ana
            "2", "DCC203", "1", "CAD 3", "204", "5", "14:00", "16:00",  # F1a sexta
            "0",                                         # sai da sessão
            "1", "DCC203", "", "5",                      # F2 DCC203, sexta
            "0",
        )
        self.assertIn("Horário cadastrado (ID", saida)
        self.assertIn("(modalidade: todas | dia: sexta)", saida)
        self.assertIn("sexta 14:00–16:00 | presencial | CAD 3, sala 204", saida)
        ana = self.cadastro.entrar("2026000001", "ana123")
        dias = [(d.codigo, a.dia, a.inicio) for d, a in self.cadastro.listar_meus_atendimentos(ana)]
        self.assertIn(("DCC203", "sexta", "14:00"), dias)

    def test_int_02_f1a_com_conflito_nao_altera_a_base(self):
        caio = self.cadastro.entrar("2026000002", "caio123")
        antes_caio = [(d.codigo, a.id, a.dia, a.inicio, a.fim)
                      for d, a in self.cadastro.listar_meus_atendimentos(caio)]
        antes = self.estado()

        saida = self.rodar_menu(
            "2", "2026000002", "caio123",
            "2", "DCC203", "1", "CAD 3", "204", "2", "15:00", "17:00",  # terça 15–17
            "0", "0",
        )
        self.assertIn("Conflito de horário: você já atende terça 14:00–16:00 em MAT001.", saida)
        self.assertIn("Nenhum dado foi alterado.", saida)
        depois_caio = [(d.codigo, a.id, a.dia, a.inicio, a.fim)
                       for d, a in self.cadastro.listar_meus_atendimentos(caio)]
        self.assertEqual(depois_caio, antes_caio)
        self.assertEqual(self.estado(), antes)

    def test_int_03_horario_persiste_apos_reiniciar(self):
        self.rodar_menu(
            "2", "2026000001", "ana123",
            "2", "DCC203", "2", "Google Meet", "https://meet.exemplo/ana", "6", "09:00", "10:00",
            "0", "0",
        )
        self.conexao.close()          # "fecha o programa"
        self._abrir()                 # "abre de novo" no mesmo arquivo

        saida = self.rodar_menu("1", "DCC203", "2", "", "0")
        self.assertIn("sábado 09:00–10:00 | online | Google Meet: https://meet.exemplo/ana", saida)

    def test_int_04_senha_errada_volta_ao_menu_inicial(self):
        antes = self.estado()
        saida = self.rodar_menu("2", "2026000001", "senha-errada", "0")
        self.assertIn("Não foi possível concluir: Matrícula ou senha inválida.", saida)
        self.assertNotIn("Sessão iniciada", saida)
        self.assertEqual(saida.count("--- Menu inicial ---"), 2)
        self.assertNotIn("senha-errada", saida)   # a senha nunca aparece na transcrição
        self.assertEqual(self.estado(), antes)

    def test_int_05_monitor_nao_ve_nem_executa_operacoes_de_admin(self):
        saida = self.rodar_menu("2", "2026000002", "caio123", "0", "0")
        self.assertIn("Cadastrar horário de atendimento", saida)
        for rotulo in ("Cadastrar disciplina", "Cadastrar monitor",
                       "Vincular monitor", "Desvincular monitor"):
            self.assertNotIn(rotulo, saida)

        caio = self.cadastro.entrar("2026000002", "caio123")
        catalogo = self.cadastro.listar_disciplinas()
        with self.assertRaises(PermissaoNegada):
            self.cadastro.cadastrar_disciplina(caio, "DCC205", "Estruturas de Dados")
        self.assertEqual(self.cadastro.listar_disciplinas(), catalogo)

    def test_int_06_entrada_invalida_nao_derruba_nem_altera(self):
        antes = self.estado()
        saida = self.rodar_menu("abc", "9", "0")
        self.assertIn("'abc' não é um número válido. Digite um número de 0 a 3.", saida)
        self.assertIn("Opção 9 não existe. Digite um número de 0 a 3.", saida)
        self.assertIn("Encerrando.", saida)
        self.assertNotIn("Traceback", saida)
        self.assertEqual(self.estado(), antes)

    def test_int_07_fim_da_entrada_encerra_sem_traceback(self):
        saida = self.rodar_menu("2", "2026000001")   # entrada acaba antes da senha
        self.assertIn("Encerrando.", saida)
        self.assertNotIn("Traceback", saida)


if __name__ == "__main__":
    unittest.main()
