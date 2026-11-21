"""Horários de atendimento: classe abstrata Atendimento e as subclasses presencial e online."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date

from .excecoes import DadosInvalidos
from .horario import formatar_minutos, para_minutos, validar_dia

class Atendimento(ABC):
    """Um horário semanal em que o monitor atende alunos.

    Classe abstrata: só as subclasses (presencial e online) podem ser criadas.
    Atributos, todos só leitura: dia, inicio, fim, registrado_em.
    """

    def __init__(self, dia: str, inicio: str, fim: str,
                 registrado_em: date | None = None) -> None:
        """Valida e cria o atendimento.

        Lança:
            DadosInvalidos se o dia ou os horários forem inválidos,
            ou se o início não for antes do fim.
        """
        
        dia_normalizado = validar_dia(dia)
        minutos_inicio = para_minutos(inicio)
        minutos_fim = para_minutos(fim)
        if minutos_inicio >= minutos_fim:
            raise DadosInvalidos(f"O início ({inicio}) precisa ser antes do fim ({fim}).")
        if registrado_em is None:
            registrado_em = date.today()

        self._dia = dia_normalizado
        self._inicio = minutos_inicio
        self._fim = minutos_fim
        self._registrado_em = registrado_em

    @property
    def dia(self) -> str:
        """Dia da semana, em minúsculas."""
        return self._dia

    @property
    def inicio(self) -> str:
        """Horário de início, "hh:mm"."""
        return formatar_minutos(self._inicio)
    
    @property
    def fim(self) -> str:
        """Horário de fim, "hh:mm"."""
        return formatar_minutos(self._fim)
    
    @property
    def registrado_em(self) -> date:
        """Data em que o horário foi registrado."""
        return self._registrado_em


    def sobrepoe(self, outro: Atendimento) -> bool:
        """Diz se este horário cruza com outro.

        Só há sobreposição no mesmo dia e quando os intervalos se cruzam.
        Horários encostados (14:00–16:00 e 16:00–18:00) NÃO se sobrepõem.
        A modalidade não importa: o monitor não pode estar em dois lugares.

        Recebe:
            outro: qualquer Atendimento (presencial ou online).
        Devolve:
            True se houver sobreposição; False caso contrário.
        """
        if self._dia != outro._dia:
            return False
        return self._inicio < outro._fim and outro._inicio < self._fim
    
    @abstractmethod
    def modalidade(self) -> str:
        """Devolve "presencial" ou "online"."""

    @abstractmethod
    def local(self) ->str:
        """Devolve onde o aluno deve ir para ser atendido"""


class AtendimentoPresencial(Atendimento):
    """Atendimento numa sala física. Atributos extras (só leitura): predio e sala."""

    def __init__(self, dia: str, inicio: str, fim: str, predio: str, sala: str,
                 registrado_em: date | None = None) -> None:
        """Valida e cria o atendimento presencial.

        Recebe, além dos dados de Atendimento:
            predio: ex.: "CAD 3" (obrigatório).
            sala: ex.: "204" (obrigatória).
        Lança:
            DadosInvalidos se algum dado for inválido ou vazio.
        """
        super().__init__(dia, inicio, fim, registrado_em)   # a mãe valida o que é comum
        predio = predio.strip()
        sala = sala.strip()
        if not predio or not sala:
            raise DadosInvalidos("Prédio e sala são obrigatórios.")
        self._predio = predio
        self._sala = sala

    @property
    def predio(self) -> str:
        """Prédio do atendimento."""
        return self._predio

    @property
    def sala(self) -> str:
        """Sala do atendimento."""
        return self._sala

    def modalidade(self) -> str:
        """Sempre "presencial"."""
        return "presencial"

    def local(self) -> str:
        """Prédio e sala, ex.: "CAD 3, sala 204"."""
        return f"{self._predio}, sala {self._sala}"
    

class AtendimentoOnline(Atendimento):
    """Atendimento por videochamada. Atributos extras (só leitura): plataforma e link.""" 

    def __init__(self, dia: str, inicio: str, fim: str, plataforma: str, link: str,
                 registrado_em: date | None = None) -> None:
        """Valida e cria o atendimento online.

        Recebe, além dos dados de Atendimento:
            plataforma: ex.: "Google Meet" (obrigatório).
            link: ex.: "https://meet.exemplo/abc" (obrigatório; precisa começar com https://).
        Lança:
            DadosInvalidos se algum dado for inválido ou vazio.
        """

        super().__init__(dia, inicio, fim, registrado_em)
        plataforma = plataforma.strip()
        link = link.strip()
        if not plataforma or not link:
            raise DadosInvalidos("Plataforma e link são obrigatórios.")
        if not link.startswith("https://"):
            raise DadosInvalidos(f"Link inválido: '{link}'. Ele precisa começar com https://.")
        self._plataforma = plataforma
        self._link = link


    @property
    def plataforma(self) -> str:
        """Plataforma do atendimento."""
        return self._plataforma

    @property
    def link(self) -> str:
        """link do atendimento."""
        return self._link

    def modalidade(self) -> str:
        """Sempre "online"."""
        return "online"

    def local(self) -> str:
        """Plataforma e link, ex.: "Google meet, https://meet.exemplo/abc"."""
        return f"{self._plataforma}: {self._link}"