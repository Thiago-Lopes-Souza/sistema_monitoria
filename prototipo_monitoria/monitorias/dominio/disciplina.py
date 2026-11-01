"""Disciplina do catálogo de Engenharia de Sistemas ofertado em 2026/2."""

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
        """Código da disciplina em maiúsculas, ex.: "DCC203". Só leitura."""
        return self._codigo

    @property
    def nome(self) -> str:
        """Nome da disciplina, sem espaços nas pontas. Só leitura."""
        return self._nome

    def __eq__(self, outra_disciplina: object) -> bool:
        """Duas disciplinas são iguais quando têm o mesmo código."""
        if not isinstance(outra_disciplina, Disciplina):
            return NotImplemented
        return self.codigo == outra_disciplina.codigo

    def __hash__(self) -> int:
        """Hash pelo código, coerente com __eq__."""
        return hash(self.codigo)
