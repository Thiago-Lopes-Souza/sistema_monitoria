"""Testes de F1a, F1b, F1c e F1d integradas a SQLite e autenticação.

Executar na pasta prototipo_monitoria:
    python -m unittest discover -s tests -p "test_f1.py" -v

A base utilizada é sempre temporária; o banco de demonstração não é alterado.
"""

import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

from monitorias.dominio import senha
from monitorias.dominio.atendimento import AtendimentoOnline, AtendimentoPresencial
from monitorias.dominio.cadastro import CadastroMonitorias
from monitorias.dominio.disciplina import Disciplina
from monitorias.dominio.excecoes import (
    AtendimentoInexistente,
    ConflitoDeHorario,
    DadosInvalidos,
    DisciplinaForaDoEscopo,
    MatriculaNaoCadastrada,
    PermissaoNegada,
    VinculoInexistente,
)
from monitorias.dominio.monitor import Monitor
from monitorias.dominio.usuario import Aluno
from monitorias.persistencia.conexao import EM_MEMORIA, abrir_base
from monitorias.persistencia.repositorio import RepositorioMonitorias
from monitorias.persistencia.seed_demo import carregar_demo


class BaseF1(unittest.TestCase):
    """Ambiente isolado, recriado para cada cenário."""

    def setUp(self):
        patch = mock.patch.object(senha, "ITERACOES", 1_000)
        patch.start()
        self.addCleanup(patch.stop)

        self.conexao = abrir_base(EM_MEMORIA)
        self.addCleanup(self.conexao.close)
        self.repositorio = RepositorioMonitorias(self.conexao)
        carregar_demo(self.repositorio)
        self.cadastro = CadastroMonitorias(self.repositorio)

        self.ana = self.cadastro.entrar("2026000001", "ana123")
        self.caio = self.cadastro.entrar("2026000002", "caio123")
        self.duda = self.cadastro.entrar("2026000003", "duda123")
        self.admin = self.cadastro.entrar("2026900001", "admin123")
        self.aluno = Aluno()

    def presencial(
        self, usuario=None, codigo="DCC203", dia="sexta", inicio="14:00",
        fim="16:00", predio="CAD 3", sala="204",
    ):
        if usuario is None:
            usuario = self.ana
        return self.cadastro.cadastrar_presencial(
            usuario, codigo, dia, inicio, fim, predio, sala
        )

    def online(
        self, usuario=None, codigo="DCC203", dia="sexta", inicio="19:00",
        fim="20:00", plataforma="Google Meet",
        link="https://meet.exemplo/abc",
    ):
        if usuario is None:
            usuario = self.ana
        return self.cadastro.cadastrar_online(
            usuario, codigo, dia, inicio, fim, plataforma, link
        )

    def estado(self):
        """Fotografia completa da tabela: detecta alterações indevidas."""
        linhas = self.conexao.execute(
            "SELECT id, matricula, codigo, dia, inicio, fim, modalidade, "
            "predio, sala, plataforma, link, registrado_em "
            "FROM atendimentos ORDER BY id"
        ).fetchall()
        return tuple(tuple(linha) for linha in linhas)

    def buscar(self, id_atendimento):
        """Consulta o banco, sem utilizar o objeto devolvido pela F1a/F1c."""
        return self.repositorio.buscar_atendimento(id_atendimento)

    def id_inicial(self, matricula, codigo, dia):
        for vinculo in self.repositorio.vinculos_do_monitor(matricula):
            if vinculo.disciplina.codigo == codigo:
                for atendimento in vinculo.atendimentos:
                    if atendimento.dia == dia:
                        return atendimento.id
        self.fail(f"Não existe atendimento inicial: {matricula} {codigo} {dia}")

    def verificar_estado_preservado(self, antes):
        self.assertEqual(self.estado(), antes)


