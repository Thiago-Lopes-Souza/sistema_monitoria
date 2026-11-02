"""Testes Frente B: monitor, disciplina, vinculo e cadastro de atendimentos."""


import unittest

from monitorias.dominio.monitor import Monitor
from monitorias.dominio.disciplina import Disciplina
from monitorias.dominio.cadastro import CadastroMonitorias
from monitorias.dominio.atendimento import AtendimentoOnline, AtendimentoPresencial
from monitorias.dominio.excecoes import (ConflitoDeHorario, DadosInvalidos, DisciplinaForaDoEscopo, MatriculaNaoCadastrada, VinculoInexistente)

# -- Criação de Classes --

class TestPreparacaoFrenteB(unittest.TestCase):
    # Disciplina, Monitor e criacao de vinculos.

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
        monitor = Monitor(" 2026000002 ", "  Thiago  ", "thiago@ufmg.br")
        self.assertEqual(monitor.matricula, "2026000002")
        self.assertEqual(monitor.nome, "Thiago")

    def test_setter_email_aceita_e_normaliza_email(self):
        self.monitor.email = "  NOVO@UFMG.BR  "
        self.assertEqual(self.monitor.email, "novo@ufmg.br")

    def test_setter_email_invalido_nao_altera(self):
        email_anterior = self.monitor.email
        with self.assertRaises(DadosInvalidos):
            self.monitor.email = "ana@gmail.com"
        self.assertEqual(self.monitor.email, email_anterior)

    def test_matricula_e_nome_do_monitor_read_only(self):
        with self.assertRaises(AttributeError):
            self.monitor.matricula = "9999999999"
        with self.assertRaises(AttributeError):
            self.monitor.nome = "Outro nome"

    def test_adicionar_disciplina_duplicada(self):
        self.cadastro.adicionar_disciplina(self.disciplina)
        with self.assertRaises(DadosInvalidos):
            self.cadastro.adicionar_disciplina(Disciplina("DCC203", "Outro nome"))

    def test_adicionar_monitor_duplicado(self):
        self.cadastro.adicionar_monitor(self.monitor)
        outro = Monitor("2026000001", "Outra Ana", "outra@ufmg.br")
        with self.assertRaises(DadosInvalidos):
            self.cadastro.adicionar_monitor(outro)

    def test_criar_vinculo(self):
        self.cadastro.adicionar_monitor(self.monitor)
        self.cadastro.adicionar_disciplina(self.disciplina)
        vinculo = self.cadastro.vincular(self.monitor.matricula, self.disciplina.codigo)
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

# -- Funcionalidade --

