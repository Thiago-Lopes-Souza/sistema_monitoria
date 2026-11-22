"""Testes da frente A: esquema, conexão, repositório e carga fictícia.

Cada teste monta a própria base: ":memory:" na maioria, e um arquivo numa
pasta temporária quando o teste precisa fechar e reabrir a conexão. Nenhum
teste toca a base de demonstração (dados/monitorias.db).
"""

import sqlite3
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

from monitorias.dominio import senha
from monitorias.dominio.atendimento import AtendimentoOnline, AtendimentoPresencial
from monitorias.dominio.disciplina import Disciplina
from monitorias.dominio.excecoes import RegistroDuplicado
from monitorias.dominio.monitor import Monitor
from monitorias.dominio.senha import conferir_senha
from monitorias.dominio.usuario import Administrador
from monitorias.persistencia import seed_demo
from monitorias.persistencia.conexao import EM_MEMORIA, abrir_base, criar_esquema
from monitorias.persistencia.repositorio import RepositorioMonitorias

DATA = date(2026, 11, 1)
HASH, SAL = b"hash-ficticio", b"sal-ficticio"  # o repositório não calcula hash


def preparar_base_minima(repo: RepositorioMonitorias) -> None:
    """Caio vinculado a MAT001 e DCC203, Ana a DCC203. Sem atendimentos."""
    with repo.transacao():
        repo.inserir_monitor(Monitor("2026000001", "Ana Fictícia", "ana.ficticia@ufmg.br"), HASH, SAL)
        repo.inserir_monitor(Monitor("2026000002", "Caio Exemplo", "caio.exemplo@ufmg.br"), HASH, SAL)
        repo.inserir_disciplina(Disciplina("MAT001", "Cálculo I"))
        repo.inserir_disciplina(Disciplina("DCC203", "PDS I"))
        repo.inserir_vinculo("2026000002", "MAT001")
        repo.inserir_vinculo("2026000002", "DCC203")
        repo.inserir_vinculo("2026000001", "DCC203")


def presencial(dia="terça", inicio="14:00", fim="16:00"):
    return AtendimentoPresencial(dia, inicio, fim, "ICEx", "1010", DATA)


def online(dia="quinta", inicio="19:00", fim="20:00"):
    return AtendimentoOnline(dia, inicio, fim, "Google Meet", "https://meet.exemplo/x", DATA)


def contar(conexao, tabela: str) -> int:
    return conexao.execute(f"SELECT COUNT(*) FROM {tabela}").fetchone()[0]


class BaseEmMemoria(unittest.TestCase):
    """Base nova em memória para cada teste, já com o esquema."""

    def setUp(self):
        self.conexao = abrir_base(EM_MEMORIA)
        self.repo = RepositorioMonitorias(self.conexao)

    def tearDown(self):
        self.conexao.close()


class TestConexaoEEsquema(BaseEmMemoria):

    def test_chaves_estrangeiras_ligadas(self):
        self.assertEqual(self.conexao.execute("PRAGMA foreign_keys").fetchone()[0], 1)

    def test_esquema_pode_ser_aplicado_de_novo_sem_perder_dados(self):
        preparar_base_minima(self.repo)
        criar_esquema(self.conexao)
        self.assertEqual(contar(self.conexao, "vinculos"), 3)

    def test_base_nova_esta_vazia(self):
        self.assertTrue(self.repo.esta_vazia())
        preparar_base_minima(self.repo)
        self.assertFalse(self.repo.esta_vazia())


