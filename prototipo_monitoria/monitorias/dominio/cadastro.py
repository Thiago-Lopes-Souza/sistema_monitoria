"""CadastroMonitorias: ponto único de entrada do domínio (F1, F2 e preparação dos dados)."""

from monitorias.dominio.disciplina import Disciplina
from monitorias.dominio.monitor import Monitor
from monitorias.dominio.vinculo import Vinculo
from monitorias.dominio.atendimento import Atendimento, AtendimentoOnline, AtendimentoPresencial
from monitorias.dominio.consulta import ItemConsulta, ResultadoConsulta, SituacaoConsulta
from monitorias.dominio.horario import validar_codigo, validar_dia
from monitorias.dominio.excecoes import (
    ConflitoDeHorario, DadosInvalidos, DisciplinaForaDoEscopo, MatriculaNaoCadastrada, VinculoInexistente, CredenciaisInvalidas)
from monitorias.persistencia.repositorio import RepositorioMonitorias
from monitorias.dominio.senha import conferir_senha
from monitorias.dominio.usuario import UsuarioCadastrado


class CadastroMonitorias:

    """Ponto de entrada do domínio (comunicação com menu): guarda disciplinas, monitores e vínculos
      e coordena as funcionalidades"""
    
    def __init__(self, repositorio: RepositorioMonitorias):
        """Recebe o repositório responsável pela persistência dos dados."""
        self._repositorio = repositorio

    def adicionar_disciplina(self, disciplina: Disciplina) -> None:
        """Registra uma disciplina no sistema."""
        if disciplina.codigo in self._repositorio.listar_disciplinas():
            raise DadosInvalidos("A disciplina já está cadastrada!")
        self._repositorio.inserir_disciplina(disciplina)

    def adicionar_monitor(self, monitor: Monitor) -> None:
        """Registra um monitor no sistema."""
        if monitor.matricula in self._repositorio.buscar_usuario(monitor.matricula):
            raise DadosInvalidos("O monitor já está cadastrado!")
        self._repositorio._inserir_usuario()

    def vincular(self, matricula: str, codigo: str) -> Vinculo:
        """Cria o vínculo entre um monitor e uma disciplina já cadastrados."""
        monitor = self._buscar_monitor(matricula)
        disciplina = self._buscar_disciplina(codigo)

        if matricula in self._repositorio.vinculos_do_monitor(matricula):
            raise DadosInvalidos(f"O monitor {monitor.nome} já está vinculado a disciplina {disciplina.codigo}!")

        vinculo = Vinculo(monitor, disciplina)
        return vinculo

    def entrar(self, matricula: str, senha: str):
        """Autentica um monitor ou administrador.
        Recebe matrícula e senha.
        Retorna o usuário autenticado.
        Lança CredenciaisInvalidas se o login falhar.
        """
        if not isinstance(matricula, str) or not isinstance(senha, str) or not matricula.strip() or not senha:
            raise CredenciaisInvalidas("Matrícula ou senha inválida")
        matricula = matricula.strip()

        credenciais = self._repositorio.buscar_credenciais(matricula)

        if credenciais is None:
            raise CredenciaisInvalidas("Matrícula ou senha inválida.")
        
    # Verifica a senha informada.
        senha_hash, senha_sal = credenciais

        if not conferir_senha(senha, senha_hash, senha_sal):
            raise CredenciaisInvalidas("Matrícula ou senha inválida.")

    # Recupera o usuário autenticado.
        usuario = self._repositorio.buscar_usuario(matricula)
        if usuario is None:
            raise CredenciaisInvalidas("Matrícula ou senha inválida.")
        
        return usuario

    def encontrar_conflito(self, matricula: str, atendimento: Atendimento, ignorar_id: int | None = None) -> tuple[Vinculo, Atendimento] | None:
        """Método de CONSULTA.
        Procura nos vínculos do monitor um atendimento que se sobreponha ao informado.
        ignorar_id permite desconsiderar o próprio atendimento durante uma alteração de horário  
        """
        matricula = matricula.strip()

        vinculos = self._repositorio.vinculos_do_monitor(matricula)
        for vinculo in vinculos:
            for existente in vinculo.atendimentos:
                if existente.id == ignorar_id and ignorar_id is not None:
                    continue

                if atendimento.sobrepoe(existente):
                    return vinculo, existente

        return None

    def cadastrar_presencial(self, matricula: str, codigo: str, dia: str, inicio: str, fim: str, predio: str, sala: str) -> Atendimento:
        """Cria e cadastra um atendimento online no vínculo do monitor.
            Recebe: matrícula, código da disciplina, dia, horários, plataforma e link.
            Retorna: o AtendimentoOnline cadastrado.
            Lança DadosInvalidos, MatriculaNaoCadastrada, DisciplinaForaDoEscopo,
            VinculoInexistente ou ConflitoDeHorario."""

        atendimento = AtendimentoPresencial(dia, inicio, fim, predio, sala)

        return self._cadastrar_atendimento(matricula, codigo, atendimento)


    def cadastrar_online(self, matricula: str, codigo: str, dia: str, inicio: str, fim: str, plataforma: str, link: str) -> Atendimento:
        """Cria e cadastra um atendimento presencial no vínculo do monitor.
            Recebe: matrícula, código da disciplina, dia, horários, prédio e sala.
            Retorna: o AtendimentoPresencial cadastrado.
            Lança DadosInvalidos, MatriculaNaoCadastrada, DisciplinaForaDoEscopo,
            VinculoInexistente ou ConflitoDeHorario."""

        atendimento = AtendimentoOnline(dia, inicio, fim, plataforma, link)

        return self._cadastrar_atendimento(matricula, codigo, atendimento)


    def consultar_monitorias(self, codigo: str, modalidade: str | None = None, dia: str | None = None) -> ResultadoConsulta:
        """F2: consulta monitores e horários de uma disciplina (só leitura).
          Recebe o código (AAA999, maiúsculas ou minúsculas) e, opcionalmente, a
          modalidade ("presencial" ou "online") e o dia da semana. Vazio ou None
          significa sem filtro; com os dois, vale a combinação.
          Devolve um ResultadoConsulta com uma das quatro situações.
          Lança DadosInvalidos (código mal formatado, modalidade ou dia
          desconhecidos) e DisciplinaForaDoEscopo (código fora do catálogo).
          Não altera nenhum dado, nem quando rejeita."""
        
        if not isinstance(codigo, str):
            raise DadosInvalidos("O código da disciplina deve ser um texto.")
        filtro = self._normalizar_modalidade(modalidade)
        filtro_dia = self._normalizar_dia(dia)
        disciplina = self._buscar_disciplina(codigo.strip())

        vinculos = [v for v in self._vinculos.values()
                    if v.disciplina.codigo == disciplina.codigo]
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
            horarios = tuple(a for a in v.atendimentos
                             if (filtro is None or a.modalidade() == filtro)
                             and (filtro_dia is None or a.dia == filtro_dia))
            # Sem filtro, aparece todo monitor vinculado; com filtro, só quem tem horário que combine.
            if horarios or not com_filtro:
                itens.append(ItemConsulta(v.monitor, horarios))

        if not itens:
            return ResultadoConsulta(
                disciplina, SituacaoConsulta.SEM_HORARIOS_NA_MODALIDADE, (), filtro, filtro_dia)
        return ResultadoConsulta(
            disciplina, SituacaoConsulta.COM_HORARIOS, tuple(itens), filtro, filtro_dia)

    def listar_disciplinas(self) -> tuple[Disciplina, ...]:
        """Lista as disciplinas do catálogo no repositório, ordenadas pelo código."""
        return self._repositorio.listar_disciplinas()
    
    # =============================  AUXILIARES  ===========================================================
    
    def _buscar_monitor(self, matricula: str) -> Monitor:
        """Busca um monitor no repositório pela matrícula."""
        matricula = matricula.strip()
        usuario = self._repositorio.buscar_usuario(matricula)
        
        if not isinstance(usuario, Monitor):
            raise MatriculaNaoCadastrada(matricula)
        
        return usuario

    def _buscar_disciplina(self, codigo: str) -> Disciplina:
        """Busca um monitor no repositório pela matrícula."""
        codigo = validar_codigo(codigo)
        disciplina = self._repositorio.buscar_disciplina(codigo)
        
        if disciplina is None:
            raise DisciplinaForaDoEscopo(codigo)
        
        return disciplina

    def _cadastrar_atendimento(self, matricula: str, codigo: str, atendimento: Atendimento) -> Atendimento:
        """Valida o vínculo e os conflitos antes de gravar
        o atendimento no repositório SQLite.
        Retorna o atendimento cadastrado, já com seu ID.
        Não altera o banco em caso de rejeição.
        """
        
        codigo = validar_codigo(codigo)
        monitor = self._buscar_monitor(matricula)
        disciplina = self._buscar_disciplina(codigo)

        vinculo = self._repositorio.buscar_vinculo(monitor.matricula, disciplina.codigo) # Retorna Vinculo ou None

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
        """Devolve None (todos os dias) ou o dia validado, em minúsculas.
          Lança DadosInvalidos para texto que não seja um dia de segunda a sábado."""
        if dia is None:
            return None
        if not isinstance(dia, str):
            raise DadosInvalidos("O dia deve ser um texto.")
        if dia.strip() == "":
            return None
        return validar_dia(dia)

    @staticmethod
    def _normalizar_modalidade(modalidade: str | None) -> str | None:
        """Devolve None (todas) ou "presencial"/"online" em minúsculas.
          Lança DadosInvalidos para qualquer outro valor."""
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

    # ======================================================================================================   
    