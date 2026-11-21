"""Testes da Frente B: entidades, vínculos e cadastro de atendimentos (F1a)."""

import unittest

from monitorias.dominio.monitor import Monitor
from monitorias.dominio.disciplina import Disciplina
from monitorias.dominio.cadastro import CadastroMonitorias
from monitorias.dominio.atendimento import (
    AtendimentoOnline,
    AtendimentoPresencial,
)
from monitorias.dominio.excecoes import (
    ConflitoDeHorario,
    DadosInvalidos,
    DisciplinaForaDoEscopo,
    MatriculaNaoCadastrada,
    VinculoInexistente,
)


# ============================================================
# PREPARAÇÃO: DISCIPLINA, MONITOR E VINCULO
# ============================================================

class TestPreparacaoFrenteB(unittest.TestCase):

    def setUp(self):
        self.cadastro = CadastroMonitorias()
        self.monitor = Monitor("2026000001", "Ana", "ana@ufmg.br")
        self.disciplina = Disciplina("DCC203", "Engenharia de Computação")

    def test_disciplina_normaliza_codigo_e_nome(self):
        disciplina = Disciplina("dcc203", "  Computação  ")
        self.assertEqual(disciplina.codigo, "DCC203")
        self.assertEqual(disciplina.nome, "Computação")

    def test_disciplinas_com_mesmo_codigo_sao_iguais(self):
        outra = Disciplina("DCC203", "Outro nome")
        self.assertEqual(self.disciplina, outra)
        self.assertEqual(hash(self.disciplina), hash(outra))

    def test_codigo_e_nome_da_disciplina_read_only(self):
        with self.assertRaises(AttributeError):
            self.disciplina.codigo = "MAT001"
        with self.assertRaises(AttributeError):
            self.disciplina.nome = "Outro nome"

    def test_monitor_normaliza_matricula_e_nome(self):
        monitor = Monitor(
            " 2026000002 ", "  Thiago  ", "thiago@ufmg.br"
        )
        self.assertEqual(monitor.matricula, "2026000002")
        self.assertEqual(monitor.nome, "Thiago")

    def test_setter_email_aceita_e_normaliza(self):
        self.monitor.email = "  NOVO@UFMG.BR  "
        self.assertEqual(self.monitor.email, "novo@ufmg.br")

    def test_setter_email_invalido_preserva_anterior(self):
        anterior = self.monitor.email

        with self.assertRaises(DadosInvalidos):
            self.monitor.email = "ana@gmail.com"

        self.assertEqual(self.monitor.email, anterior)

    def test_matricula_e_nome_do_monitor_read_only(self):
        with self.assertRaises(AttributeError):
            self.monitor.matricula = "9999999999"

        with self.assertRaises(AttributeError):
            self.monitor.nome = "Outro nome"

    def test_adicionar_disciplina_duplicada(self):
        self.cadastro.adicionar_disciplina(self.disciplina)

        with self.assertRaises(DadosInvalidos):
            self.cadastro.adicionar_disciplina(
                Disciplina("DCC203", "Outro nome")
            )

    def test_adicionar_monitor_duplicado(self):
        self.cadastro.adicionar_monitor(self.monitor)

        with self.assertRaises(DadosInvalidos):
            self.cadastro.adicionar_monitor(
                Monitor("2026000001", "Outra Ana", "outra@ufmg.br")
            )

    def test_criar_vinculo(self):
        self.cadastro.adicionar_monitor(self.monitor)
        self.cadastro.adicionar_disciplina(self.disciplina)

        vinculo = self.cadastro.vincular(
            self.monitor.matricula, self.disciplina.codigo
        )

        self.assertIs(vinculo.monitor, self.monitor)
        self.assertIs(vinculo.disciplina, self.disciplina)
        self.assertEqual(vinculo.atendimentos, ())

    def test_nao_permite_vinculo_duplicado(self):
        self.cadastro.adicionar_monitor(self.monitor)
        self.cadastro.adicionar_disciplina(self.disciplina)

        vinculo = self.cadastro.vincular("2026000001", "DCC203")

        with self.assertRaises(DadosInvalidos):
            self.cadastro.vincular("2026000001", "dcc203")

        self.assertEqual(vinculo.atendimentos, ())

    def test_vincular_monitor_nao_cadastrado(self):
        self.cadastro.adicionar_disciplina(self.disciplina)

        with self.assertRaises(MatriculaNaoCadastrada):
            self.cadastro.vincular("2099999999", "DCC203")

    def test_vincular_disciplina_fora_do_sistema(self):
        self.cadastro.adicionar_monitor(self.monitor)

        with self.assertRaises(DisciplinaForaDoEscopo):
            self.cadastro.vincular("2026000001", "DCC999")