class TestUsuariosEDisciplinas(BaseEmMemoria):

    def setUp(self):
        super().setUp()
        preparar_base_minima(self.repo)

    def test_papel_escolhe_a_classe(self):
        with self.repo.transacao():
            self.repo.inserir_administrador(
                Administrador("2026900001", "Admin", "admin@ufmg.br"), HASH, SAL)
        self.assertIs(type(self.repo.buscar_usuario("2026900001")), Administrador)
        monitor = self.repo.buscar_usuario(" 2026000002 ")
        self.assertIs(type(monitor), Monitor)
        self.assertEqual((monitor.nome, monitor.email), ("Caio Exemplo", "caio.exemplo@ufmg.br"))

    def test_usuario_inexistente_devolve_none(self):
        self.assertIsNone(self.repo.buscar_usuario("2099999999"))
        self.assertIsNone(self.repo.buscar_credenciais("2099999999"))

    def test_credenciais_saem_separadas_do_objeto(self):
        self.assertEqual(self.repo.buscar_credenciais("2026000001"), (HASH, SAL))
        self.assertFalse(hasattr(self.repo.buscar_usuario("2026000001"), "senha_hash"))

    def test_disciplinas_ordenadas_e_busca_ignora_maiusculas(self):
        self.assertEqual([d.codigo for d in self.repo.listar_disciplinas()], ["DCC203", "MAT001"])
        self.assertEqual(self.repo.buscar_disciplina("mat001").nome, "Cálculo I")
        self.assertIsNone(self.repo.buscar_disciplina("FIS069"))

    def test_sql_injection_nao_funciona(self):
        self.assertIsNone(self.repo.buscar_disciplina("x' OR '1'='1"))
        self.assertIsNone(self.repo.buscar_usuario("' OR 1=1 --"))


class TestUnicidade(BaseEmMemoria):
    """R7: matrícula, código e par (monitor, disciplina) não se repetem."""

    def setUp(self):
        super().setUp()
        preparar_base_minima(self.repo)

    def test_disciplina_repetida(self):
        with self.assertRaises(RegistroDuplicado) as contexto:
            with self.repo.transacao():
                self.repo.inserir_disciplina(Disciplina("MAT001", "Outro nome"))
        self.assertEqual(contexto.exception.chave, "MAT001")
        self.assertEqual(self.repo.buscar_disciplina("MAT001").nome, "Cálculo I")
        self.assertEqual(contar(self.conexao, "disciplinas"), 2)

    def test_matricula_repetida_mesmo_com_outro_papel(self):
        with self.assertRaises(RegistroDuplicado):
            with self.repo.transacao():
                self.repo.inserir_administrador(
                    Administrador("2026000001", "Outra", "outra@ufmg.br"), HASH, SAL)
        self.assertIs(type(self.repo.buscar_usuario("2026000001")), Monitor)

    def test_vinculo_repetido(self):
        with self.assertRaises(RegistroDuplicado):
            with self.repo.transacao():
                self.repo.inserir_vinculo("2026000002", "MAT001")
        self.assertEqual(contar(self.conexao, "vinculos"), 3)


