"""Monitor de disciplina, identificado pela matrícula."""

from monitorias.dominio.excecoes import DadosInvalidos

class Monitor:

    """Monitor da UFMG.
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
        """Matrícula do monitor, sem espaços nas pontas. Só leitura (identifica o monitor)."""
        return self._matricula

    @property
    def nome(self) -> str:
        """Nome do monitor. Só leitura."""
        return self._nome

    @property
    def email(self) -> str:
        """E-mail institucional do monitor, em minúsculas (único contato mostrado ao aluno)."""
        return self._email

    @email.setter
    def email(self, novo_email: str) -> None:
        """Troca o e-mail, validando ANTES de alterar.

        Recebe:
            novo_email: e-mail terminado em "@ufmg.br" (normalizado para minúsculas).
        Lança:
            DadosInvalidos se vazio ou não institucional; nesse caso o e-mail
            anterior continua valendo.
        """
        novo_email = novo_email.strip().lower()
        if not novo_email or not novo_email.endswith("@ufmg.br"):
            raise DadosInvalidos("O e-mail deve ser institucional e terminar em '@ufmg.br'.")
        self._email = novo_email
