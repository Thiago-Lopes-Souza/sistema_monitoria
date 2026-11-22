"""Terminal do sistema: único módulo com print e input.

Lê e converte o que o usuário digita, chama o CadastroMonitorias e formata a
resposta. Não decide regra nenhuma (conflito, permissão, escopo, situação da
consulta), não fala com o repositório e não cria objetos do domínio: só repassa
os textos lidos ao cadastro.
"""

from __future__ import annotations

import getpass
import sys
from collections.abc import Callable

from .dominio.atendimento import Atendimento
from .dominio.cadastro import CadastroMonitorias
from .dominio.consulta import ResultadoConsulta, SituacaoConsulta
from .dominio.disciplina import Disciplina
from .dominio.excecoes import ConflitoDeHorario, ErroMonitorias
from .dominio.horario import DIAS_VALIDOS
from .dominio.usuario import Operacao, Usuario

AVISO_INICIAL = (
    "=== Consulta centralizada de monitorias — Eng. de Sistemas UFMG (2026/2) ===\n"
    "Dados de demonstração FICTÍCIOS (nomes, matrículas, e-mails, links e senhas).\n"
    "As alterações ficam salvas na base de dados e continuam lá na próxima execução."
)

AVISO_SAIDA = "Encerrando. As alterações feitas nesta execução ficaram salvas na base de dados."

MENU_INICIAL = (
    "\n--- Menu inicial ---\n"
    "1 - Consultar monitorias de uma disciplina (sem login)\n"
    "2 - Entrar como monitor ou administrador\n"
    "3 - Listar disciplinas do sistema\n"
    "0 - Sair"
)

MODALIDADES = {None: None, 1: "presencial", 2: "online"}


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


def ler_senha(rotulo: str = "Senha: ") -> str:
    """Lê uma senha sem mostrá-la.

    No terminal usa getpass (nada aparece na tela). Com a entrada redirecionada
    (cenários e testes), getpass travaria esperando o teclado; nesse caso lê com
    input() e ecoa "********", nunca a senha.

    Devolve:
        a senha digitada, sem alteração (espaços contam).
    """
    if sys.stdin.isatty():
        return getpass.getpass(rotulo)
    senha = input(rotulo)
    print("********")
    return senha


def ler_opcao(rotulo: str, minimo: int, maximo: int | None,
              permitir_vazio: bool = False) -> int | None:
    """Lê um número inteiro, repetindo só esta pergunta até ser válido.

    Recebe:
        rotulo: pergunta exibida.
        minimo, maximo: faixa aceita (inclusive); maximo None = sem limite.
        permitir_vazio: se True, Enter sem nada devolve None.
    Devolve:
        o número digitado, ou None (vazio permitido).
    """
    faixa = (f"um número de {minimo} a {maximo}" if maximo is not None
             else f"um número inteiro a partir de {minimo}")
    while True:
        texto = ler_texto(rotulo)
        if texto == "" and permitir_vazio:
            return None
        try:
            numero = int(texto)
        except ValueError:
            print(f"'{texto}' não é um número válido. Digite {faixa}.")
            continue
        if numero < minimo or (maximo is not None and numero > maximo):
            print(f"Opção {numero} não existe. Digite {faixa}.")
            continue
        return numero


def ler_dia(permitir_vazio: bool = False) -> str | None:
    """Lê o dia da semana por número (1 = segunda ... 6 = sábado).

    Usar número evita erro de digitação de acento ("terça", "sábado").

    Recebe:
        permitir_vazio: se True, Enter devolve None (todos os dias).
    Devolve:
        o nome do dia, como em DIAS_VALIDOS, ou None.
    """
    opcoes = ", ".join(f"{n} = {dia}" for n, dia in enumerate(DIAS_VALIDOS, start=1))
    prefixo = "Enter = todos, " if permitir_vazio else ""
    print(f"Dia da semana: {prefixo}{opcoes}")
    numero = ler_opcao("Dia: ", 1, len(DIAS_VALIDOS), permitir_vazio)
    return None if numero is None else DIAS_VALIDOS[numero - 1]


# ------------------------------------------------------------- formatação
# As funções formatar_* só montam texto a partir de dados: não leem, não
# imprimem e não chamam o cadastro, para poderem ser conferidas isoladamente.

