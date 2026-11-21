"""CadastroMonitorias: ponto único de entrada do domínio (F1, F2 e preparação dos dados)."""

from monitorias.dominio.disciplina import Disciplina
from monitorias.dominio.monitor import Monitor
from monitorias.dominio.vinculo import Vinculo
from monitorias.dominio.atendimento import Atendimento
from monitorias.dominio.consulta import ItemConsulta, ResultadoConsulta, SituacaoConsulta
from monitorias.dominio.horario import validar_codigo
from monitorias.dominio.excecoes import (ConflitoDeHorario, DadosInvalidos, DisciplinaForaDoEscopo, MatriculaNaoCadastrada, VinculoInexistente)


class CadastroMonitorias:

    """Ponto de entrada do domínio (comunicação com menu): guarda disciplinas, monitores e vínculos
      e coordena as funcionalidades"""
    
    def __init__(self) -> None:
        """Cria um cadastro vazio, só em memória (os dados se perdem ao sair)."""
        self._disciplinas: dict[str, Disciplina] = {}        # chave: codigo
        self._monitores: dict[str, Monitor] = {}             # chave: matricula
        self._vinculos: dict[tuple[str, str], Vinculo] = {}  # chave: (matricula, codigo)

    def adicionar_disciplina(self, disciplina: Disciplina) -> None:
        """Registra uma disciplina no sistema."""
        if disciplina.codigo in self._disciplinas:
            raise DadosInvalidos("A disciplina já está cadastrada!")
        self._disciplinas[disciplina.codigo] = disciplina

    def adicionar_monitor(self, monitor: Monitor) -> None:
        """Registra um monitor pela matrícula."""
        if monitor.matricula in self._monitores:
            raise DadosInvalidos("O monitor já está cadastrado!")
        self._monitores[monitor.matricula] = monitor

    def vincular(self, matricula: str, codigo: str) -> Vinculo:
        """Cria o vínculo entre um monitor e uma disciplina já cadastrados."""
        monitor = self._buscar_monitor(matricula)
        disciplina = self._buscar_disciplina(codigo)
        chave = (monitor.matricula, disciplina.codigo)

        if chave in self._vinculos:
            raise DadosInvalidos(f"O monitor {monitor.nome} já está vinculado a disciplina {disciplina.codigo}!")

        vinculo = Vinculo(monitor, disciplina)
        self._vinculos[chave] = vinculo
        return vinculo

    def encontrar_conflito(self, matricula: str, atendimento: Atendimento) -> tuple[Vinculo, Atendimento] | None:
        """Método de CONSULTA.
          Procura nos vínculos do monitor um atendimento que se sobreponha ao informado."""
        matricula = matricula.strip()

        for vinculo in self._vinculos.values():
            
            if vinculo.monitor.matricula != matricula:
                continue
            for existente in vinculo.atendimentos:
                if atendimento.sobrepoe(existente):
                    return vinculo, existente
                
        return None

    def cadastrar_atendimento(self, matricula: str, codigo: str, atendimento: Atendimento) -> Atendimento:
        """Cadastra um atendimento no vínculo do monitor com a disciplina.
          Lança MatriculaNaoCadastrada, DisciplinaForaDoEscopo,
          VinculoInexistente ou ConflitoDeHorario."""
        codigo = validar_codigo(codigo)
        monitor = self._buscar_monitor(matricula)
        disciplina = self._buscar_disciplina(codigo)
        vinculo = self._vinculos.get((monitor.matricula, disciplina.codigo)) # Retorna Vinculo ou None

        if vinculo is None:
            raise VinculoInexistente(monitor.matricula, disciplina.codigo)
        conflito = self.encontrar_conflito(monitor.matricula, atendimento)

        if conflito is not None:
            vinculo_conflitante, existente = conflito
            raise ConflitoDeHorario(vinculo_conflitante, existente)
        
        vinculo.adicionar_atendimento(atendimento)
        return atendimento
    

    # -- AUXILIARES --
    
    def _buscar_monitor(self, matricula: str) -> Monitor:
        """Retorna o monitor ou lança MatriculaNaoCadastrada."""
        matricula = matricula.strip()
        monitor = self._monitores.get(matricula)
        if monitor is None:
            raise MatriculaNaoCadastrada(matricula)
        return monitor

    def _buscar_disciplina(self, codigo: str) -> Disciplina:
        """Retorna a disciplina cadastrada, ou lança DadosInvalidos ou DisciplinaForaDoEscopo."""
        codigo = validar_codigo(codigo)
        disciplina = self._disciplinas.get(codigo)
        if disciplina is None:
            raise DisciplinaForaDoEscopo(codigo)
        return disciplina
    
    def consultar_monitorias(self, codigo: str, modalidade: str | None = None) -> ResultadoConsulta:
        """F2: consulta monitores e horários de uma disciplina (só leitura).
          Recebe o código (AAA999, maiúsculas ou minúsculas) e a modalidade
          opcional ("presencial", "online" ou vazio para todas).
          Devolve um ResultadoConsulta com uma das quatro situações.
          Lança DadosInvalidos (código mal formatado ou modalidade desconhecida)
          e DisciplinaForaDoEscopo (código fora do catálogo).
          Não altera nenhum dado, nem quando rejeita."""
        if not isinstance(codigo, str):
            raise DadosInvalidos("O código da disciplina deve ser um texto.")
        filtro = self._normalizar_modalidade(modalidade)
        disciplina = self._buscar_disciplina(codigo.strip())

        vinculos = [v for v in self._vinculos.values()
                    if v.disciplina.codigo == disciplina.codigo]
        if not vinculos:
            return ResultadoConsulta(
                disciplina, SituacaoConsulta.NENHUMA_MONITORIA_CADASTRADA, (), filtro)

        if all(len(v.atendimentos) == 0 for v in vinculos):
            sem_horario = tuple(ItemConsulta(v.monitor, ()) for v in vinculos)
            return ResultadoConsulta(
                disciplina, SituacaoConsulta.MONITOR_SEM_HORARIOS, sem_horario, filtro)

        itens = []
        for v in vinculos:
            horarios = tuple(a for a in v.atendimentos
                             if filtro is None or a.modalidade() == filtro)
            # Sem filtro, todo monitor vinculado aparece, mesmo sem horário
            # (o aluno vê o e-mail); com filtro, só quem tem horário na modalidade.
            if horarios or filtro is None:
                itens.append(ItemConsulta(v.monitor, horarios))

        if not itens:
            return ResultadoConsulta(
                disciplina, SituacaoConsulta.SEM_HORARIOS_NA_MODALIDADE, (), filtro)
        return ResultadoConsulta(
            disciplina, SituacaoConsulta.COM_HORARIOS, tuple(itens), filtro)

    def listar_disciplinas(self) -> tuple[Disciplina, ...]:
        """Lista as disciplinas do catálogo, ordenadas pelo código."""
        return tuple(sorted(self._disciplinas.values(), key=lambda d: d.codigo))

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