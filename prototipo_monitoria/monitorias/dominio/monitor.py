from monitorias.dominio.excecoes import DadosInvalidos

class Monitor:

    """Monitor da UFMG..
    Guarda matrícula, nome e e-mail institucional.
    Matrícula e nome 'read only', o e-mail com setter e validação"""

    def __init__(self, matricula: str, nome: str, email: str) -> None:
        """Cria um monitor.
          Lança DadosInvalidos se matrícula ou nome vazios ou e-mail inválido."""
        matricula = matricula.strip()
        if not matricula:
            raise DadosInvalidos("A matrícula do monitor é obrigatória!")
        self._matricula = matricula

        nome = nome.strip()
        if not nome:
            raise DadosInvalidos("O nome do monitor é obrigatório!")
        self._nome = nome

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

    @email.setter
    def email(self, novo_email: str) -> None:
        novo_email = novo_email.strip().lower()
        if not novo_email or not novo_email.endswith("@ufmg.br"):
            raise DadosInvalidos("O e-mail deve ser institucional e terminar em '@ufmg.br'.")
        self._email = novo_email
