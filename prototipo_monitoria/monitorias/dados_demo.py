"""Dados de demonstração do protótipo: TODOS FICTÍCIOS.

Nomes, matrículas, e-mails, links e até os códigos de disciplina são
ilustrativos. Simula a lista de vínculos que o departamento enviaria ao
sistema. Os testes não usam este módulo (cada teste monta os próprios dados).
"""

from __future__ import annotations

from datetime import date

from .dominio.atendimento import AtendimentoOnline, AtendimentoPresencial
from .dominio.cadastro import CadastroMonitorias
from .dominio.disciplina import Disciplina
from .dominio.monitor import Monitor

# Data fixa de registro dos horários demo, para a saída ser reproduzível.
DATA_DEMO = date(2026, 10, 20)


def criar_cadastro_demo() -> CadastroMonitorias:
    """Monta um CadastroMonitorias novo com dados fictícios.

    Cada chamada devolve um cadastro independente. Os dados ficam só em
    memória e se perdem ao encerrar o programa.
    """
    cadastro = CadastroMonitorias()

    # Catálogo. DCC999 fica de fora de propósito (cenário de rejeição da F2).
    cadastro.adicionar_disciplina(
        Disciplina("DCC203", "Programação e Desenvolvimento de Software I")
    )
    cadastro.adicionar_disciplina(
        Disciplina("MAT001", "Cálculo Diferencial e Integral I")
    )
    cadastro.adicionar_disciplina(Disciplina("FIS069", "Física III"))
    cadastro.adicionar_disciplina(Disciplina("ELT001", "Circuitos Elétricos I"))

    cadastro.adicionar_monitor(
        Monitor("2026000001", "Ana Fictícia", "ana.ficticia@ufmg.br")
    )
    cadastro.adicionar_monitor(
        Monitor("2026000002", "Caio Exemplo", "caio.exemplo@ufmg.br")
    )
    cadastro.adicionar_monitor(
        Monitor("2026000003", "Duda Teste", "duda.teste@ufmg.br")
    )

    # Vínculos (simulam a lista do departamento). ELT001 fica sem vínculo.
    vinculo_ana_dcc = cadastro.vincular("2026000001", "DCC203")
    cadastro.vincular("2026000002", "DCC203")  # Caio, sem horário em DCC203
    vinculo_caio_mat = cadastro.vincular("2026000002", "MAT001")
    cadastro.vincular("2026000003", "FIS069")  # Duda, sem horários

    # Horários iniciais de demonstração; novos horários usam a funcionalidade F1.
    vinculo_ana_dcc.adicionar_atendimento(
        AtendimentoPresencial(
            "terça", "10:00", "12:00", "CAD 3", "204",
            registrado_em=DATA_DEMO,
        )
    )
    vinculo_caio_mat.adicionar_atendimento(
        AtendimentoPresencial(
            "terça", "14:00", "16:00", "ICEx", "1010",
            registrado_em=DATA_DEMO,
        )
    )
    vinculo_caio_mat.adicionar_atendimento(
        AtendimentoOnline(
            "quinta",
            "19:00",
            "20:00",
            "Google Meet",
            "https://meet.exemplo/mat001",
            registrado_em=DATA_DEMO,
        )
    )

    return cadastro