# ============================================================
# F1a: CADASTRAR ATENDIMENTOS PRESENCIAIS E ONLINE
# ============================================================

class TestCadastrarAtendimento(unittest.TestCase):

    def setUp(self):
        self.cadastro = CadastroMonitorias()

        self.ana = Monitor(
            "2026000001", "Ana", "ana@ufmg.br"
        )
        self.thiago = Monitor(
            "2026000002", "Thiago", "thiago@ufmg.br"
        )

        self.dcc = Disciplina(
            "DCC203", "Engenharia de Computação"
        )
        self.mat = Disciplina("MAT001", "Cálculo I")
        self.fis = Disciplina("FIS069", "Física III")

        for monitor in (self.ana, self.thiago):
            self.cadastro.adicionar_monitor(monitor)

        for disciplina in (self.dcc, self.mat, self.fis):
            self.cadastro.adicionar_disciplina(disciplina)

        self.ana_dcc = self.cadastro.vincular(
            "2026000001", "DCC203"
        )
        self.ana_mat = self.cadastro.vincular(
            "2026000001", "MAT001"
        )
        self.thiago_mat = self.cadastro.vincular(
            "2026000002", "MAT001"
        )

        self.vinculos = (
            self.ana_dcc,
            self.ana_mat,
            self.thiago_mat,
        )

    # Auxiliares dos testes: usam apenas a API pública.

    def presencial(
        self,
        matricula="2026000001",
        codigo="DCC203",
        dia="terça",
        inicio="14:00",
        fim="16:00",
        predio="CAD 3",
        sala="204",
    ):
        return self.cadastro.cadastrar_presencial(
            matricula, codigo, dia, inicio, fim, predio, sala
        )

    def online(
        self,
        matricula="2026000001",
        codigo="DCC203",
        dia="quinta",
        inicio="19:00",
        fim="20:00",
        plataforma="Google Meet",
        link="https://meet.exemplo/abc",
    ):
        return self.cadastro.cadastrar_online(
            matricula, codigo, dia, inicio, fim, plataforma, link
        )

    def estado(self):
        """Fotografia dos horários para verificar preservação."""
        return tuple(v.atendimentos for v in self.vinculos)

    # --------------------------------------------------------
    # CADASTROS VÁLIDOS
    # --------------------------------------------------------

    def test_f1a_01_cadastro_presencial_valido(self):
        atendimento = self.presencial()

        self.assertIsInstance(atendimento, AtendimentoPresencial)
        self.assertEqual(atendimento.dia, "terça")
        self.assertEqual(atendimento.inicio, "14:00")
        self.assertEqual(atendimento.fim, "16:00")
        self.assertEqual(atendimento.modalidade(), "presencial")
        self.assertEqual(atendimento.local(), "CAD 3, sala 204")

        self.assertEqual(len(self.ana_dcc.atendimentos), 1)
        self.assertIs(self.ana_dcc.atendimentos[0], atendimento)
        self.assertEqual(self.ana_mat.atendimentos, ())

    def test_f1a_02_cadastro_online_valido(self):
        atendimento = self.online()

        self.assertIsInstance(atendimento, AtendimentoOnline)
        self.assertEqual(atendimento.dia, "quinta")
        self.assertEqual(atendimento.inicio, "19:00")
        self.assertEqual(atendimento.fim, "20:00")
        self.assertEqual(atendimento.modalidade(), "online")
        self.assertEqual(
            atendimento.local(),
            "Google Meet: https://meet.exemplo/abc",
        )

        self.assertIs(self.ana_dcc.atendimentos[0], atendimento)

    def test_f1a_03_normaliza_dia_horario_e_local(self):
        atendimento = self.presencial(
            dia="  TERÇA  ",
            inicio="9:00",
            fim="11:00",
            predio=" CAD 3 ",
            sala=" 204 ",
        )

        self.assertEqual(atendimento.dia, "terça")
        self.assertEqual(atendimento.inicio, "09:00")
        self.assertEqual(atendimento.fim, "11:00")
        self.assertEqual(atendimento.predio, "CAD 3")
        self.assertEqual(atendimento.sala, "204")

    def test_f1a_04_link_preserva_maiusculas(self):
        atendimento = self.online(
            link="https://meet.exemplo/SalaABC"
        )

        self.assertEqual(
            atendimento.link, "https://meet.exemplo/SalaABC"
        )

    def test_f1a_05_codigo_minusculo_e_aceito(self):
        atendimento = self.presencial(codigo=" dcc203 ")

        self.assertIs(self.ana_dcc.atendimentos[0], atendimento)

    def test_f1a_06_matricula_com_espacos_e_aceita(self):
        atendimento = self.presencial(
            matricula=" 2026000001 "
        )

        self.assertIs(self.ana_dcc.atendimentos[0], atendimento)

    def test_f1a_07_cada_cadastro_cria_novo_objeto(self):
        primeiro = self.presencial()
        segundo = self.online()

        self.assertIsNot(primeiro, segundo)
        self.assertEqual(len(self.ana_dcc.atendimentos), 2)

    # --------------------------------------------------------
    # REJEIÇÕES E PRESERVAÇÃO DO ESTADO
    # --------------------------------------------------------

    def test_f1a_08_matricula_inexistente(self):
        antes = self.estado()

        with self.assertRaises(MatriculaNaoCadastrada):
            self.presencial(matricula="2099999999")

        self.assertEqual(self.estado(), antes)

    def test_f1a_09_disciplina_fora_do_escopo(self):
        antes = self.estado()

        with self.assertRaises(DisciplinaForaDoEscopo):
            self.presencial(codigo="DCC999")

        self.assertEqual(self.estado(), antes)

    def test_f1a_10_codigo_mal_formatado(self):
        antes = self.estado()

        with self.assertRaises(DadosInvalidos):
            self.presencial(codigo="CODIGO-ERRADO")

        self.assertEqual(self.estado(), antes)

    def test_f1a_11_monitor_sem_vinculo(self):
        antes = self.estado()

        with self.assertRaises(VinculoInexistente):
            self.presencial(codigo="FIS069")

        self.assertEqual(self.estado(), antes)

    def test_f1a_12_dia_invalido(self):
        antes = self.estado()

        for dia in ("domingo", "", "dia-inexistente"):
            with self.subTest(dia=dia):
                with self.assertRaises(DadosInvalidos):
                    self.presencial(dia=dia)

                self.assertEqual(self.estado(), antes)

    def test_f1a_13_horarios_invalidos(self):
        antes = self.estado()

        casos = (
            ("16:00", "14:00"),  # Início após o fim
            ("14:00", "14:00"),  # Duração zero
            ("25:00", "26:00"),  # Horário inexistente
            ("14h00", "16:00"),  # Formato inválido
        )

        for inicio, fim in casos:
            with self.subTest(inicio=inicio, fim=fim):
                with self.assertRaises(DadosInvalidos):
                    self.presencial(inicio=inicio, fim=fim)

                self.assertEqual(self.estado(), antes)

    def test_f1a_14_local_presencial_invalido(self):
        antes = self.estado()

        for predio, sala in (("", "204"), ("CAD 3", "  ")):
            with self.subTest(predio=predio, sala=sala):
                with self.assertRaises(DadosInvalidos):
                    self.presencial(predio=predio, sala=sala)

                self.assertEqual(self.estado(), antes)

    def test_f1a_15_local_online_invalido(self):
        antes = self.estado()

        casos = (
            ("", "https://meet.exemplo/abc"),
            ("Google Meet", "http://meet.exemplo/abc"),
            ("Google Meet", ""),
        )

        for plataforma, link in casos:
            with self.subTest(plataforma=plataforma, link=link):
                with self.assertRaises(DadosInvalidos):
                    self.online(plataforma=plataforma, link=link)

                self.assertEqual(self.estado(), antes)

    # --------------------------------------------------------
    # CONFLITOS DE HORÁRIO
    # --------------------------------------------------------

    def test_f1a_16_dias_diferentes_sao_permitidos(self):
        primeiro = self.presencial(
            dia="terça", inicio="14:00", fim="16:00"
        )
        segundo = self.presencial(
            dia="quinta", inicio="14:00", fim="16:00"
        )

        self.assertEqual(
            self.ana_dcc.atendimentos,
            (primeiro, segundo),
        )

    def test_f1a_17_conflito_no_mesmo_vinculo(self):
        existente = self.presencial()
        antes = self.estado()

        with self.assertRaises(ConflitoDeHorario):
            self.presencial(
                dia="terça", inicio="15:00", fim="17:00"
            )

        self.assertEqual(self.estado(), antes)
        self.assertIs(self.ana_dcc.atendimentos[0], existente)

    def test_f1a_18_conflito_entre_disciplinas(self):
        existente = self.presencial(
            codigo="MAT001",
            dia="terça",
            inicio="14:00",
            fim="16:00",
        )
        antes = self.estado()

        with self.assertRaises(ConflitoDeHorario) as contexto:
            self.presencial(
                codigo="DCC203",
                dia="terça",
                inicio="15:00",
                fim="17:00",
            )

        self.assertIs(contexto.exception.vinculo, self.ana_mat)
        self.assertIs(contexto.exception.atendimento, existente)
        self.assertEqual(self.estado(), antes)

    def test_f1a_19_conflito_entre_modalidades(self):
        self.online(
            codigo="MAT001",
            dia="terça",
            inicio="14:00",
            fim="16:00",
        )
        antes = self.estado()

        with self.assertRaises(ConflitoDeHorario):
            self.presencial(
                codigo="DCC203",
                dia="terça",
                inicio="15:00",
                fim="17:00",
            )

        self.assertEqual(self.estado(), antes)

    def test_f1a_20_horarios_encostados_pelo_inicio(self):
        self.presencial(
            codigo="MAT001",
            dia="terça",
            inicio="14:00",
            fim="16:00",
        )

        novo = self.presencial(
            codigo="DCC203",
            dia="terça",
            inicio="12:00",
            fim="14:00",
        )

        self.assertIs(self.ana_dcc.atendimentos[0], novo)

    def test_f1a_21_horarios_encostados_pelo_fim(self):
        self.presencial(
            codigo="MAT001",
            dia="terça",
            inicio="14:00",
            fim="16:00",
        )

        novo = self.online(
            codigo="DCC203",
            dia="terça",
            inicio="16:00",
            fim="18:00",
        )

        self.assertIs(self.ana_dcc.atendimentos[0], novo)

    def test_f1a_22_monitores_distintos_mesmo_horario(self):
        primeiro = self.presencial(
            matricula="2026000001",
            codigo="MAT001",
        )
        segundo = self.presencial(
            matricula="2026000002",
            codigo="MAT001",
        )

        self.assertIs(self.ana_mat.atendimentos[0], primeiro)
        self.assertIs(self.thiago_mat.atendimentos[0], segundo)

    def test_f1a_23_encontrar_conflito_sem_sobreposicao(self):
        self.presencial(
            dia="terça", inicio="10:00", fim="12:00"
        )

        antes = self.estado()
        candidato = AtendimentoPresencial(
            "terça", "14:00", "16:00", "CAD 3", "204"
        )

        conflito = self.cadastro.encontrar_conflito(
            "2026000001", candidato
        )

        self.assertIsNone(conflito)
        self.assertEqual(self.estado(), antes)


if __name__ == "__main__":
    unittest.main()