class TestAtendimentos(BaseEmMemoria):

    def setUp(self):
        super().setUp()
        preparar_base_minima(self.repo)

    def test_presencial_e_online_voltam_iguais_e_com_id(self):
        with self.repo.transacao():
            p = self.repo.inserir_atendimento("2026000002", "MAT001", presencial())
            o = self.repo.inserir_atendimento("2026000002", "MAT001", online())
        self.assertIsNotNone(p.id)
        self.assertNotEqual(p.id, o.id)
        vinculo, lido = self.repo.buscar_atendimento(o.id)
        self.assertEqual(vinculo.monitor.matricula, "2026000002")
        self.assertEqual(vinculo.disciplina.codigo, "MAT001")
        self.assertEqual((lido.modalidade(), lido.local(), lido.registrado_em),
                         ("online", "Google Meet: https://meet.exemplo/x", DATA))
        _, lido = self.repo.buscar_atendimento(p.id)
        self.assertEqual((lido.dia, lido.inicio, lido.fim, lido.local()),
                         ("terça", "14:00", "16:00", "ICEx, sala 1010"))

    def test_vinculos_do_monitor_trazem_todas_as_disciplinas(self):
        with self.repo.transacao():
            self.repo.inserir_atendimento("2026000002", "MAT001", presencial())
            self.repo.inserir_atendimento("2026000002", "DCC203", online())
        vinculos = self.repo.vinculos_do_monitor("2026000002")
        self.assertEqual([(v.disciplina.codigo, len(v.atendimentos)) for v in vinculos],
                         [("DCC203", 1), ("MAT001", 1)])

    def test_vinculos_da_disciplina_incluem_monitor_sem_horario(self):
        with self.repo.transacao():
            self.repo.inserir_atendimento("2026000001", "DCC203", presencial())
        vinculos = self.repo.vinculos_da_disciplina("DCC203")
        self.assertEqual([(v.monitor.nome, len(v.atendimentos)) for v in vinculos],
                         [("Ana Fictícia", 1), ("Caio Exemplo", 0)])

    def test_atendimento_sem_vinculo_e_recusado_pela_base(self):
        with self.assertRaises(sqlite3.IntegrityError):
            with self.repo.transacao():
                self.repo.inserir_atendimento("2026000001", "MAT001", presencial())
        self.assertEqual(contar(self.conexao, "atendimentos"), 0)

    def test_atualizar_mantem_id_e_vinculo(self):
        with self.repo.transacao():
            original = self.repo.inserir_atendimento("2026000002", "MAT001", presencial())
            novo = self.repo.atualizar_atendimento(original.id, presencial("quarta"))
        self.assertEqual((novo.id, novo.dia), (original.id, "quarta"))
        vinculo, _ = self.repo.buscar_atendimento(original.id)
        self.assertEqual(vinculo.disciplina.codigo, "MAT001")

    def test_atualizar_id_inexistente(self):
        with self.assertRaises(LookupError):
            with self.repo.transacao():
                self.repo.atualizar_atendimento(999, presencial())

    def test_excluir_e_id_nao_e_reaproveitado(self):
        with self.repo.transacao():
            primeiro = self.repo.inserir_atendimento("2026000002", "MAT001", presencial())
        with self.repo.transacao():
            self.assertTrue(self.repo.excluir_atendimento(primeiro.id))
            self.assertFalse(self.repo.excluir_atendimento(primeiro.id))
        self.assertIsNone(self.repo.buscar_atendimento(primeiro.id))
        with self.repo.transacao():
            segundo = self.repo.inserir_atendimento("2026000002", "MAT001", presencial())
        self.assertGreater(segundo.id, primeiro.id)

    def test_check_da_base_e_rede_de_seguranca(self):
        """Linhas que o domínio nunca criaria são recusadas pela própria base."""
        invalidas = (
            ("domingo", "10:00", "12:00", "presencial", "ICEx", "1", None, None),
            ("terça", "16:00", "14:00", "presencial", "ICEx", "1", None, None),
            ("terça", "10:00", "12:00", "presencial", None, None, "Meet", "https://x"),
            ("terça", "10:00", "12:00", "online", None, None, "Meet", "http://x"),
        )
        for linha in invalidas:
            with self.subTest(linha=linha):
                with self.assertRaises(sqlite3.IntegrityError):
                    with self.conexao:
                        self.conexao.execute(
                            "INSERT INTO atendimentos (matricula, codigo, dia, inicio, fim, "
                            "modalidade, predio, sala, plataforma, link, registrado_em) "
                            "VALUES ('2026000002', 'MAT001', ?, ?, ?, ?, ?, ?, ?, ?, '2026-11-01')",
                            linha)
        self.assertEqual(contar(self.conexao, "atendimentos"), 0)