class TestF1aCadastrar(BaseF1):
    """F1a: criação, validação, conflitos, autorização e persistência."""

    def test_f1a_01_cadastro_presencial_valido(self):
        atendimento = self.presencial()
        self.assertIsInstance(atendimento, AtendimentoPresencial)
        self.assertIsInstance(atendimento.id, int)
        self.assertEqual((atendimento.dia, atendimento.inicio, atendimento.fim),
                         ("sexta", "14:00", "16:00"))
        self.assertEqual(atendimento.local(), "CAD 3, sala 204")
        vinculo, lido = self.buscar(atendimento.id)
        self.assertEqual(vinculo.monitor.matricula, self.ana.matricula)
        self.assertEqual(vinculo.disciplina.codigo, "DCC203")
        self.assertEqual(lido.local(), atendimento.local())

    def test_f1a_02_cadastro_online_valido(self):
        atendimento = self.online()
        self.assertIsInstance(atendimento, AtendimentoOnline)
        self.assertIsInstance(atendimento.id, int)
        _, lido = self.buscar(atendimento.id)
        self.assertEqual(lido.modalidade(), "online")
        self.assertEqual(lido.local(), "Google Meet: https://meet.exemplo/abc")

    def test_f1a_03_normalizacao_dia_horario_e_local(self):
        a = self.presencial(dia="  SEXTA ", inicio="9:00", fim="11:00",
                            predio=" CAD 3 ", sala=" 204 ")
        self.assertEqual((a.dia, a.inicio, a.fim), ("sexta", "09:00", "11:00"))
        self.assertEqual((a.predio, a.sala), ("CAD 3", "204"))
        _, lido = self.buscar(a.id)
        self.assertEqual((lido.predio, lido.sala), ("CAD 3", "204"))

    def test_f1a_04_link_preserva_maiusculas(self):
        a = self.online(link="https://meet.exemplo/SalaABC")
        _, lido = self.buscar(a.id)
        self.assertEqual(lido.link, "https://meet.exemplo/SalaABC")

    def test_f1a_05_codigo_minusculo_e_aceito(self):
        a = self.presencial(codigo=" dcc203 ")
        vinculo, _ = self.buscar(a.id)
        self.assertEqual(vinculo.disciplina.codigo, "DCC203")

    def test_f1a_06_matricula_com_espacos_no_login(self):
        usuario = self.cadastro.entrar(" 2026000001 ", "ana123")
        a = self.presencial(usuario=usuario)
        vinculo, _ = self.buscar(a.id)
        self.assertEqual(vinculo.monitor.matricula, "2026000001")

    def test_f1a_07_cadastros_distintos_recebem_ids_distintos(self):
        primeiro = self.presencial()
        segundo = self.online()
        self.assertNotEqual(primeiro.id, segundo.id)
        self.assertIsNotNone(self.buscar(primeiro.id))
        self.assertIsNotNone(self.buscar(segundo.id))

    def test_f1a_08_monitor_nao_cadastrado(self):
        antes = self.estado()
        estranho = Monitor("2099999999", "Outro", "outro@ufmg.br")
        with self.assertRaises(MatriculaNaoCadastrada):
            self.presencial(usuario=estranho)
        self.verificar_estado_preservado(antes)

    def test_f1a_09_disciplina_fora_do_escopo(self):
        antes = self.estado()
        with self.assertRaises(DisciplinaForaDoEscopo):
            self.presencial(codigo="DCC999")
        self.verificar_estado_preservado(antes)

    def test_f1a_10_codigo_mal_formatado(self):
        antes = self.estado()
        with self.assertRaises(DadosInvalidos):
            self.presencial(codigo="CODIGO-ERRADO")
        self.verificar_estado_preservado(antes)

    def test_f1a_11_monitor_sem_vinculo(self):
        antes = self.estado()
        with self.assertRaises(VinculoInexistente):
            self.presencial(codigo="MAT001")  # Ana não é monitora de MAT001.
        self.verificar_estado_preservado(antes)

    def test_f1a_12_dia_invalido(self):
        antes = self.estado()
        for dia in ("domingo", "", "dia-inexistente"):
            with self.subTest(dia=dia):
                with self.assertRaises(DadosInvalidos):
                    self.presencial(dia=dia)
                self.verificar_estado_preservado(antes)

    def test_f1a_13_horarios_invalidos(self):
        antes = self.estado()
        casos = (("16:00", "14:00"), ("14:00", "14:00"),
                 ("25:00", "26:00"), ("14h00", "16:00"))
        for inicio, fim in casos:
            with self.subTest(inicio=inicio, fim=fim):
                with self.assertRaises(DadosInvalidos):
                    self.presencial(inicio=inicio, fim=fim)
                self.verificar_estado_preservado(antes)

    def test_f1a_14_local_presencial_invalido(self):
        antes = self.estado()
        for predio, sala in (("", "204"), ("CAD 3", "  ")):
            with self.subTest(predio=predio, sala=sala):
                with self.assertRaises(DadosInvalidos):
                    self.presencial(predio=predio, sala=sala)
                self.verificar_estado_preservado(antes)

    def test_f1a_15_local_online_invalido(self):
        antes = self.estado()
        casos = (("", "https://meet.exemplo/abc"),
                 ("Google Meet", "http://meet.exemplo/abc"),
                 ("Google Meet", ""))
        for plataforma, link in casos:
            with self.subTest(plataforma=plataforma, link=link):
                with self.assertRaises(DadosInvalidos):
                    self.online(plataforma=plataforma, link=link)
                self.verificar_estado_preservado(antes)

    def test_f1a_16_mesmo_horario_em_dias_diferentes(self):
        primeiro = self.presencial(dia="segunda")
        segundo = self.presencial(dia="sexta")
        self.assertNotEqual(primeiro.id, segundo.id)

    def test_f1a_17_conflito_na_mesma_disciplina(self):
        antes = self.estado()
        with self.assertRaises(ConflitoDeHorario) as contexto:
            self.presencial(dia="terça", inicio="11:00", fim="13:00")
        self.assertEqual(contexto.exception.vinculo.disciplina.codigo, "DCC203")
        self.verificar_estado_preservado(antes)

    def test_f1a_18_conflito_entre_disciplinas(self):
        antes = self.estado()
        with self.assertRaises(ConflitoDeHorario) as contexto:
            self.presencial(usuario=self.caio, codigo="DCC203",
                            dia="terça", inicio="15:00", fim="17:00")
        self.assertEqual(contexto.exception.vinculo.disciplina.codigo, "MAT001")
        self.verificar_estado_preservado(antes)

    def test_f1a_19_conflito_entre_modalidades(self):
        antes = self.estado()
        with self.assertRaises(ConflitoDeHorario):
            self.online(dia="terça", inicio="11:00", fim="13:00")
        self.verificar_estado_preservado(antes)

    def test_f1a_20_horario_encostado_ao_fim_e_permitido(self):
        a = self.presencial(dia="terça", inicio="12:00", fim="14:00")
        self.assertIsNotNone(self.buscar(a.id))

    def test_f1a_21_horario_encostado_ao_inicio_e_permitido(self):
        a = self.presencial(dia="terça", inicio="08:00", fim="10:00")
        self.assertIsNotNone(self.buscar(a.id))

    def test_f1a_22_monitores_diferentes_podem_coincidir(self):
        a = self.presencial(usuario=self.caio, codigo="DCC203",
                            dia="terça", inicio="10:00", fim="12:00")
        vinculo, _ = self.buscar(a.id)
        self.assertEqual(vinculo.monitor.matricula, self.caio.matricula)

    def test_f1a_23_consultar_conflito_nao_altera_o_banco(self):
        antes = self.estado()
        candidato = AtendimentoPresencial("sábado", "10:00", "12:00", "CAD 3", "204")
        conflito = self.cadastro.encontrar_conflito(self.ana.matricula, candidato)
        self.assertIsNone(conflito)
        self.verificar_estado_preservado(antes)

    def test_f1a_24_persistencia_apos_reinicio(self):
        """Fluxo completo pela F1a; fecha e reabre um arquivo SQLite."""
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "teste_f1a.db"
            conexao1 = abrir_base(caminho)
            try:
                repo1 = RepositorioMonitorias(conexao1)
                carregar_demo(repo1)
                cadastro1 = CadastroMonitorias(repo1)
                ana = cadastro1.entrar("2026000001", "ana123")
                novo = cadastro1.cadastrar_presencial(
                    ana, "DCC203", "sexta", "10:00", "12:00", "ICEx", "1010"
                )
                id_salvo = novo.id
            finally:
                conexao1.close()

            conexao2 = abrir_base(caminho)
            try:
                repo2 = RepositorioMonitorias(conexao2)
                registro = repo2.buscar_atendimento(id_salvo)
                self.assertIsNotNone(registro)
                vinculo, lido = registro
                self.assertEqual(vinculo.disciplina.codigo, "DCC203")
                self.assertEqual(vinculo.monitor.matricula, "2026000001")
                self.assertEqual((lido.id, lido.dia, lido.inicio, lido.fim),
                                 (id_salvo, "sexta", "10:00", "12:00"))
            finally:
                conexao2.close()

    def test_f1a_25_administrador_sem_permissao(self):
        antes = self.estado()
        with self.assertRaises(PermissaoNegada):
            self.presencial(usuario=self.admin)
        self.verificar_estado_preservado(antes)

    def test_f1a_26_aluno_sem_permissao(self):
        antes = self.estado()
        with self.assertRaises(PermissaoNegada):
            self.online(usuario=self.aluno)
        self.verificar_estado_preservado(antes)

    def test_f1a_27_usuario_ausente_sem_permissao(self):
        antes = self.estado()
        with self.assertRaises(PermissaoNegada):
            self.cadastro.cadastrar_presencial(
                None, "DCC203", "sexta", "14:00", "16:00", "CAD 3", "204"
            )
        self.verificar_estado_preservado(antes)


