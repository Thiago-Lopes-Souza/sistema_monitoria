"""Vínculo entre um monitor e uma disciplina, com os horários de atendimento."""

from monitorias.dominio.monitor import Monitor
from monitorias.dominio.disciplina import Disciplina
from monitorias.dominio.atendimento import Atendimento
from monitorias.dominio.horario import DIAS_VALIDOS

class Vinculo:

    """Liga um monitor a uma disciplina e guarda os atendimentos desse vínculo."""

    def __init__(self, monitor: Monitor, disciplina: Disciplina,
                 atendimentos: tuple[Atendimento, ...] = ()) -> None:
        """Cria um vínculo.

        Recebe:
            atendimentos: horários que o vínculo já tem. Só o repositório passa
                este argumento, ao remontar o vínculo a partir da base de dados,
                onde os horários já foram validados quando foram gravados. Um
                vínculo novo (vincular) começa vazio.
        """
        self._monitor = monitor
        self._disciplina = disciplina
        self._atendimentos: list[Atendimento] = list(atendimentos)

    @property
    def monitor(self) -> Monitor:
        """Monitor do vínculo. Só leitura."""
        return self._monitor

    @property
    def disciplina(self) -> Disciplina:
        """Disciplina do vínculo. Só leitura."""
        return self._disciplina

    @property
    def atendimentos(self) -> tuple[Atendimento, ...]:
        """Cópia dos atendimentos, ordenada por dia da semana e início.

        Sem setter: horários só entram por _adicionar_atendimento, chamado pelo
        CadastroMonitorias depois de todas as verificações.
        """
        return tuple(sorted(self._atendimentos, key=lambda a: (DIAS_VALIDOS.index(a.dia), a.inicio)))
