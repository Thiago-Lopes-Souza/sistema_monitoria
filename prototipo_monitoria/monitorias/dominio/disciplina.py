from monitorias.dominio.excecoes import DadosInvalidos
from monitorias.dominio.horario import validar_codigo

class Disciplina:

    """Disciplina da grade, identificada pelo código (ex.: MAT001).
      Código e nome 'read only' Duas disciplinas com MESMO CÓDIGO são iguais."""

    def __init__(self, codigo: str, nome: str) -> None:
        """Cria uma disciplina.
          Código no formato (ABC123).
          Lança DadosInvalidos se código inválido ou se nome vazio."""
        if not codigo.strip():
          raise DadosInvalidos("O código da disciplina é obrigatório!")
        self._codigo = validar_codigo(codigo)

        nome = nome.strip()
        if not nome:
          raise DadosInvalidos("O nome da disciplina é obrigatório!")
        self._nome = nome

    @property
    def codigo(self) -> str:
        return self._codigo
    
    @property
    def nome(self) -> str:
        return self._nome

    def __eq__(self, outra_disciplina: object) -> bool:
        if not isinstance(outra_disciplina, Disciplina):
          return NotImplemented
        return self.codigo == outra_disciplina.codigo

    def __hash__(self) -> int:
        return hash(self.codigo)
