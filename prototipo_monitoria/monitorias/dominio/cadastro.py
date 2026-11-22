"""CadastroMonitorias: ponto único de entrada do domínio (F1, F2 e preparação dos dados)."""

from monitorias.dominio.disciplina import Disciplina
from monitorias.dominio.monitor import Monitor
from monitorias.dominio.vinculo import Vinculo
from monitorias.dominio.atendimento import Atendimento, AtendimentoOnline, AtendimentoPresencial
from monitorias.dominio.consulta import ItemConsulta, ResultadoConsulta, SituacaoConsulta
from monitorias.dominio.horario import validar_codigo, validar_dia, DIAS_VALIDOS
from monitorias.dominio.excecoes import (
    ConflitoDeHorario, DadosInvalidos, DisciplinaForaDoEscopo,
    MatriculaNaoCadastrada, VinculoInexistente, CredenciaisInvalidas,
    PermissaoNegada, AtendimentoInexistente, RegistroDuplicado)
from monitorias.persistencia.repositorio import RepositorioMonitorias
from monitorias.dominio.senha import gerar_hash_senha, conferir_senha
from monitorias.dominio.usuario import UsuarioCadastrado, Usuario, Operacao, Administrador


class CadastroMonitorias:
    """Ponto de entrada do domínio: coordena as funcionalidades sobre o repositório."""

    def __init__(self, repositorio: RepositorioMonitorias):
        """Recebe o repositório que persiste os dados."""
        self._repositorio = repositorio

    def cadastrar_disciplina(self,usuario: Usuario,codigo: str,nome: str) -> Disciplina:
        """A1: cadastra uma disciplina (só administrador)."""
        if (not isinstance(usuario, Administrador) or not usuario.pode(Operacao.CADASTRAR_DISCIPLINA)):
            raise PermissaoNegada("Usuário sem permissão para cadastrar disciplinas.")

        disciplina = Disciplina(codigo, nome)
        existente = self._repositorio.buscar_disciplina(disciplina.codigo)

        if existente is not None:
            raise RegistroDuplicado("disciplina", disciplina.codigo)

        with self._repositorio.transacao():
            self._repositorio.inserir_disciplina(disciplina)

        return disciplina

    def cadastrar_monitor(self, usuario: Usuario, matricula: str, nome: str, email: str, senha_inicial: str) -> Monitor:
        """A2: cadastra um monitor com senha inicial (só administrador)."""
        if (not isinstance(usuario, Administrador)or not usuario.pode(Operacao.CADASTRAR_MONITOR)):
            raise PermissaoNegada("Usuário sem permissão para cadastrar monitores.")

        monitor = Monitor(matricula, nome, email)
        existente = self._repositorio.buscar_usuario(monitor.matricula)

        if existente is not None:
            raise RegistroDuplicado("matrícula", monitor.matricula)

        senha_hash, senha_sal = gerar_hash_senha(senha_inicial)

        with self._repositorio.transacao():
            self._repositorio.inserir_monitor(monitor, senha_hash, senha_sal)

        return monitor

    def vincular(self, usuario: Usuario, matricula: str, codigo: str) -> Vinculo:
        """A3: vincula um monitor a uma disciplina (só administrador)."""
        if (not isinstance(usuario, Administrador) or not usuario.pode(Operacao.VINCULAR)):
            raise PermissaoNegada("Usuário sem permissão para vincular monitores.")

        monitor = self._buscar_monitor(matricula)
        disciplina = self._buscar_disciplina(codigo)
        existente = self._repositorio.buscar_vinculo(monitor.matricula,disciplina.codigo)

        if existente is not None:
            raise RegistroDuplicado("vínculo",f"{monitor.matricula}-{disciplina.codigo}")

        with self._repositorio.transacao():
            self._repositorio.inserir_vinculo(monitor.matricula, disciplina.codigo)

        vinculo = self._repositorio.buscar_vinculo(monitor.matricula, disciplina.codigo)

        return vinculo

    def desvincular(self, usuario: Usuario, matricula: str, codigo: str) -> int:
        """A4: remove o vínculo do monitor com a disciplina e só os horários dele.
        Devolve quantos horários foram removidos.
        Lança PermissaoNegada, DadosInvalidos, MatriculaNaoCadastrada,
        DisciplinaForaDoEscopo ou VinculoInexistente; nada muda se rejeitar."""
        if not isinstance(usuario, Administrador) or not usuario.pode(Operacao.DESVINCULAR):
            raise PermissaoNegada("Usuário sem permissão para desvincular monitores.")
        if not isinstance(matricula, str) or not isinstance(codigo, str):
            raise DadosInvalidos("A matrícula e o código devem ser um texto.")

        monitor = self._buscar_monitor(matricula)
        disciplina = self._buscar_disciplina(codigo)
        if self._repositorio.buscar_vinculo(monitor.matricula, disciplina.codigo) is None:
            raise VinculoInexistente(monitor.matricula, disciplina.codigo)

        with self._repositorio.transacao():
            return self._repositorio.excluir_vinculo(monitor.matricula, disciplina.codigo)

    def entrar(self, matricula: str, senha: str) -> UsuarioCadastrado:
        """S1: autentica um monitor ou administrador e devolve o usuário.
        Lança CredenciaisInvalidas se o login falhar."""
        if not isinstance(matricula, str) or not isinstance(senha, str) or not matricula.strip() or not senha:
            raise CredenciaisInvalidas("Matrícula ou senha inválida.")
        matricula = matricula.strip()

        credenciais = self._repositorio.buscar_credenciais(matricula)

        if credenciais is None:
            raise CredenciaisInvalidas("Matrícula ou senha inválida.")

        senha_hash, senha_sal = credenciais

        if not conferir_senha(senha, senha_hash, senha_sal):
            raise CredenciaisInvalidas("Matrícula ou senha inválida.")

        usuario = self._repositorio.buscar_usuario(matricula)
        if usuario is None:
            raise CredenciaisInvalidas("Matrícula ou senha inválida.")

        return usuario

    def encontrar_conflito(self, matricula: str, atendimento: Atendimento, ignorar_id: int | None = None) -> tuple[Vinculo, Atendimento] | None:
        """Procura, nos vínculos do monitor, um atendimento que se sobreponha ao informado.
        ignorar_id desconsidera o próprio atendimento numa alteração."""
        matricula = matricula.strip()

        vinculos = self._repositorio.vinculos_do_monitor(matricula)
        for vinculo in vinculos:
            for existente in vinculo.atendimentos:
                if existente.id == ignorar_id and ignorar_id is not None:
                    continue

                if atendimento.sobrepoe(existente):
                    return vinculo, existente

        return None

    def cadastrar_presencial(self, usuario: Usuario, codigo: str, dia: str, inicio: str, fim: str, predio: str, sala: str) -> Atendimento:
        """F1a: cadastra um atendimento presencial no vínculo do monitor autenticado.
        Lança PermissaoNegada, DadosInvalidos, DisciplinaForaDoEscopo,
        VinculoInexistente ou ConflitoDeHorario."""
        atendimento = AtendimentoPresencial(dia, inicio, fim, predio, sala)

        return self._cadastrar_atendimento(usuario, codigo, atendimento)

    def cadastrar_online(self, usuario: Usuario, codigo: str, dia: str, inicio: str, fim: str, plataforma: str, link: str) -> Atendimento:
        """F1a: cadastra um atendimento online no vínculo do monitor autenticado.
        Lança PermissaoNegada, DadosInvalidos, DisciplinaForaDoEscopo,
        VinculoInexistente ou ConflitoDeHorario."""
        atendimento = AtendimentoOnline(dia, inicio, fim, plataforma, link)

        return self._cadastrar_atendimento(usuario, codigo, atendimento)

    def listar_meus_atendimentos(self, usuario: Usuario) -> tuple[tuple[Disciplina, Atendimento], ...]:
        """F1b: lista os horários do monitor autenticado como pares (disciplina, atendimento),
        ordenados por dia e horário. Só leitura."""
        if (not isinstance(usuario, Monitor) or not usuario.pode(Operacao.VISUALIZAR_HORARIOS)):
            raise PermissaoNegada(
                "Usuário sem permissão para visualizar horários.")

        monitor = self._buscar_monitor(usuario.matricula)
        vinculos = self._repositorio.vinculos_do_monitor(monitor.matricula)

        itens = []
        for vinculo in vinculos:
            for atendimento in vinculo.atendimentos:
                itens.append((vinculo.disciplina, atendimento))

        return tuple(sorted(itens, key=lambda item: (DIAS_VALIDOS.index(item[1].dia),item[1].inicio,item[1].id)))

    def alterar_horario(self, usuario: Usuario, id_atendimento: int, dia: str, inicio: str, fim: str) -> Atendimento:
        """F1c: altera dia e horários de um atendimento próprio, mantendo ID, disciplina,
        modalidade e local. Lança PermissaoNegada, DadosInvalidos, AtendimentoInexistente
        ou ConflitoDeHorario; nada muda se rejeitar."""
        if (not isinstance(usuario, Monitor) or not usuario.pode(Operacao.ALTERAR_HORARIO)):
            raise PermissaoNegada("Usuário sem permissão para alterar horários.")

        if type(id_atendimento) is not int or id_atendimento <= 0:
            raise DadosInvalidos("O ID do atendimento deve ser um inteiro positivo.")

        registro = self._repositorio.buscar_atendimento(id_atendimento)

        if registro is None:
            raise AtendimentoInexistente(id_atendimento)

        vinculo, antigo = registro
        if vinculo.monitor.matricula != usuario.matricula:
            raise PermissaoNegada("O atendimento pertence a outro monitor.")

        if antigo.modalidade() == "presencial":
            novo = AtendimentoPresencial(dia, inicio, fim, antigo.predio, antigo.sala)
        else:
            novo = AtendimentoOnline(dia, inicio, fim, antigo.plataforma, antigo.link)

        conflito = self.encontrar_conflito(usuario.matricula, novo, ignorar_id=id_atendimento)

        if conflito is not None:
            vinculo_conflitante, existente = conflito
            raise ConflitoDeHorario(vinculo_conflitante,existente)

        with self._repositorio.transacao():
            atualizado = self._repositorio.atualizar_atendimento(id_atendimento, novo)

        return atualizado

    def remover_atendimento(self, usuario: Usuario, id_atendimento: int) -> None:
        """F1d: remove um atendimento do monitor autenticado.
        Lança PermissaoNegada, DadosInvalidos ou AtendimentoInexistente; nada muda se rejeitar."""
        if (not isinstance(usuario, Monitor) or not usuario.pode(Operacao.REMOVER_ATENDIMENTO)):
            raise PermissaoNegada("Usuário sem permissão para remover horários.")

        if type(id_atendimento) is not int or id_atendimento <= 0:
            raise DadosInvalidos("O ID do atendimento deve ser um inteiro positivo.")

        registro = self._repositorio.buscar_atendimento(id_atendimento)

        if registro is None:
            raise AtendimentoInexistente(id_atendimento)

        vinculo, atendimento = registro

        if vinculo.monitor.matricula != usuario.matricula:
            raise PermissaoNegada("O atendimento pertence a outro monitor.")

        with self._repositorio.transacao():
            removido = self._repositorio.excluir_atendimento(id_atendimento)

            if not removido:
                raise AtendimentoInexistente(id_atendimento)

    def consultar_monitorias(self, codigo: str, modalidade: str | None = None, dia: str | None = None) -> ResultadoConsulta:
        """F2: consulta monitores e horários de uma disciplina (só leitura).
        Modalidade ("presencial" ou "online") e dia são opcionais; vazio ou None é sem filtro.
        Lança DadosInvalidos ou DisciplinaForaDoEscopo; nunca altera dados."""
        if not isinstance(codigo, str):
            raise DadosInvalidos("O código da disciplina deve ser um texto.")
        filtro = self._normalizar_modalidade(modalidade)
        filtro_dia = self._normalizar_dia(dia)
        disciplina = self._buscar_disciplina(codigo.strip())

        vinculos = self._repositorio.vinculos_da_disciplina(disciplina.codigo)
        if not vinculos:
            return ResultadoConsulta(
                disciplina, SituacaoConsulta.NENHUMA_MONITORIA_CADASTRADA, (), filtro, filtro_dia)

        if all(len(v.atendimentos) == 0 for v in vinculos):
            sem_horario = tuple(ItemConsulta(v.monitor, ()) for v in vinculos)
            return ResultadoConsulta(
                disciplina, SituacaoConsulta.MONITOR_SEM_HORARIOS, sem_horario, filtro, filtro_dia)

        com_filtro = filtro is not None or filtro_dia is not None
        itens = []
        for v in vinculos:
            horarios = tuple(sorted((a for a in v.atendimentos
                if (filtro is None or a.modalidade() == filtro)
                and (filtro_dia is None or a.dia == filtro_dia)), key=lambda a: (DIAS_VALIDOS.index(a.dia), a.inicio, a.id)))

            # com filtro, só aparece quem tem horário que combine
            if horarios or not com_filtro:
                itens.append(ItemConsulta(v.monitor, horarios))

        if not itens:
            return ResultadoConsulta(
                disciplina, SituacaoConsulta.SEM_HORARIOS_NA_MODALIDADE, (), filtro, filtro_dia)
        return ResultadoConsulta(
            disciplina, SituacaoConsulta.COM_HORARIOS, tuple(itens), filtro, filtro_dia)

    def listar_disciplinas(self) -> tuple[Disciplina, ...]:
        """Lista as disciplinas do catálogo, ordenadas pelo código."""
        return self._repositorio.listar_disciplinas()

    # -- AUXILIARES --

    def _buscar_monitor(self, matricula: str) -> Monitor:
        """Devolve o monitor ou lança MatriculaNaoCadastrada."""
        matricula = matricula.strip()
        usuario = self._repositorio.buscar_usuario(matricula)

        if not isinstance(usuario, Monitor):
            raise MatriculaNaoCadastrada(matricula)

        return usuario

    def _buscar_disciplina(self, codigo: str) -> Disciplina:
        """Devolve a disciplina ou lança DadosInvalidos / DisciplinaForaDoEscopo."""
        codigo = validar_codigo(codigo)
        disciplina = self._repositorio.buscar_disciplina(codigo)

        if disciplina is None:
            raise DisciplinaForaDoEscopo(codigo)

        return disciplina

    def _cadastrar_atendimento(self, usuario: Usuario, codigo: str, atendimento: Atendimento) -> Atendimento:
        """Valida permissão, vínculo e conflito e grava o atendimento; devolve-o com o ID.
        Nada muda se rejeitar."""
        if (not isinstance(usuario, Monitor) or not usuario.pode(Operacao.CADASTRAR_HORARIO)):
            raise PermissaoNegada("Usuário sem permissão para cadastrar horários.")

        matricula = usuario.matricula

        codigo = validar_codigo(codigo)
        monitor = self._buscar_monitor(matricula)
        disciplina = self._buscar_disciplina(codigo)

        vinculo = self._repositorio.buscar_vinculo(monitor.matricula, disciplina.codigo)

        if vinculo is None:
            raise VinculoInexistente(monitor.matricula, disciplina.codigo)

        conflito = self.encontrar_conflito(monitor.matricula, atendimento)

        if conflito is not None:
            vinculo_conflitante, existente = conflito
            raise ConflitoDeHorario(vinculo_conflitante, existente)

        with self._repositorio.transacao():
            cadastrado = self._repositorio.inserir_atendimento(monitor.matricula, disciplina.codigo, atendimento)

        return cadastrado

    @staticmethod
    def _normalizar_dia(dia: str | None) -> str | None:
        """Devolve None (todos os dias) ou o dia validado, em minúsculas."""
        if dia is None:
            return None
        if not isinstance(dia, str):
            raise DadosInvalidos("O dia deve ser um texto.")
        if dia.strip() == "":
            return None
        return validar_dia(dia)

    @staticmethod
    def _normalizar_modalidade(modalidade: str | None) -> str | None:
        """Devolve None (todas) ou "presencial"/"online" em minúsculas."""
        if modalidade is None:
            return None
        if not isinstance(modalidade, str):
            raise DadosInvalidos("A modalidade deve ser um texto.")
        texto = modalidade.strip().lower()
        if texto == "":
            return None
        if texto not in ("presencial", "online"):
            raise DadosInvalidos(
                "Modalidade desconhecida: use 'presencial', 'online' "
                "ou deixe em branco para ver todas.")
        return texto