class TestCascataA4(BaseEmMemoria):
    """Desvincular apaga o vínculo e só os horários dele."""

    def setUp(self):
        super().setUp()
        preparar_base_minima(self.repo)
        with self.repo.transacao():
            self.repo.inserir_atendimento("2026000002", "MAT001", presencial("terça"))
            self.repo.inserir_atendimento("2026000002", "MAT001", online("quinta"))
            self.repo.inserir_atendimento("2026000002", "DCC203", presencial("sexta"))
            self.repo.inserir_atendimento("2026000001", "DCC203", presencial("segunda"))

    def test_a4_desvincular_remove_so_os_horarios_do_vinculo(self):
        with self.repo.transacao():
            removidos = self.repo.excluir_vinculo("2026000002", "MAT001")
        self.assertEqual(removidos, 2)
        self.assertIsNone(self.repo.buscar_vinculo("2026000002", "MAT001"))
        restante = self.repo.vinculos_do_monitor("2026000002")
        self.assertEqual([(v.disciplina.codigo, [a.dia for a in v.atendimentos]) for v in restante],
                         [("DCC203", ["sexta"])])
        self.assertEqual(len(self.repo.buscar_vinculo("2026000001", "DCC203").atendimentos), 1)
        self.assertEqual(contar(self.conexao, "atendimentos"), 2)

    def test_desvincular_par_inexistente_nao_apaga_nada(self):
        with self.repo.transacao():
            self.assertEqual(self.repo.excluir_vinculo("2026000001", "MAT001"), 0)
        self.assertEqual(contar(self.conexao, "atendimentos"), 4)


class TestTransacao(BaseEmMemoria):

    def setUp(self):
        super().setUp()
        preparar_base_minima(self.repo)

    def test_erro_no_meio_desfaz_tudo(self):
        with self.assertRaises(RegistroDuplicado):
            with self.repo.transacao():
                self.repo.inserir_atendimento("2026000002", "MAT001", presencial())
                self.repo.inserir_disciplina(Disciplina("FIS069", "Física III"))
                self.repo.inserir_vinculo("2026000002", "MAT001")  # repetido: falha
        self.assertEqual(contar(self.conexao, "atendimentos"), 0)
        self.assertIsNone(self.repo.buscar_disciplina("FIS069"))

    def test_excecao_do_dominio_tambem_desfaz(self):
        class RecusaDoDominio(Exception):
            pass
        with self.assertRaises(RecusaDoDominio):
            with self.repo.transacao():
                self.repo.inserir_atendimento("2026000002", "MAT001", presencial())
                raise RecusaDoDominio()
        self.assertEqual(contar(self.conexao, "atendimentos"), 0)

    def test_transacao_interna_entra_na_externa(self):
        with self.assertRaises(ValueError):
            with self.repo.transacao():
                with self.repo.transacao():
                    self.repo.inserir_atendimento("2026000002", "MAT001", presencial())
                raise ValueError("falha depois do bloco interno")
        self.assertEqual(contar(self.conexao, "atendimentos"), 0)

    def test_gravacao_fora_de_transacao_e_recusada(self):
        with self.assertRaises(RuntimeError):
            self.repo.inserir_disciplina(Disciplina("FIS069", "Física III"))
        self.assertIsNone(self.repo.buscar_disciplina("FIS069"))


class TestPersistenciaAposReinicio(unittest.TestCase):
    """Os dados continuam lá depois de fechar e reabrir a base (arquivo real)."""

    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory()
        self.caminho = Path(self.pasta.name) / "teste.db"

    def tearDown(self):
        self.pasta.cleanup()

    def reabrir(self):
        """Abre a base do arquivo, como o programa faz ao iniciar."""
        conexao = abrir_base(self.caminho)
        self.addCleanup(conexao.close)  # fechar duas vezes não dá erro
        return conexao, RepositorioMonitorias(conexao)

    def test_f1a_persistencia_apos_reinicio(self):
        conexao, repo = self.reabrir()
        preparar_base_minima(repo)
        with repo.transacao():
            gravado = repo.inserir_atendimento("2026000002", "MAT001", presencial("sexta"))
        conexao.close()  # "encerra o programa"

        _, repo = self.reabrir()
        _, lido = repo.buscar_atendimento(gravado.id)
        self.assertEqual((lido.dia, lido.inicio, lido.fim, lido.local()),
                         ("sexta", "14:00", "16:00", "ICEx, sala 1010"))

    def test_rollback_nao_aparece_depois_de_reabrir(self):
        conexao, repo = self.reabrir()
        preparar_base_minima(repo)
        with self.assertRaises(RegistroDuplicado):
            with repo.transacao():
                repo.inserir_atendimento("2026000002", "MAT001", presencial())
                repo.inserir_vinculo("2026000002", "MAT001")
        conexao.close()

        _, repo = self.reabrir()
        self.assertEqual(repo.buscar_vinculo("2026000002", "MAT001").atendimentos, ())