def formatar_atendimento(atendimento: Atendimento) -> str:
    """Uma linha com dia, horário, modalidade, local e data do último cadastro ou alteração.

    Usa modalidade() e local() sem saber a subclasse (polimorfismo).
    """
    return (f"{atendimento.dia} {atendimento.inicio}–{atendimento.fim} | "
            f"{atendimento.modalidade()} | {atendimento.local()} | "
            f"atualizado em {atendimento.registrado_em:%d/%m/%Y}")


def formatar_resultado(resultado: ResultadoConsulta,
                       contatos: tuple[str, ...] = ()) -> str:
    """Monta o texto de uma consulta (F2) conforme a situação devolvida.

    Recebe:
        resultado: o ResultadoConsulta do domínio.
        contatos: monitores a mostrar quando nenhum horário combina com o
            filtro (o domínio não os inclui nessa situação).
    Devolve:
        o texto pronto para exibir.
    """
    disciplina = resultado.disciplina
    filtros = (f"modalidade: {resultado.modalidade or 'todas'} | "
               f"dia: {resultado.dia or 'todos'}")
    linhas = [f"\n{disciplina.codigo} — {disciplina.nome} ({filtros})"]
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
        linhas.append("  Não há horário cadastrado com esse filtro (modalidade e/ou dia).")
        for contato in contatos:
            linhas.append(f"  Contato: {contato}")
    elif situacao is SituacaoConsulta.NENHUMA_MONITORIA_CADASTRADA:
        linhas.append("  Nenhuma monitoria cadastrada no sistema para esta disciplina.")
        linhas.append("  Atenção: a ausência no sistema não garante que não exista "
                      "monitoria; confirme com o departamento que oferta a disciplina.")
    return "\n".join(linhas)


def formatar_meus_horarios(pares: tuple[tuple[Disciplina, Atendimento], ...]) -> str:
    """Lista da F1b: ID, disciplina e dados de cada horário do monitor."""
    if not pares:
        return "\nVocê ainda não tem horários cadastrados."
    linhas = ["\nSeus horários:"]
    for disciplina, atendimento in pares:
        linhas.append(f"  ID {atendimento.id} | {disciplina.codigo} — {disciplina.nome} | "
                      f"{formatar_atendimento(atendimento)}")
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
# Todas recebem (cadastro, usuario); as que não dependem de sessão ignoram o
# usuário. Erros do domínio sobem para _executar_acao().

def consultar(cadastro: CadastroMonitorias, usuario: Usuario | None = None) -> None:
    """F2: lê código, modalidade e dia; chama consultar_monitorias e mostra o resultado."""
    codigo = ler_texto("Código da disciplina (ex.: DCC203): ")
    print("Modalidade: Enter = todas, 1 = presencial, 2 = online")
    modalidade = MODALIDADES[ler_opcao("Modalidade: ", 1, 2, permitir_vazio=True)]
    dia = ler_dia(permitir_vazio=True)

    resultado = cadastro.consultar_monitorias(codigo, modalidade, dia)
    contatos: tuple[str, ...] = ()
    if resultado.situacao is SituacaoConsulta.SEM_HORARIOS_NA_MODALIDADE:
        # Consulta só de leitura, sem filtro, para mostrar a quem perguntar.
        todos = cadastro.consultar_monitorias(codigo)
        contatos = tuple(f"{i.monitor.nome} <{i.monitor.email}>" for i in todos.itens)
    print(formatar_resultado(resultado, contatos))


def listar(cadastro: CadastroMonitorias, usuario: Usuario | None = None) -> None:
    """Chama listar_disciplinas e mostra o catálogo (apoio à F2 e à F1a)."""
    print(formatar_disciplinas(cadastro.listar_disciplinas()))


def cadastrar_horario(cadastro: CadastroMonitorias, usuario: Usuario) -> None:
    """F1a: lê código, modalidade, local, dia, início e fim; chama cadastrar_presencial
    ou cadastrar_online e mostra o horário gravado.

    O local é perguntado antes do dia e do horário, para um erro de horário
    aparecer logo depois do último dado digitado.
    """
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
        atendimento = cadastro.cadastrar_presencial(usuario, codigo, dia, inicio, fim, predio, sala)
    else:
        atendimento = cadastro.cadastrar_online(usuario, codigo, dia, inicio, fim, plataforma, link)
    print(f"\nHorário cadastrado (ID {atendimento.id}): {formatar_atendimento(atendimento)}")


