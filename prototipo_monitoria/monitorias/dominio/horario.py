from .excecoes import DadosInvalidos
import re

DIAS_VALIDOS = ("segunda" , "terça", "quarta", "quinta", "sexta", "sábado")

_PADRAO_HORA = re.compile(r"^(\d{1,2}):(\d{2})$")

_PADRAO_CODIGO = re.compile(r"^[A-Z]{3}[0-9]{3}$")

def para_minutos(texto: str) -> int:
    """Converte um horário "hh:mm" em minutos desde a meia-noite.

    Exemplo: "14:30" -> 870.

    Recebe:
        texto: horário local no formato hh:mm (horas de 0 a 23).
    Devolve:
        o total de minutos (int).
    Lança:
        DadosInvalidos se o formato ou os valores forem inválidos.
    """

    resultado = _PADRAO_HORA.match(texto.strip())        
    if resultado is None:                                 
        raise DadosInvalidos(
            f"Horário inválido: '{texto}'. Use o formato hh:mm, ex.: 14:30."
        )
    horas = int(resultado.group(1))                       
    minutos = int(resultado.group(2))                     
    if horas > 23 or minutos > 59:                        
        raise DadosInvalidos(f"Horário inexistente: '{texto}'.")
    return horas * 60 + minutos          

def validar_dia(dia: str) ->str:
    """Normaliza e valida um dia da semana.

    Recebe:
        dia: texto como "Terça" ou " quinta ".
    Devolve:
        o dia em minúsculas e sem espaços, ex.: "terça".
    Lança:
        DadosInvalidos se não for um dos DIAS_VALIDOS.
    """

    dia_normalizado = dia.strip().lower()
    if dia_normalizado not in DIAS_VALIDOS:
        raise DadosInvalidos(f"Dia inválido: '{dia_normalizado}'")
    return dia_normalizado

def validar_codigo(codigo: str) -> str:
    """Normaliza e valida um código de disciplina.

    Recebe:
        codigo: texto como "dcc203" ou " DCC203 ".
    Devolve:
        o código em maiúsculas e sem espaços, ex.: "DCC203".
    Lança:
        DadosInvalidos se não seguir o padrão três letras + três números.
    """
    normalizado = codigo.strip().upper()                 
    if _PADRAO_CODIGO.match(normalizado) is None:      
        raise DadosInvalidos(
            f"Código de disciplina inválido: '{codigo}'. "
            "Use três letras e três números, ex.: DCC203."
        )
    return normalizado   

def formatar_minutos(minutos: int) -> str:
    """Converte minutos desde a meia-noite em "hh:mm". Ex.: 545 -> "09:05"."""
    return f"{minutos // 60:02d}:{minutos % 60:02d}"