"""Terminal do protótipo: único módulo com print e input.

Lê e converte o que o usuário digita, chama o domínio pelo CadastroMonitorias
e formata a resposta. Não decide regra nenhuma (conflito, escopo, situação da
consulta): isso é do domínio, que devolve objetos ou lança ErroMonitorias.
"""

from __future__ import annotations

import sys

from .dados_demo import criar_cadastro_demo
from .dominio.atendimento import Atendimento, AtendimentoOnline, AtendimentoPresencial
from .dominio.cadastro import CadastroMonitorias
from .dominio.consulta import ResultadoConsulta, SituacaoConsulta
from .dominio.disciplina import Disciplina
from .dominio.excecoes import ConflitoDeHorario, ErroMonitorias
from .dominio.horario import DIAS_VALIDOS

AVISO_INICIAL = (
    "=== Consulta centralizada de monitorias — Eng. de Sistemas UFMG (2026/2) ===\n"
    "Protótipo com dados FICTÍCIOS (nomes, matrículas, e-mails e links).\n"
    "Os dados ficam só em memória: o que for cadastrado se perde ao sair."
)

AVISO_SAIDA = "Encerrando. Os dados cadastrados nesta execução foram descartados."

MENU_PRINCIPAL = (
    "\n--- Menu principal ---\n"
    "1 - Consultar monitorias de uma disciplina (aluno)\n"
    "2 - Cadastrar horário de atendimento (monitor)\n"
    "3 - Listar disciplinas do sistema\n"
    "0 - Sair"
)


# ------------------------------------------------------------------ leitura

def ler_texto(rotulo: str) -> str:
    """Lê uma linha do usuário, sem espaços nas pontas.

    Se a entrada vier redirecionada de arquivo (stdin não é terminal), ecoa o
    valor lido, para a transcrição mostrar o que foi "digitado".

    Recebe:
        rotulo: pergunta exibida antes da leitura.
    Devolve:
        o texto lido (pode ser vazio).
    Lança:
        EOFError se a entrada acabar (tratado em executar()).
    """
    valor = input(rotulo).strip()
    if not sys.stdin.isatty():
        print(valor)
    return valor


def ler_opcao(rotulo: str, minimo: int, maximo: int,
              permitir_vazio: bool = False) -> int | None:
    """Lê um número inteiro entre minimo e maximo, repetindo só esta pergunta.

    Recebe:
        rotulo: pergunta exibida.
        minimo, maximo: faixa aceita (inclusive).
        permitir_vazio: se True, Enter sem nada devolve None.
    Devolve:
        o número escolhido, ou None (vazio permitido).
    """
    while True:
        texto = ler_texto(rotulo)
        if texto == "" and permitir_vazio:
            return None
        try:
            numero = int(texto)
        except ValueError:
            print(f"'{texto}' não é um número válido. "
                  f"Digite um número de {minimo} a {maximo}.")
            continue
        if not minimo <= numero <= maximo:
            print(f"Opção {numero} não existe. Digite um número de {minimo} a {maximo}.")
            continue
        return numero


def ler_dia() -> str:
    """Lê o dia da semana por número (1 = segunda ... 6 = sábado).

    Usar número evita erro de digitação de acento ("terça", "sábado").

    Devolve:
        o nome do dia, como em DIAS_VALIDOS.
    """
    opcoes = ", ".join(f"{n} = {dia}" for n, dia in enumerate(DIAS_VALIDOS, start=1))
    print(f"Dia da semana: {opcoes}")
    numero = ler_opcao(f"Dia (1 a {len(DIAS_VALIDOS)}): ", 1, len(DIAS_VALIDOS))
    return DIAS_VALIDOS[numero - 1]


# ------------------------------------------------------------- formatação
# As funções formatar_* só montam texto a partir de dados: não leem nem
# imprimem, para poderem ser conferidas isoladamente.

def formatar_atendimento(atendimento: Atendimento) -> str:
    """Uma linha com dia, horário, modalidade, local e data de registro.

    Usa modalidade() e local() sem saber a subclasse (polimorfismo).
    """
    return (f"{atendimento.dia} {atendimento.inicio}–{atendimento.fim} | "
            f"{atendimento.modalidade()} | {atendimento.local()} | "
            f"registrado em {atendimento.registrado_em:%d/%m/%Y}")


def formatar_resultado(resultado: ResultadoConsulta,
                       contatos: tuple[str, ...] = ()) -> str:
    """Monta o texto de uma consulta (F2) conforme a situação devolvida.

    Recebe:
        resultado: o ResultadoConsulta do domínio.
        contatos: e-mails a mostrar quando não há horário na modalidade
            pedida (o domínio não os inclui nessa situação).
    Devolve:
        o texto pronto para exibir.
    """
    disciplina = resultado.disciplina
    filtro = resultado.modalidade or "todas"
    linhas = [f"\n{disciplina.codigo} — {disciplina.nome} (modalidade: {filtro})"]
    situacao = resultado.situacao

    if situacao is SituacaoConsulta.COM_HORARIOS:
        for item in resultado.itens:
            linhas.append(f"  Monitor(a): {item.monitor.nome} <{item.monitor.email}>")
            for atendimento in item.atendimentos:
                linhas.append(f"    - {formatar_atendimento(atendimento)}")
            if not item.atendimentos:
                linhas.append("    (sem horários cadastrados nesta disciplina)")
    elif situacao is SituacaoConsulta.MONITOR_SEM_HORARIOS:
        linhas.append("  Há monitor cadastrado, mas os horários ainda não foram informados.")
        for item in resultado.itens:
            linhas.append(f"  Contato: {item.monitor.nome} <{item.monitor.email}>")
    elif situacao is SituacaoConsulta.SEM_HORARIOS_NA_MODALIDADE:
        linhas.append("  Não há horário cadastrado nessa modalidade.")
        for contato in contatos:
            linhas.append(f"  Contato: {contato}")
    elif situacao is SituacaoConsulta.NENHUMA_MONITORIA_CADASTRADA:
        linhas.append("  Nenhuma monitoria cadastrada no sistema para esta disciplina.")
        linhas.append("  Atenção: a ausência no sistema não garante que não exista "
                      "monitoria; confirme com o departamento que oferta a disciplina.")
    return "\n".join(linhas)


