"""Carga de dados fictícios na base de demonstração.

Uso, de dentro de prototipo_monitoria/:

    python -m monitorias.persistencia.seed_demo            # prepara a base, se estiver vazia
    python -m monitorias.persistencia.seed_demo --recriar  # apaga a base e prepara de novo

TODOS os dados são fictícios: nomes, matrículas, e-mails, links e senhas.
As senhas abaixo existem só para a demonstração e estão listadas no README.

Pode ser executado quantas vezes quiser sem duplicar nada: se a base já tem
dados, a carga não faz nada. Ela também roda numa única transação, então ou
entra tudo, ou nada. Por isso "a base tem algum usuário" equivale a "a carga
já foi feita".

A carga passa pelas operações do CadastroMonitorias (A1, A2, A3 e F1a), com as
mesmas validações e checagens de conflito do uso normal. A única gravação feita
direto pelo repositório é a do primeiro administrador: nenhuma operação do
sistema cadastra administradores, e sem um deles não há quem execute A1–A3.
"""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from monitorias.dominio.cadastro import CadastroMonitorias
from monitorias.dominio.senha import gerar_hash_senha
from monitorias.dominio.usuario import Administrador
from monitorias.persistencia.conexao import CAMINHO_PADRAO, abrir_base
from monitorias.persistencia.repositorio import RepositorioMonitorias

#: Data de registro fixa dos horários iniciais, para a saída ser reproduzível.
DATA_DEMO = date(2026, 10, 20)

#: (matrícula, nome, e-mail, senha) — fictícios.
ADMINISTRADORES = (
    ("2026900001", "Admin Fictício", "admin.ficticio@ufmg.br", "admin123"),
)
MONITORES = (
    ("2026000001", "Ana Fictícia", "ana.ficticia@ufmg.br", "ana123"),
    ("2026000002", "Caio Exemplo", "caio.exemplo@ufmg.br", "caio123"),
    ("2026000003", "Duda Teste", "duda.teste@ufmg.br", "duda123"),
)

#: DCC999 fica de fora de propósito (rejeição "fora do escopo" da F2).
DISCIPLINAS = (
    ("DCC203", "Programação e Desenvolvimento de Software I"),
    ("MAT001", "Cálculo Diferencial e Integral I"),
    ("MAT002", "Geometria Analítica e Álgebra Linear"),
    ("FIS069", "Física III"),
    ("ELT001", "Circuitos Elétricos I"),
)

#: Simulam a lista de vínculos que o departamento enviaria. ELT001 fica sem
#: vínculo (situação "nenhuma monitoria cadastrada") e Duda fica sem horários
#: (situação "monitor sem horários"). Ana atende em duas disciplinas (DCC203 e
#: MAT002), para os cenários de conflito entre disciplinas (F1C-03) e de
#: desvincular quem atende em duas disciplinas (A4-01).
VINCULOS = (
    ("2026000001", "DCC203"),
    ("2026000001", "MAT002"),
    ("2026000002", "DCC203"),  # Caio, sem horário em DCC203
    ("2026000002", "MAT001"),
    ("2026000003", "FIS069"),
)


#: Horários iniciais: (matrícula, código, modalidade, dia, início, fim, local 1, local 2).
#: Local 1 e 2 são prédio e sala (presencial) ou plataforma e link (online).
#: Os mesmos valores do protótipo, para os cenários continuarem válidos, mais
#: o horário da Ana em MAT002.
HORARIOS = (
    ("2026000001", "DCC203", "presencial", "terça", "10:00", "12:00", "CAD 3", "204"),
    ("2026000001", "MAT002", "presencial", "quarta", "10:00", "12:00", "ICEx", "2033"),
    ("2026000002", "MAT001", "presencial", "terça", "14:00", "16:00", "ICEx", "1010"),
    ("2026000002", "MAT001", "online", "quinta", "19:00", "20:00", "Google Meet",
     "https://meet.exemplo/mat001"),
)


def carregar_demo(repositorio: RepositorioMonitorias) -> bool:
    """Preenche a base com os dados fictícios, se ela estiver vazia.

    Grava o primeiro administrador pelo repositório e todo o resto pelas
    operações do cadastro (A2, A1, A3 e F1a), numa única transação. Os horários
    recebem a data fixa DATA_DEMO.

    Devolve:
        True se carregou; False se a base já tinha dados (nada foi alterado).
    Lança:
        ErroMonitorias, se algum dado fictício violar uma regra; nesse caso a
        transação é desfeita e a base continua vazia.
    """
    if not repositorio.esta_vazia():
        return False
    cadastro = CadastroMonitorias(repositorio, hoje=lambda: DATA_DEMO)
    with repositorio.transacao():
        for matricula, nome, email, senha in ADMINISTRADORES:
            repositorio.inserir_administrador(
                Administrador(matricula, nome, email), *gerar_hash_senha(senha))
        administrador = repositorio.buscar_usuario(ADMINISTRADORES[0][0])
        for matricula, nome, email, senha in MONITORES:
            cadastro.cadastrar_monitor(administrador, matricula, nome, email, senha)
        for codigo, nome in DISCIPLINAS:
            cadastro.cadastrar_disciplina(administrador, codigo, nome)
        for matricula, codigo in VINCULOS:
            cadastro.vincular(administrador, matricula, codigo)
        for matricula, codigo, modalidade, dia, inicio, fim, local1, local2 in HORARIOS:
            monitor = repositorio.buscar_usuario(matricula)
            if modalidade == "presencial":
                cadastro.cadastrar_presencial(monitor, codigo, dia, inicio, fim, local1, local2)
            else:
                cadastro.cadastrar_online(monitor, codigo, dia, inicio, fim, local1, local2)
    return True


def main(argumentos: list[str] | None = None) -> None:
    """Ponto de entrada do comando python -m monitorias.persistencia.seed_demo."""
    leitor = argparse.ArgumentParser(description="Prepara a base de demonstração.")
    leitor.add_argument("--caminho", type=Path, default=CAMINHO_PADRAO,
                        help="arquivo da base (padrão: dados/monitorias.db)")
    leitor.add_argument("--recriar", action="store_true",
                        help="apaga a base existente antes de carregar")
    opcoes = leitor.parse_args(argumentos)

    if opcoes.recriar and opcoes.caminho.exists():
        opcoes.caminho.unlink()
    conexao = abrir_base(opcoes.caminho)
    try:
        if carregar_demo(RepositorioMonitorias(conexao)):
            print(f"Base de demonstração criada em {opcoes.caminho}.")
        else:
            print(f"A base {opcoes.caminho} já tem dados; nada foi alterado.")
    finally:
        conexao.close()


if __name__ == "__main__":
    main()
