"""Testes da F2 (consultar monitorias) integrada ao repositório SQLite.

Preserva os 24 cenários do protótipo: filtros, situações de consulta,
ordenação, normalização, imutabilidade e ausência de efeitos colaterais.
Cada teste utiliza sua própria base SQLite em memória.
"""

import dataclasses
import unittest
from datetime import date

from monitorias.dominio.atendimento import AtendimentoOnline, AtendimentoPresencial
from monitorias.dominio.cadastro import CadastroMonitorias
from monitorias.dominio.consulta import SituacaoConsulta
from monitorias.dominio.disciplina import Disciplina
from monitorias.dominio.excecoes import DadosInvalidos, DisciplinaForaDoEscopo
from monitorias.dominio.monitor import Monitor
from monitorias.persistencia.conexao import EM_MEMORIA, abrir_base
from monitorias.persistencia.repositorio import RepositorioMonitorias


DATA = date(2026, 10, 1)
HASH_TESTE = b"hash-ficticio"
SAL_TESTE = b"sal-ficticio"


class TestConsultarMonitorias(unittest.TestCase):
    """F2: cenário independente com cinco monitores e quatro disciplinas."""

    def setUp(self):
        self.conexao = abrir_base(EM_MEMORIA)
        self.addCleanup(self.conexao.close)
        self.repo = RepositorioMonitorias(self.conexao)
        self.cadastro = CadastroMonitorias(self.repo)

        # A F2 é pública; não requer autenticação. Para preparar o cenário,
        # gravamos diretamente pela API pública do repositório em transação.
        with self.repo.transacao():
            for codigo, nome in (
                ("AAA111", "Disciplina A"),
                ("BBB222", "Disciplina B"),
                ("CCC333", "Disciplina C"),
                ("DDD444", "Disciplina D"),
            ):
                self.repo.inserir_disciplina(Disciplina(codigo, nome))

            for matricula, nome, email in (
                ("1", "Bia Teste", "bia.teste@ufmg.br"),
                ("2", "Davi Teste", "davi.teste@ufmg.br"),
                ("3", "Eva Teste", "eva.teste@ufmg.br"),
                ("4", "Fabio Teste", "fabio.teste@ufmg.br"),
                ("5", "Gabi Teste", "gabi.teste@ufmg.br"),
            ):
                self.repo.inserir_monitor(
                    Monitor(matricula, nome, email), HASH_TESTE, SAL_TESTE
                )

            for matricula, codigo in (
                ("1", "AAA111"),
                ("2", "AAA111"),
                ("3", "BBB222"),
                ("4", "CCC333"),
                ("5", "CCC333"),
            ):
                self.repo.inserir_vinculo(matricula, codigo)

            # A quinta é gravada ANTES da terça, intencionalmente.
            # A F2 deve apresentar os horários em ordem semanal, não por ID.
            self.h_bia_quinta = self.repo.inserir_atendimento(
                "1", "AAA111",
                AtendimentoPresencial(
                    "quinta", "14:00", "16:00", "Predio X", "10",
                    registrado_em=DATA,
                ),
            )
            self.h_bia_terca = self.repo.inserir_atendimento(
                "1", "AAA111",
                AtendimentoOnline(
                    "terça", "09:00", "10:00", "Meet",
                    "https://meet.exemplo/bia", registrado_em=DATA,
                ),
            )
            self.h_davi = self.repo.inserir_atendimento(
                "2", "AAA111",
                AtendimentoPresencial(
                    "segunda", "08:00", "10:00", "Predio Y", "20",
                    registrado_em=DATA,
                ),
            )
            self.h_fabio = self.repo.inserir_atendimento(
                "4", "CCC333",
                AtendimentoPresencial(
                    "sexta", "10:00", "11:00", "Predio Z", "30",
                    registrado_em=DATA,
                ),
            )

    @staticmethod
    def _ids(atendimentos):
        """Compara IDs, não identidades Python: o SQLite recria os objetos."""
        return tuple(a.id for a in atendimentos)

    @staticmethod
    def _resumo_resultado(resultado):
        """Compara conteúdo, pois os objetos Monitor são reconstruídos pelo banco."""
        return (
            (resultado.disciplina.codigo, resultado.disciplina.nome),
            resultado.situacao,
            resultado.modalidade,
            resultado.dia,
            tuple(
                (
                    item.monitor.matricula,
                    item.monitor.nome,
                    item.monitor.email,
                    tuple(
                        (a.id, a.dia, a.inicio, a.fim,
                         a.modalidade(), a.local(), a.registrado_em)
                        for a in item.atendimentos
                    ),
                )
                for item in resultado.itens
            ),
        )

    def _foto(self):
        """Fotografia do estado completo do SQLite para detectar escritas indevidas."""
        consultas = (
            "SELECT matricula, nome, email, papel, senha_hash, senha_sal "
            "FROM usuarios ORDER BY matricula",
            "SELECT codigo, nome FROM disciplinas ORDER BY codigo",
            "SELECT matricula, codigo FROM vinculos ORDER BY matricula, codigo",
            "SELECT id, matricula, codigo, dia, inicio, fim, modalidade, "
            "predio, sala, plataforma, link, registrado_em "
            "FROM atendimentos ORDER BY id",
        )
        return tuple(
            tuple(tuple(linha) for linha in self.conexao.execute(sql))
            for sql in consultas
        )

    def _assert_nao_alterou(self, antes):
        self.assertEqual(antes, self._foto())

    def test_f2_01_sem_filtro_lista_monitores_e_horarios_ordenados(self):
        antes = self._foto()
        r = self.cadastro.consultar_monitorias("AAA111")
        self.assertEqual(r.disciplina.codigo, "AAA111")
        self.assertEqual(r.situacao, SituacaoConsulta.COM_HORARIOS)
        self.assertIsNone(r.modalidade)
        self.assertEqual([i.monitor.nome for i in r.itens], ["Bia Teste", "Davi Teste"])
        self.assertEqual(
            self._ids(r.itens[0].atendimentos),
            (self.h_bia_terca.id, self.h_bia_quinta.id),
        )
        self.assertEqual(self._ids(r.itens[1].atendimentos), (self.h_davi.id,))
        self._assert_nao_alterou(antes)

    def test_f2_02_filtro_online_mostra_so_horarios_online(self):
        r = self.cadastro.consultar_monitorias("AAA111", "online")
        self.assertEqual(r.situacao, SituacaoConsulta.COM_HORARIOS)
        self.assertEqual([i.monitor.nome for i in r.itens], ["Bia Teste"])
        self.assertEqual(self._ids(r.itens[0].atendimentos), (self.h_bia_terca.id,))

    def test_f2_03_filtro_por_dia_mostra_so_horarios_do_dia(self):
        antes = self._foto()
        r = self.cadastro.consultar_monitorias("AAA111", dia="terça")
        self.assertEqual(r.situacao, SituacaoConsulta.COM_HORARIOS)
        self.assertEqual(r.dia, "terça")
        self.assertEqual([i.monitor.nome for i in r.itens], ["Bia Teste"])
        self.assertEqual(self._ids(r.itens[0].atendimentos), (self.h_bia_terca.id,))
        self._assert_nao_alterou(antes)

    def test_f2_04_filtro_por_dia_sem_atendimento_nesse_dia(self):
        antes = self._foto()
        r = self.cadastro.consultar_monitorias("AAA111", dia="sexta")
        self.assertEqual(r.situacao, SituacaoConsulta.SEM_HORARIOS_NA_MODALIDADE)
        self.assertEqual(r.dia, "sexta")
        self.assertEqual(r.itens, ())
        self._assert_nao_alterou(antes)

    def test_f2_05_modalidade_e_dia_combinados(self):
        antes = self._foto()
        r = self.cadastro.consultar_monitorias("AAA111", "presencial", "quinta")
        self.assertEqual(r.situacao, SituacaoConsulta.COM_HORARIOS)
        self.assertEqual([i.monitor.nome for i in r.itens], ["Bia Teste"])
        self.assertEqual(self._ids(r.itens[0].atendimentos), (self.h_bia_quinta.id,))

        r = self.cadastro.consultar_monitorias("AAA111", "online", "quinta")
        self.assertEqual(r.situacao, SituacaoConsulta.SEM_HORARIOS_NA_MODALIDADE)
        self.assertEqual((r.modalidade, r.dia), ("online", "quinta"))
        self._assert_nao_alterou(antes)

    def test_f2_06_sem_filtro_monitor_sem_horario_tambem_aparece(self):
        antes = self._foto()
        r = self.cadastro.consultar_monitorias("CCC333")
        self.assertEqual(r.situacao, SituacaoConsulta.COM_HORARIOS)
        self.assertEqual([i.monitor.nome for i in r.itens], ["Fabio Teste", "Gabi Teste"])
        self.assertEqual(self._ids(r.itens[0].atendimentos), (self.h_fabio.id,))
        self.assertEqual(r.itens[1].atendimentos, ())
        self._assert_nao_alterou(antes)

    def test_f2_07_monitores_sem_nenhum_horario(self):
        antes = self._foto()
        r = self.cadastro.consultar_monitorias("BBB222")
        self.assertEqual(r.situacao, SituacaoConsulta.MONITOR_SEM_HORARIOS)
        self.assertEqual(len(r.itens), 1)
        self.assertEqual(r.itens[0].monitor.email, "eva.teste@ufmg.br")
        self.assertEqual(r.itens[0].atendimentos, ())
        self._assert_nao_alterou(antes)

    def test_f2_08_modalidade_sem_horarios(self):
        antes = self._foto()
        r = self.cadastro.consultar_monitorias("CCC333", "online")
        self.assertEqual(r.situacao, SituacaoConsulta.SEM_HORARIOS_NA_MODALIDADE)
        self.assertEqual(r.modalidade, "online")
        self.assertEqual(r.itens, ())
        self._assert_nao_alterou(antes)

    def test_f2_09_nenhuma_monitoria_cadastrada(self):
        antes = self._foto()
        r = self.cadastro.consultar_monitorias("DDD444")
        self.assertEqual(r.situacao, SituacaoConsulta.NENHUMA_MONITORIA_CADASTRADA)
        self.assertEqual(r.itens, ())
        self.assertEqual(r.disciplina.codigo, "DDD444")
        self._assert_nao_alterou(antes)

    def test_f2_10_codigo_fora_do_catalogo_e_rejeitado_sem_alterar_nada(self):
        antes = self._foto()
        with self.assertRaises(DisciplinaForaDoEscopo):
            self.cadastro.consultar_monitorias("DCC999")
        self._assert_nao_alterou(antes)

    def test_f2_11_codigo_mal_formatado_e_rejeitado_sem_alterar_nada(self):
        antes = self._foto()
        for ruim in ("", "AA111", "AAAA111", "AAA11", "123ABC", "AAA 111"):
            with self.subTest(codigo=ruim):
                with self.assertRaises(DadosInvalidos):
                    self.cadastro.consultar_monitorias(ruim)
        self._assert_nao_alterou(antes)

    def test_f2_12_modalidade_desconhecida_e_rejeitada_sem_alterar_nada(self):
        antes = self._foto()
        with self.assertRaises(DadosInvalidos):
            self.cadastro.consultar_monitorias("AAA111", "hibrida")
        self._assert_nao_alterou(antes)

    def test_f2_13_dia_invalido_e_rejeitado_sem_alterar_nada(self):
        antes = self._foto()
        for ruim in ("domingo", "xyz", "13"):
            with self.subTest(dia=ruim):
                with self.assertRaises(DadosInvalidos):
                    self.cadastro.consultar_monitorias("AAA111", dia=ruim)
        self._assert_nao_alterou(antes)

    def test_f2_14_formato_e_checado_antes_do_catalogo(self):
        with self.assertRaises(DadosInvalidos):
            self.cadastro.consultar_monitorias("DCC999", "hibrida")
        with self.assertRaises(DadosInvalidos):
            self.cadastro.consultar_monitorias("DCC999", dia="domingo")

    def test_f2_15_consultar_varias_vezes_nao_muda_dados(self):
        antes = self._foto()
        for codigo in ("AAA111", "BBB222", "CCC333", "DDD444"):
            for modalidade in (None, "online", "presencial"):
                for dia in (None, "terça", "sexta"):
                    self.cadastro.consultar_monitorias(codigo, modalidade, dia)
        self._assert_nao_alterou(antes)

    def test_local_e_modalidade_vem_de_cada_subclasse(self):
        r = self.cadastro.consultar_monitorias("AAA111")
        terca, quinta = r.itens[0].atendimentos
        self.assertEqual(terca.modalidade(), "online")
        self.assertEqual(terca.local(), "Meet: https://meet.exemplo/bia")
        self.assertEqual(quinta.modalidade(), "presencial")
        self.assertEqual(quinta.local(), "Predio X, sala 10")

    def test_com_filtro_monitor_sem_horario_na_modalidade_nao_aparece(self):
        r = self.cadastro.consultar_monitorias("CCC333", "presencial")
        self.assertEqual([i.monitor.nome for i in r.itens], ["Fabio Teste"])

    def test_filtro_presencial_mostra_so_horarios_presenciais(self):
        r = self.cadastro.consultar_monitorias("AAA111", "presencial")
        self.assertEqual(r.situacao, SituacaoConsulta.COM_HORARIOS)
        self.assertEqual(self._ids(r.itens[0].atendimentos), (self.h_bia_quinta.id,))
        self.assertEqual(self._ids(r.itens[1].atendimentos), (self.h_davi.id,))

    def test_modalidade_vazia_ou_none_equivale_a_todas(self):
        sem_filtro = self._resumo_resultado(self.cadastro.consultar_monitorias("AAA111"))
        for vazio in ("", "  ", None):
            with self.subTest(modalidade=vazio):
                atual = self._resumo_resultado(
                    self.cadastro.consultar_monitorias("AAA111", vazio)
                )
                self.assertEqual(atual, sem_filtro)

    def test_modalidade_aceita_maiusculas_e_espacos(self):
        r = self.cadastro.consultar_monitorias("AAA111", "  ONLINE ")
        self.assertEqual(r.modalidade, "online")
        self.assertEqual(self._ids(r.itens[0].atendimentos), (self.h_bia_terca.id,))

    def test_dia_aceita_maiusculas_espacos_e_vazio(self):
        r = self.cadastro.consultar_monitorias("AAA111", dia="  TERÇA ")
        self.assertEqual(r.dia, "terça")
        self.assertEqual(self._ids(r.itens[0].atendimentos), (self.h_bia_terca.id,))

        sem_filtro = self._resumo_resultado(self.cadastro.consultar_monitorias("AAA111"))
        for vazio in ("", "  ", None):
            with self.subTest(dia=vazio):
                atual = self._resumo_resultado(
                    self.cadastro.consultar_monitorias("AAA111", dia=vazio)
                )
                self.assertEqual(atual, sem_filtro)

    def test_codigo_em_minusculas_e_com_espacos_e_aceito(self):
        r = self.cadastro.consultar_monitorias("  aaa111 ")
        self.assertEqual(r.disciplina.codigo, "AAA111")
        self.assertEqual(r.situacao, SituacaoConsulta.COM_HORARIOS)

    def test_resultado_e_imutavel(self):
        r = self.cadastro.consultar_monitorias("AAA111")
        with self.assertRaises(dataclasses.FrozenInstanceError):
            r.situacao = SituacaoConsulta.MONITOR_SEM_HORARIOS
        self.assertIsInstance(r.itens, tuple)
        self.assertIsInstance(r.itens[0].atendimentos, tuple)

    def test_listar_disciplinas_ordenado_por_codigo(self):
        codigos = [d.codigo for d in self.cadastro.listar_disciplinas()]
        self.assertEqual(codigos, ["AAA111", "BBB222", "CCC333", "DDD444"])
        self.assertIsInstance(self.cadastro.listar_disciplinas(), tuple)


if __name__ == "__main__":
    unittest.main()
