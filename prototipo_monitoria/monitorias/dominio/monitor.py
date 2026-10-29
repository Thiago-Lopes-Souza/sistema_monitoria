from vinculo import Vinculo
from atendimento import Atendimento

class Monitor:

  def __init__(self, matricula: str, nome: str, email: str) -> None:
    matricula = matricula.strip()
    if not matricula:
      raise ValueError("Matrícula Inválida!")
    self._matricula = matricula

    nome = nome.strip().capitalize()
    if not nome:
      raise ValueError("Nome Inválido!")
    self._nome = nome

    email = email.strip().lower()
    self.email = email

  @property
  def matricula(self) -> str:
    return self._matricula
  @property
  def nome(self) -> str:
    return self._nome
  @property
  def email(self) -> str:
    return self._email
  @property
  def vinculos(self) -> str:
    return self._vinculos

  @email.setter
  def email(self, novo_email: str) -> str:
    if not self.email or "@ufmg.br" not in self.email:
      raise ValueError("Nome Inválido!")
    self._email = novo_email

  # Metodos
  def buscar_vinculo(codigo: str) -> Vinculo | None:
    pass
  
  def encontrar_conflito(novo: Atendimento) -> Vinculo | Atendimento | None:
    pass