def ver_meus_horarios(cadastro: CadastroMonitorias, usuario: Usuario) -> bool:
    """F1b: chama listar_meus_atendimentos e mostra os horários do monitor.

    Devolve:
        True se o monitor tem algum horário (usado pela F1c e pela F1d).
    """
    pares = cadastro.listar_meus_atendimentos(usuario)
    print(formatar_meus_horarios(pares))
    return bool(pares)


def alterar_horario(cadastro: CadastroMonitorias, usuario: Usuario) -> None:
    """F1c: mostra a F1b, lê o ID e o novo dia, início e fim; chama alterar_horario."""
    if not ver_meus_horarios(cadastro, usuario):
        return
    id_atendimento = ler_opcao("ID do atendimento a alterar: ", 1, None)
    dia = ler_dia()
    inicio = ler_texto("Novo início (hh:mm): ")
    fim = ler_texto("Novo fim (hh:mm): ")
    alterado = cadastro.alterar_horario(usuario, id_atendimento, dia, inicio, fim)
    print(f"\nHorário alterado (ID {alterado.id}): {formatar_atendimento(alterado)}")


def remover_horario(cadastro: CadastroMonitorias, usuario: Usuario) -> None:
    """F1d: mostra a F1b, lê o ID e chama remover_atendimento."""
    if not ver_meus_horarios(cadastro, usuario):
        return
    id_atendimento = ler_opcao("ID do atendimento a remover: ", 1, None)
    cadastro.remover_atendimento(usuario, id_atendimento)
    print(f"\nAtendimento de ID {id_atendimento} removido.")


def cadastrar_disciplina(cadastro: CadastroMonitorias, usuario: Usuario) -> None:
    """A1: lê código e nome; chama cadastrar_disciplina e mostra a disciplina gravada."""
    codigo = ler_texto("Código da nova disciplina (ex.: DCC205): ")
    nome = ler_texto("Nome da disciplina: ")
    disciplina = cadastro.cadastrar_disciplina(usuario, codigo, nome)
    print(f"\nDisciplina cadastrada: {disciplina.codigo} — {disciplina.nome}")


def cadastrar_monitor(cadastro: CadastroMonitorias, usuario: Usuario) -> None:
    """A2: lê matrícula, nome, e-mail e senha inicial; chama cadastrar_monitor."""
    matricula = ler_texto("Matrícula do novo monitor: ")
    nome = ler_texto("Nome: ")
    email = ler_texto("E-mail institucional (@ufmg.br): ")
    senha = ler_senha("Senha inicial: ")
    monitor = cadastro.cadastrar_monitor(usuario, matricula, nome, email, senha)
    print(f"\nMonitor cadastrado: {monitor.nome} ({monitor.matricula}) <{monitor.email}>. "
          "Ainda sem vínculo com disciplinas.")


def vincular(cadastro: CadastroMonitorias, usuario: Usuario) -> None:
    """A3: lê matrícula e código; chama vincular e mostra o vínculo criado."""
    matricula = ler_texto("Matrícula do monitor: ")
    codigo = ler_texto("Código da disciplina: ")
    vinculo = cadastro.vincular(usuario, matricula, codigo)
    print(f"\nVínculo criado: {vinculo.monitor.nome} agora é monitor(a) de "
          f"{vinculo.disciplina.codigo} — {vinculo.disciplina.nome}.")


def desvincular(cadastro: CadastroMonitorias, usuario: Usuario) -> None:
    """A4: lê matrícula e código; chama desvincular e mostra quantos horários saíram."""
    matricula = ler_texto("Matrícula do monitor: ")
    codigo = ler_texto("Código da disciplina: ")
    removidos = cadastro.desvincular(usuario, matricula, codigo)
    print(f"\nVínculo removido. Horários apagados junto com ele: {removidos}.")


