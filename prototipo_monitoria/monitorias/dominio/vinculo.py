from monitor import Monitor
from disciplina import Disciplina

# Verificar imports, ainda nao tenho atendimento.py

class Vinculo:

  def __init__(self, monitor: Monitor, disciplina: Disciplina) -> None:
    self._monitor = monitor
    self._disciplina = disciplina
    self._atendimentos = [] #list[Atendimentos]

  @property
  def monitor(self) -> str:
    return self._monitor
  
  @property
  def disciplina(self) -> str:
    return self._disciplina

  @property
  def atendimentos(self) -> tuple:
    return tuple(sorted(self._atendimentos))

  # Metodos
  def adicionar_atendimento(self, atendimento: Atendimento) -> None:
    self._atendimentos.append(atendimento)