class TestF1bVisualizar(BaseF1):
    """F1b: pares (Disciplina, Atendimento), autorização e leitura sem escrita."""

    def test_f1b_01_lista_pares_com_disciplina_e_id(self):
        itens = self.cadastro.listar_meus_atendimentos(self.ana)
        self.assertIsInstance(itens, tuple)
        self.assertEqual(len(itens), 2)
        for disciplina, atendimento in itens:
            self.assertIsInstance(disciplina, Disciplina)
            self.assertIsInstance(atendimento.id, int)

    def test_f1b_02_ordem_e_disciplinas_da_ana(self):
        itens = self.cadastro.listar_meus_atendimentos(self.ana)
        resumo = [(d.codigo, a.dia, a.inicio) for d, a in itens]
        self.assertEqual(resumo, [
            ("DCC203", "terça", "10:00"),
            ("MAT002", "quarta", "10:00"),
        ])

    def test_f1b_03_caio_tem_presencial_e_online(self):
        itens = self.cadastro.listar_meus_atendimentos(self.caio)
        self.assertEqual([(d.codigo, a.modalidade()) for d, a in itens], [
            ("MAT001", "presencial"), ("MAT001", "online")
        ])

    def test_f1b_04_monitor_sem_horarios_devolve_tupla_vazia(self):
        self.assertEqual(self.cadastro.listar_meus_atendimentos(self.duda), ())

    def test_f1b_05_novo_atendimento_aparece_na_consulta(self):
        novo = self.presencial()
        itens = self.cadastro.listar_meus_atendimentos(self.ana)
        self.assertIn(novo.id, [a.id for _, a in itens])
        self.assertEqual(len(itens), 3)

    def test_f1b_06_nao_mostra_horarios_de_outros_monitores(self):
        ids_ana = {a.id for _, a in self.cadastro.listar_meus_atendimentos(self.ana)}
        ids_caio = {a.id for _, a in self.cadastro.listar_meus_atendimentos(self.caio)}
        self.assertTrue(ids_ana.isdisjoint(ids_caio))

    def test_f1b_07_administrador_sem_permissao(self):
        antes = self.estado()
        with self.assertRaises(PermissaoNegada):
            self.cadastro.listar_meus_atendimentos(self.admin)
        self.verificar_estado_preservado(antes)

    def test_f1b_08_aluno_sem_permissao(self):
        antes = self.estado()
        with self.assertRaises(PermissaoNegada):
            self.cadastro.listar_meus_atendimentos(self.aluno)
        self.verificar_estado_preservado(antes)

    def test_f1b_09_consulta_nao_altera_dados(self):
        antes = self.estado()
        self.cadastro.listar_meus_atendimentos(self.ana)
        self.cadastro.listar_meus_atendimentos(self.caio)
        self.verificar_estado_preservado(antes)

    def test_f1b_10_monitor_nao_cadastrado(self):
        outro = Monitor("2099999999", "Outro", "outro@ufmg.br")
        with self.assertRaises(MatriculaNaoCadastrada):
            self.cadastro.listar_meus_atendimentos(outro)