@mock.patch.object(senha, "ITERACOES", 1_000)  # hash mais rápido só nos testes
class TestCargaDemo(BaseEmMemoria):

    def test_carga_preenche_todos_os_fluxos(self):
        self.assertTrue(seed_demo.carregar_demo(self.repo))
        self.assertIs(type(self.repo.buscar_usuario("2026900001")), Administrador)
        self.assertEqual(len(self.repo.listar_disciplinas()), 5)
        self.assertEqual(self.repo.vinculos_da_disciplina("ELT001"), ())
        self.assertEqual(self.repo.vinculos_do_monitor("2026000003")[0].atendimentos, ())
        self.assertEqual(contar(self.conexao, "atendimentos"), 4)

    def test_carga_tem_monitor_com_horarios_em_duas_disciplinas(self):
        """Necessário para demonstrar F1C-03 (conflito entre disciplinas) e A4-01."""
        seed_demo.carregar_demo(self.repo)
        com_horario = [v.disciplina.codigo
                       for v in self.repo.vinculos_do_monitor("2026000001") if v.atendimentos]
        self.assertEqual(com_horario, ["DCC203", "MAT002"])

    def test_carga_mantem_as_situacoes_do_prototipo(self):
        """DCC203 e MAT001 continuam como nos cenários C1 a C3 do protótipo."""
        seed_demo.carregar_demo(self.repo)
        resumo = {v.monitor.nome: [(a.dia, a.inicio) for a in v.atendimentos]
                  for v in self.repo.vinculos_da_disciplina("DCC203")}
        self.assertEqual(resumo, {"Ana Fictícia": [("terça", "10:00")], "Caio Exemplo": []})
        mat001 = self.repo.vinculos_da_disciplina("MAT001")
        self.assertEqual([(a.dia, a.modalidade()) for a in mat001[0].atendimentos],
                         [("terça", "presencial"), ("quinta", "online")])

    def test_carga_e_idempotente(self):
        seed_demo.carregar_demo(self.repo)
        antes = [contar(self.conexao, t) for t in ("usuarios", "disciplinas", "vinculos", "atendimentos")]
        self.assertFalse(seed_demo.carregar_demo(self.repo))
        depois = [contar(self.conexao, t) for t in ("usuarios", "disciplinas", "vinculos", "atendimentos")]
        self.assertEqual(antes, depois)

    def test_carga_nao_mexe_em_base_com_dados(self):
        preparar_base_minima(self.repo)
        self.assertFalse(seed_demo.carregar_demo(self.repo))
        self.assertIsNone(self.repo.buscar_usuario("2026900001"))

    def test_senhas_de_demonstracao_conferem(self):
        seed_demo.carregar_demo(self.repo)
        for matricula, _, _, senha_demo in seed_demo.ADMINISTRADORES + seed_demo.MONITORES:
            with self.subTest(matricula=matricula):
                self.assertTrue(conferir_senha(senha_demo, *self.repo.buscar_credenciais(matricula)))
                self.assertFalse(conferir_senha("errada", *self.repo.buscar_credenciais(matricula)))

    def test_carga_respeita_a_regra_de_sobreposicao(self):
        seed_demo.carregar_demo(self.repo)
        for matricula, *_ in seed_demo.MONITORES:
            horarios = [a for v in self.repo.vinculos_do_monitor(matricula) for a in v.atendimentos]
            for i, a in enumerate(horarios):
                for b in horarios[i + 1:]:
                    with self.subTest(matricula=matricula, a=a, b=b):
                        self.assertFalse(a.sobrepoe(b))


if __name__ == "__main__":
    unittest.main()