class TestCadastrarAtendimento(unittest.TestCase):

    def setUp(self):
        
        self.cadastro = CadastroMonitorias()
        self.ana = Monitor("2026000001", "Ana", "ana@ufmg.br")
        self.thiago = Monitor("2026000002", "Thiago", "thiago@ufmg.br")
        self.dcc = Disciplina("DCC203", "Engenharia de Computação")
        self.mat = Disciplina("MAT001", "Calculo I")
        self.fis = Disciplina("FIS069", "Fisica III")

        for monitor in (self.ana, self.thiago):
            self.cadastro.adicionar_monitor(monitor)
        for disciplina in (self.dcc, self.mat, self.fis):
            self.cadastro.adicionar_disciplina(disciplina)

        self.ana_dcc = self.cadastro.vincular("2026000001", "DCC203")
        self.ana_mat = self.cadastro.vincular("2026000001", "MAT001")
        self.thiago_mat = self.cadastro.vincular("2026000002", "MAT001")
        self.vinculos = (self.ana_dcc, self.ana_mat, self.thiago_mat)

    @staticmethod
    def presencial(dia="terça", inicio="14:00", fim="16:00"):
        return AtendimentoPresencial(dia, inicio, fim, "CAD 3", "204")

    @staticmethod
    def online(dia="quinta", inicio="19:00", fim="20:00"):
        return AtendimentoOnline(dia, inicio, fim, "Google Meet", "https://meet.exemplo/abc")

    def estado(self):
        # Estado dos atendimentos para comparar antes e depois.
        return tuple(vinculo.atendimentos for vinculo in self.vinculos)

    # CADASTRO
    def test_cadastro_valido(self):
        atendimento = self.presencial("quinta", "14:00", "16:00")
        retorno = self.cadastro.cadastrar_atendimento("2026000001", "DCC203", atendimento)
        self.assertIs(retorno, atendimento)
        self.assertEqual(self.ana_dcc.atendimentos, (atendimento,))

    # EXCECOES E FORMATACOES
    def test_matricula_inexistente_lanca_excecao(self):
        antes = self.estado()
        with self.assertRaises(MatriculaNaoCadastrada):
            self.cadastro.cadastrar_atendimento("2099999999", "DCC203", self.presencial())
        self.assertEqual(self.estado(), antes)

    def test_disciplina_fora_do_escopo_lanca_excecao(self):
        antes = self.estado()
        with self.assertRaises(DisciplinaForaDoEscopo):
            self.cadastro.cadastrar_atendimento("2026000001", "DCC999", self.presencial())
        self.assertEqual(self.estado(), antes)

    def test_codigo_mal_formatado_lanca_dados_invalidos(self):
        antes = self.estado()
        with self.assertRaises(DadosInvalidos):
            self.cadastro.cadastrar_atendimento("2026000001", "CODIGO-ERRADO", self.presencial())
        self.assertEqual(self.estado(), antes)

    def test_monitor_sem_vinculo(self):
        antes = self.estado()
        with self.assertRaises(VinculoInexistente):
            self.cadastro.cadastrar_atendimento("2026000001", "FIS069", self.presencial())
        self.assertEqual(self.estado(), antes)

    def test_codigo_em_minusculas_e_aceito(self):
        atendimento = self.presencial()
        self.cadastro.cadastrar_atendimento("2026000001", "dcc203", atendimento)
        self.assertEqual(self.ana_dcc.atendimentos, (atendimento,))

    def test_matricula_com_espacos_e_aceita(self):
        atendimento = self.presencial()
        self.cadastro.cadastrar_atendimento(" 2026000001 ", "DCC203", atendimento)
        self.assertEqual(self.ana_dcc.atendimentos, (atendimento,))

    # CONFLITOS DE ATENDIMENTOS
    def test_dois_atendimentos_em_dias_diferentes(self):
        a1 = self.presencial("terça", "14:00", "16:00")
        a2 = self.presencial("quinta", "14:00", "16:00")
        self.cadastro.cadastrar_atendimento("2026000001", "DCC203", a1)
        self.cadastro.cadastrar_atendimento("2026000001", "DCC203", a2)
        self.assertEqual(self.ana_dcc.atendimentos, (a1, a2))

    def test_conflito_no_mesmo_vinculo(self):
        existente = self.presencial("terça", "14:00", "16:00")
        self.cadastro.cadastrar_atendimento("2026000001", "DCC203", existente)
        antes = self.estado()
        with self.assertRaises(ConflitoDeHorario):
            self.cadastro.cadastrar_atendimento("2026000001", "DCC203", self.presencial("terça", "15:00", "17:00"))
        self.assertEqual(self.estado(), antes)

    def test_conflito_entre_disciplinas(self):
        existente = self.presencial("terça", "14:00", "16:00")
        self.cadastro.cadastrar_atendimento("2026000001", "MAT001", existente)
        antes = self.estado()
        with self.assertRaises(ConflitoDeHorario) as contexto:
            self.cadastro.cadastrar_atendimento("2026000001", "DCC203", self.presencial("terça", "15:00", "17:00"))
        self.assertIs(contexto.exception.vinculo, self.ana_mat)
        self.assertIs(contexto.exception.atendimento, existente)
        self.assertEqual(self.estado(), antes)

    def test_conflito_entre_modalidades(self):
        self.cadastro.cadastrar_atendimento("2026000001", "MAT001", self.online("terça", "14:00", "16:00"))
        with self.assertRaises(ConflitoDeHorario):
            self.cadastro.cadastrar_atendimento("2026000001", "DCC203", self.presencial("terça", "15:00", "17:00"))

    def test_horarios_podem_encostar_pelo_inicio(self):
        a1 = self.presencial("terça", "14:00", "16:00")
        a2 = self.presencial("terça", "12:00", "14:00")
        self.cadastro.cadastrar_atendimento("2026000001", "MAT001", a1)
        self.cadastro.cadastrar_atendimento("2026000001", "DCC203", a2)
        self.assertEqual(len(self.ana_dcc.atendimentos), 1)

    def test_monitores_diferentes_podem_atender_no_mesmo_horario(self):
        a1 = self.presencial("terça", "14:00", "16:00")
        a2 = self.presencial("terça", "14:00", "16:00")
        self.cadastro.cadastrar_atendimento("2026000001", "MAT001", a1)
        self.cadastro.cadastrar_atendimento("2026000002", "MAT001", a2)
        self.assertEqual(self.ana_mat.atendimentos, (a1,))
        self.assertEqual(self.thiago_mat.atendimentos, (a2,))

    def test_encontrar_conflito_sem_sobreposicao(self):
        # Cadastra um atendimento existente
        atendimento1 = self.presencial("terça", "10:00", "12:00")
        self.cadastro.cadastrar_atendimento("2026000001", "DCC203", atendimento1)

        antes = self.estado()

        atendimento2 = self.presencial("terça", "14:00", "16:00")

        conflito = self.cadastro.encontrar_conflito("2026000001", atendimento2)
        self.assertIsNone(conflito)
        self.assertEqual(self.estado(), antes)


if __name__ == "__main__":
    unittest.main()