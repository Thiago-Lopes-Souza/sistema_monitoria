from monitorias.dominio.monitor import Monitor
from monitorias.dominio.disciplina import Disciplina
from monitorias.dominio.atendimento import Atendimento
from monitorias.dominio.horario import DIAS_VALIDOS

class Vinculo:

    """Liga um monitor a uma disciplina e guarda os atendimentos desse vínculo."""

    def __init__(self, monitor: Monitor, disciplina: Disciplina) -> None:
        """Cria um vínculo sem atendimentos."""
        self._monitor = monitor
        self._disciplina = disciplina
        self._atendimentos: list[Atendimento] = []

    @property
    def monitor(self) -> Monitor:
        return self._monitor
    
    @property
    def disciplina(self) -> Disciplina:
        return self._disciplina

    @property
    def atendimentos(self) -> tuple[Atendimento, ...]:
        return tuple(sorted(self._atendimentos, key=lambda a: (DIAS_VALIDOS.index(a.dia), a.inicio)))

    # Metodos
    def adicionar_atendimento(self, atendimento: Atendimento) -> None:
        """Acrescenta um atendimento ao vínculo.
          Só o 'CadastroMonitorias' chama o método após validação."""
        self._atendimentos.append(atendimento)