class TestF1cAlterar(BaseF1):
    """F1c: alterar apenas dia/início/fim, preservando identidade e regras."""

    def test_f1c_01_alteracao_presencial_valida(self):
        id_alvo = self.id_inicial(self.ana.matricula, "DCC203", "terça")
        atualizado = self.cadastro.alterar_horario(
            self.ana, id_alvo, "sexta", "15:00", "17:00"
        )
        vinculo, gravado = self.buscar(id_alvo)
        self.assertEqual(atualizado.id, id_alvo)
        self.assertEqual((gravado.dia, gravado.inicio, gravado.fim),
                         ("sexta", "15:00", "17:00"))
        self.assertEqual(vinculo.disciplina.codigo, "DCC203")
        self.assertEqual(gravado.modalidade(), "presencial")
        self.assertEqual(gravado.local(), "CAD 3, sala 204")
        self.assertEqual(gravado.registrado_em, date.today())

    def test_f1c_02_alteracao_online_preserva_plataforma_e_link(self):
        id_alvo = self.id_inicial(self.caio.matricula, "MAT001", "quinta")
        _, anterior = self.buscar(id_alvo)
        atualizado = self.cadastro.alterar_horario(
            self.caio, id_alvo, "sábado", "18:00", "19:00"
        )
        self.assertEqual(atualizado.id, id_alvo)
        _, gravado = self.buscar(id_alvo)
        self.assertEqual(gravado.modalidade(), "online")
        self.assertEqual(gravado.local(), anterior.local())
        self.assertEqual((gravado.dia, gravado.inicio, gravado.fim),
                         ("sábado", "18:00", "19:00"))

    def test_f1c_03_ignora_proprio_atendimento_no_conflito(self):
        id_alvo = self.id_inicial(self.ana.matricula, "DCC203", "terça")
        atualizado = self.cadastro.alterar_horario(
            self.ana, id_alvo, "terça", "11:00", "13:00"
        )
        self.assertEqual((atualizado.inicio, atualizado.fim), ("11:00", "13:00"))

    def test_f1c_04_conflito_na_mesma_disciplina(self):
        """Cria outro horário na mesma disciplina e tenta sobrepor a ele."""
        alvo = self.presencial(dia="sexta", inicio="14:00", fim="16:00")
        self.online(dia="sexta", inicio="19:00", fim="20:00")
        antes = self.estado()
        with self.assertRaises(ConflitoDeHorario):
            self.cadastro.alterar_horario(
                self.ana, alvo.id, "sexta", "19:30", "20:30"
            )
        self.verificar_estado_preservado(antes)

    def test_f1c_05_conflito_entre_disciplinas(self):
        id_alvo = self.id_inicial(self.ana.matricula, "MAT002", "quarta")
        antes = self.estado()
        with self.assertRaises(ConflitoDeHorario) as contexto:
            self.cadastro.alterar_horario(
                self.ana, id_alvo, "terça", "11:00", "13:00"
            )
        self.assertEqual(contexto.exception.vinculo.disciplina.codigo, "DCC203")
        self.verificar_estado_preservado(antes)

    def test_f1c_06_conflito_entre_modalidades(self):
        id_online = self.id_inicial(self.caio.matricula, "MAT001", "quinta")
        antes = self.estado()
        with self.assertRaises(ConflitoDeHorario):
            self.cadastro.alterar_horario(
                self.caio, id_online, "terça", "15:00", "17:00"
            )
        self.verificar_estado_preservado(antes)

    def test_f1c_07_outro_monitor_nao_pode_alterar(self):
        id_ana = self.id_inicial(self.ana.matricula, "DCC203", "terça")
        antes = self.estado()
        with self.assertRaises(PermissaoNegada):
            self.cadastro.alterar_horario(
                self.caio, id_ana, "sexta", "14:00", "16:00"
            )
        self.verificar_estado_preservado(antes)

    def test_f1c_08_administrador_nao_pode_alterar(self):
        id_ana = self.id_inicial(self.ana.matricula, "DCC203", "terça")
        antes = self.estado()
        with self.assertRaises(PermissaoNegada):
            self.cadastro.alterar_horario(
                self.admin, id_ana, "sexta", "14:00", "16:00"
            )
        self.verificar_estado_preservado(antes)

    def test_f1c_09_aluno_nao_pode_alterar(self):
        id_ana = self.id_inicial(self.ana.matricula, "DCC203", "terça")
        antes = self.estado()
        with self.assertRaises(PermissaoNegada):
            self.cadastro.alterar_horario(
                self.aluno, id_ana, "sexta", "14:00", "16:00"
            )
        self.verificar_estado_preservado(antes)

    def test_f1c_10_id_inexistente(self):
        antes = self.estado()
        with self.assertRaises(AtendimentoInexistente):
            self.cadastro.alterar_horario(
                self.ana, 99999, "sexta", "14:00", "16:00"
            )
        self.verificar_estado_preservado(antes)

    def test_f1c_11_id_invalido(self):
        antes = self.estado()
        for id_ruim in (0, -1, True, "1", None):
            with self.subTest(id_ruim=id_ruim):
                with self.assertRaises(DadosInvalidos):
                    self.cadastro.alterar_horario(
                        self.ana, id_ruim, "sexta", "14:00", "16:00"
                    )
                self.verificar_estado_preservado(antes)

    def test_f1c_12_dia_e_horarios_invalidos(self):
        id_alvo = self.id_inicial(self.ana.matricula, "DCC203", "terça")
        antes = self.estado()
        casos = (("domingo", "14:00", "16:00"),
                 ("sexta", "15:00", "15:00"),
                 ("sexta", "18:00", "17:00"),
                 ("sexta", "25:00", "26:00"))
        for dia, inicio, fim in casos:
            with self.subTest(dia=dia, inicio=inicio, fim=fim):
                with self.assertRaises(DadosInvalidos):
                    self.cadastro.alterar_horario(
                        self.ana, id_alvo, dia, inicio, fim
                    )
                self.verificar_estado_preservado(antes)

    def test_f1c_13_horarios_encostados_sao_permitidos(self):
        id_alvo = self.id_inicial(self.ana.matricula, "MAT002", "quarta")
        atualizado = self.cadastro.alterar_horario(
            self.ana, id_alvo, "terça", "12:00", "14:00"
        )
        self.assertEqual((atualizado.dia, atualizado.inicio), ("terça", "12:00"))

    def test_f1c_14_alterar_nao_muda_outros_atendimentos(self):
        id_alvo = self.id_inicial(self.ana.matricula, "DCC203", "terça")
        outro_id = self.id_inicial(self.ana.matricula, "MAT002", "quarta")
        _, outro_antes = self.buscar(outro_id)
        self.cadastro.alterar_horario(
            self.ana, id_alvo, "sexta", "14:00", "16:00"
        )
        _, outro_depois = self.buscar(outro_id)
        self.assertEqual(
            (outro_depois.id, outro_depois.dia, outro_depois.inicio,
             outro_depois.fim, outro_depois.local()),
            (outro_antes.id, outro_antes.dia, outro_antes.inicio,
             outro_antes.fim, outro_antes.local()),
        )


