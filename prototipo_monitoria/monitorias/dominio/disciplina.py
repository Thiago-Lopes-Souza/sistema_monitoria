class Disciplina:

  def __init__(self, codigo: str, nome: str) -> None:
    codigo = codigo.strip().upper()
    if not codigo:
      raise ValueError("Código Inválido!")
    self._codigo = codigo

    nome = nome.strip().capitalize()
    if not nome:
      raise ValueError("Nome Inválido!")
    self._nome = nome

  @property
  def codigo(self) -> str:
    return self._codigo
  
  @property
  def nome(self) -> str:
    return self._nome