#: Operação do perfil -> (rótulo no menu, função). O submenu da sessão é
#: montado a partir de usuario.opcoes_menu(), na ordem que o perfil devolve.
ACOES_DA_SESSAO: dict[Operacao, tuple[str, Callable[[CadastroMonitorias, Usuario], object]]] = {
    Operacao.CONSULTAR_MONITORIAS: ("Consultar monitorias de uma disciplina", consultar),
    Operacao.CADASTRAR_HORARIO: ("Cadastrar horário de atendimento", cadastrar_horario),
    Operacao.VISUALIZAR_HORARIOS: ("Ver meus horários", ver_meus_horarios),
    Operacao.ALTERAR_HORARIO: ("Alterar dia e horário de um atendimento", alterar_horario),
    Operacao.REMOVER_ATENDIMENTO: ("Remover um atendimento", remover_horario),
    Operacao.CADASTRAR_DISCIPLINA: ("Cadastrar disciplina", cadastrar_disciplina),
    Operacao.CADASTRAR_MONITOR: ("Cadastrar monitor", cadastrar_monitor),
    Operacao.VINCULAR: ("Vincular monitor a disciplina", vincular),
    Operacao.DESVINCULAR: ("Desvincular monitor de disciplina", desvincular),
}


def opcoes_da_sessao(usuario: Usuario) -> list[tuple[str, Callable]]:
    """Monta as opções do submenu a partir de usuario.opcoes_menu().

    Não confere o tipo do usuário: cada perfil diz o que oferece
    (polimorfismo). Operações sem função no menu são ignoradas.
    """
    return [ACOES_DA_SESSAO[op] for op in usuario.opcoes_menu() if op in ACOES_DA_SESSAO]


def formatar_menu_da_sessao(usuario: Usuario, opcoes: list[tuple[str, Callable]]) -> str:
    """Texto do submenu: opções numeradas a partir de 1 e "0 - Sair da sessão"."""
    linhas = [f"\n--- Sessão de {usuario.nome} ---"]
    linhas += [f"{n} - {rotulo}" for n, (rotulo, _) in enumerate(opcoes, start=1)]
    linhas.append("0 - Sair da sessão")
    return "\n".join(linhas)


# ------------------------------------------------------------ laços

def _executar_acao(acao: Callable, cadastro: CadastroMonitorias, usuario: Usuario | None) -> None:
    """Ponto único de tratamento das rejeições do domínio.

    Qualquer ErroMonitorias mostra a mensagem, avisa que nada foi alterado e
    devolve o controle ao menu que chamou. O domínio garante que uma rejeição
    não deixa gravação parcial.
    """
    try:
        acao(cadastro, usuario)
    except ConflitoDeHorario as erro:
        print(f"\nNão foi possível concluir: {formatar_conflito(erro)}")
        print("Nenhum dado foi alterado.")
    except ErroMonitorias as erro:
        print(f"\nNão foi possível concluir: {erro}")
        print("Nenhum dado foi alterado.")


def entrar(cadastro: CadastroMonitorias, usuario: Usuario | None = None) -> None:
    """S1: lê matrícula e senha, chama cadastro.entrar e abre a sessão do usuário.

    A sessão dura até "Sair da sessão"; depois o usuário é descartado e o
    controle volta ao menu inicial.
    """
    matricula = ler_texto("Matrícula: ")
    senha = ler_senha()
    autenticado = cadastro.entrar(matricula, senha)
    print(f"\nSessão iniciada. Bem-vindo(a), {autenticado.nome}.")

    opcoes = opcoes_da_sessao(autenticado)
    while True:
        print(formatar_menu_da_sessao(autenticado, opcoes))
        escolha = ler_opcao("Escolha uma opção: ", 0, len(opcoes))
        if escolha == 0:
            print("Sessão encerrada.")
            return
        _executar_acao(opcoes[escolha - 1][1], cadastro, autenticado)


def executar(cadastro: CadastroMonitorias) -> None:
    """Laço do menu inicial.

    Recebe:
        cadastro: CadastroMonitorias já ligado ao repositório (montado no
            ponto de entrada, __main__.py, ou pelos testes).

    Fim da entrada (Ctrl+D / Ctrl+Z) e Ctrl+C encerram sem traceback.
    """
    acoes = {1: consultar, 2: entrar, 3: listar}
    print(AVISO_INICIAL)
    try:
        while True:
            print(MENU_INICIAL)
            opcao = ler_opcao("Escolha uma opção: ", 0, 3)
            if opcao == 0:
                break
            _executar_acao(acoes[opcao], cadastro, None)
    except (EOFError, KeyboardInterrupt):
        print()
    print(AVISO_SAIDA)