class TestF1dRemover(BaseF1):
    """F1d: remoção por ID, titularidade e preservação dos outros registros."""

    def test_f1d_01_remocao_valida_retorna_none(self):
        alvo = self.presencial()
        resultado = self.cadastro.remover_atendimento(self.ana, alvo.id)
        self.assertIsNone(resultado)
        self.assertIsNone(self.buscar(alvo.id))

    def test_f1d_02_outro_monitor_nao_pode_remover(self):
        alvo = self.presencial()
        antes = self.estado()
        with self.assertRaises(PermissaoNegada):
            self.cadastro.remover_atendimento(self.caio, alvo.id)
        self.verificar_estado_preservado(antes)

    def test_f1d_03_administrador_nao_pode_remover(self):
        alvo = self.presencial()
        antes = self.estado()
        with self.assertRaises(PermissaoNegada):
            self.cadastro.remover_atendimento(self.admin, alvo.id)
        self.verificar_estado_preservado(antes)

    def test_f1d_04_aluno_nao_pode_remover(self):
        alvo = self.presencial()
        antes = self.estado()
        with self.assertRaises(PermissaoNegada):
            self.cadastro.remover_atendimento(self.aluno, alvo.id)
        self.verificar_estado_preservado(antes)

    def test_f1d_05_id_inexistente(self):
        antes = self.estado()
        with self.assertRaises(AtendimentoInexistente):
            self.cadastro.remover_atendimento(self.ana, 99999)
        self.verificar_estado_preservado(antes)

    def test_f1d_06_id_invalido(self):
        antes = self.estado()
        for id_ruim in (0, -1, True, "1", None):
            with self.subTest(id_ruim=id_ruim):
                with self.assertRaises(DadosInvalidos):
                    self.cadastro.remover_atendimento(self.ana, id_ruim)
                self.verificar_estado_preservado(antes)

    def test_f1d_07_segunda_remocao_e_rejeitada(self):
        alvo = self.presencial()
        self.cadastro.remover_atendimento(self.ana, alvo.id)
        antes = self.estado()
        with self.assertRaises(AtendimentoInexistente):
            self.cadastro.remover_atendimento(self.ana, alvo.id)
        self.verificar_estado_preservado(antes)

    def test_f1d_08_preserva_vinculo_e_demais_horarios(self):
        alvo = self.presencial()
        id_outro = self.id_inicial(self.ana.matricula, "DCC203", "terça")
        self.cadastro.remover_atendimento(self.ana, alvo.id)
        self.assertIsNotNone(self.repositorio.buscar_vinculo("2026000001", "DCC203"))
        self.assertIsNotNone(self.buscar(id_outro))
        self.assertEqual(len(self.cadastro.listar_meus_atendimentos(self.ana)), 2)

    def test_f1d_09_id_removido_nao_e_reaproveitado(self):
        primeiro = self.presencial()
        self.cadastro.remover_atendimento(self.ana, primeiro.id)
        segundo = self.online()
        self.assertGreater(segundo.id, primeiro.id)
        self.assertIsNone(self.buscar(primeiro.id))

    def test_f1d_10_remove_atendimento_online(self):
        id_online = self.id_inicial(self.caio.matricula, "MAT001", "quinta")
        id_presencial = self.id_inicial(self.caio.matricula, "MAT001", "terça")
        self.cadastro.remover_atendimento(self.caio, id_online)
        self.assertIsNone(self.buscar(id_online))
        self.assertIsNotNone(self.buscar(id_presencial))


if __name__ == "__main__":
    unittest.main()