def formatar_disciplinas(disciplinas: tuple[Disciplina, ...]) -> str:
    """Lista de disciplinas do catálogo, uma por linha."""
    linhas = ["\nDisciplinas no sistema (2026/2):"]
    linhas += [f"  {d.codigo} — {d.nome}" for d in disciplinas]
    return "\n".join(linhas)


def formatar_conflito(erro: ConflitoDeHorario) -> str:
    """Frase do conflito de horário, montada com os dados da exceção."""
    existente = erro.atendimento
    return (f"Conflito de horário: você já atende {existente.dia} "
            f"{existente.inicio}–{existente.fim} em {erro.vinculo.disciplina.codigo}.")


# ------------------------------------------------------- funcionalidades

def consultar(cadastro: CadastroMonitorias) -> None:
    """F2: lê código e modalidade, consulta e mostra o resultado.

    Lança:
        ErroMonitorias vindo do domínio (tratado em executar()).
    """
    codigo = ler_texto("Código da disciplina (ex.: DCC203): ")
    print("Modalidade: Enter = todas, 1 = presencial, 2 = online")
    opcao = ler_opcao("Modalidade: ", 1, 2, permitir_vazio=True)
    modalidade = {None: None, 1: "presencial", 2: "online"}[opcao]

    resultado = cadastro.consultar_monitorias(codigo, modalidade)
    contatos: tuple[str, ...] = ()
    if resultado.situacao is SituacaoConsulta.SEM_HORARIOS_NA_MODALIDADE:
        # Consulta só de leitura, sem filtro, para mostrar a quem perguntar.
        todos = cadastro.consultar_monitorias(codigo)
        contatos = tuple(f"{i.monitor.nome} <{i.monitor.email}>" for i in todos.itens)
    print(formatar_resultado(resultado, contatos))


def cadastrar(cadastro: CadastroMonitorias) -> None:
    """F1: lê os dados do horário, cria o atendimento e pede o cadastro.

    O local é perguntado antes do dia e do horário, para um erro de horário
    aparecer logo depois do último dado digitado.

    Lança:
        ErroMonitorias vindo do domínio (tratado em executar()).
    """
    matricula = ler_texto("Matrícula do monitor: ")
    codigo = ler_texto("Código da disciplina (ex.: DCC203): ")
    print("Modalidade: 1 = presencial, 2 = online")
    opcao = ler_opcao("Modalidade: ", 1, 2)

    if opcao == 1:
        predio = ler_texto("Prédio (ex.: CAD 3): ")
        sala = ler_texto("Sala (ex.: 204): ")
    else:
        plataforma = ler_texto("Plataforma (ex.: Google Meet): ")
        link = ler_texto("Link (começando com https://): ")

    dia = ler_dia()
    inicio = ler_texto("Início (hh:mm): ")
    fim = ler_texto("Fim (hh:mm): ")

    if opcao == 1:
        atendimento = AtendimentoPresencial(dia, inicio, fim, predio, sala)
    else:
        atendimento = AtendimentoOnline(dia, inicio, fim, plataforma, link)

    cadastro.cadastrar_atendimento(matricula, codigo, atendimento)
    print(f"\nHorário cadastrado: {formatar_atendimento(atendimento)}")


def listar(cadastro: CadastroMonitorias) -> None:
    """Mostra as disciplinas do catálogo (apoio às duas funcionalidades)."""
    print(formatar_disciplinas(cadastro.listar_disciplinas()))


# ------------------------------------------------------------ laço principal

def executar(cadastro: CadastroMonitorias | None = None) -> None:
    """Laço principal do terminal.

    Recebe:
        cadastro: um cadastro pronto (útil para testes); se None, usa os
            dados fictícios de criar_cadastro_demo().

    Qualquer ErroMonitorias é tratado aqui, num único ponto: mostra a
    mensagem, avisa que nada foi alterado e volta ao menu. Fim da entrada
    (Ctrl+D / Ctrl+Z) e Ctrl+C encerram sem traceback.
    """
    if cadastro is None:
        cadastro = criar_cadastro_demo()
    acoes = {1: consultar, 2: cadastrar, 3: listar}

    print(AVISO_INICIAL)
    try:
        while True:
            print(MENU_PRINCIPAL)
            opcao = ler_opcao("Escolha uma opção: ", 0, 3)
            if opcao == 0:
                break
            try:
                acoes[opcao](cadastro)
            except ConflitoDeHorario as erro:
                print(f"\nNão foi possível concluir: {formatar_conflito(erro)}")
                print("Nenhum dado foi alterado.")
            except ErroMonitorias as erro:
                print(f"\nNão foi possível concluir: {erro}")
                print("Nenhum dado foi alterado.")
    except (EOFError, KeyboardInterrupt):
        print()
    print(AVISO_SAIDA)
