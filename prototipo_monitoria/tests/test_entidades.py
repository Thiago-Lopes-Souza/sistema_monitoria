"""Testes das entidades Disciplina e Monitor, independentes do banco SQLite.
Executar dentro de prototipo_monitoria/:
    python -m unittest discover -s tests -p 'test_entidades.py' -v
"""

import unittest

from monitorias.dominio.disciplina import Disciplina
from monitorias.dominio.excecoes import DadosInvalidos
from monitorias.dominio.monitor import Monitor


class TestEntidadesFrenteB(unittest.TestCase):
    def setUp(self):
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


if __name__ == "__main__":
    unittest.main()
