"""Repositório: tradução entre os objetos do domínio e as linhas do SQLite.

Responsabilidades (camada de dados):
    * guardar e recuperar registros com SQL parametrizado (só placeholders ?);
    * montar objetos do domínio a partir das linhas, e linhas a partir dos objetos;
    * transformar a chave repetida recusada pela base em RegistroDuplicado.

O que ele NÃO faz: decidir regras. Conflito de horário, vínculo existente,
permissão e titularidade são do CadastroMonitorias. O repositório grava o que
recebe, e por isso os métodos de gravação são chamados só pelo cadastro,
depois de todas as validações, dentro de repositorio.transacao().

Cada leitura monta objetos novos a partir da base. Não há cache: o SQLite é a
única fonte de verdade, como o plano do produto final pede.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date

from monitorias.dominio.atendimento import (
    Atendimento,
    AtendimentoOnline,
    AtendimentoPresencial,
)
from monitorias.dominio.disciplina import Disciplina
from monitorias.dominio.excecoes import RegistroDuplicado
from monitorias.dominio.monitor import Monitor
from monitorias.dominio.usuario import Administrador, UsuarioCadastrado
from monitorias.dominio.vinculo import Vinculo

# Classe do domínio que corresponde a cada valor da coluna usuarios.papel.
# Ler da base não precisa de if/isinstance: o papel escolhe a classe.
_CLASSE_POR_PAPEL = {"monitor": Monitor, "admin": Administrador}

_COLUNAS_ATENDIMENTO = (
    "a.id, a.matricula, a.codigo, a.dia, a.inicio, a.fim, a.modalidade, "
    "a.predio, a.sala, a.plataforma, a.link, a.registrado_em"
)


class RepositorioMonitorias:
    """Acesso à base de dados do sistema de monitorias.

    Recebe uma conexão pronta (veja conexao.abrir_base). Assim os testes podem
    usar uma base ":memory:", que só existe dentro da conexão que a criou.
    """

    def __init__(self, conexao: sqlite3.Connection) -> None:
        """Guarda a conexão. Não abre nem fecha nada."""
        self._conexao = conexao
        self._profundidade = 0  # quantas transacao() estão abertas, uma dentro da outra

    # ------------------------------------------------------------------
    # Transação
    # ------------------------------------------------------------------

    @contextmanager
    def transacao(self) -> Iterator[None]:
        """Agrupa gravações: ou todas valem, ou nenhuma.

        Uso, no cadastro, depois de todas as validações:

            with repositorio.transacao():
                repositorio.excluir_vinculo(...)

        Se o bloco terminar normalmente, faz commit. Se qualquer exceção sair
        do bloco, faz rollback e deixa a exceção seguir. Uma transacao() dentro
        de outra entra na de fora: só a mais externa faz commit ou rollback.
        """
        if self._profundidade > 0:
            self._profundidade += 1
            try:
                yield
            finally:
                self._profundidade -= 1
            return
        self._profundidade = 1
        try:
            with self._conexao:  # commit no fim, rollback em exceção; não fecha a conexão
                yield
        finally:
            self._profundidade = 0

    def _exigir_transacao(self) -> None:
        """Impede gravação solta, que ficaria sem commit e sem rollback."""
        if self._profundidade == 0:
            raise RuntimeError(
                "Gravação fora de transação: use 'with repositorio.transacao():'."
            )

    def _executar_gravacao(self, sql: str, parametros: tuple, tipo: str, chave: str) -> sqlite3.Cursor:
        """Executa um INSERT/UPDATE/DELETE, traduzindo chave repetida em RegistroDuplicado.

        Outras violações (CHECK, chave estrangeira) seguem como
        sqlite3.IntegrityError: indicam que o domínio deixou passar algo, e
        esconder isso atrapalharia achar o defeito.
        """
        self._exigir_transacao()
        try:
            return self._conexao.execute(sql, parametros)
        except sqlite3.IntegrityError as erro:
            texto = str(erro)
            if "UNIQUE constraint failed" in texto or "PRIMARY KEY" in texto:
                raise RegistroDuplicado(tipo, chave) from erro
            raise

    def esta_vazia(self) -> bool:
        """Diz se a base ainda não tem usuários nem disciplinas (usado pela carga)."""
        linha = self._conexao.execute(
            "SELECT EXISTS(SELECT 1 FROM usuarios) OR EXISTS(SELECT 1 FROM disciplinas)"
        ).fetchone()
        return linha[0] == 0

    # ------------------------------------------------------------------
    # Usuários (monitor e administrador)
    # ------------------------------------------------------------------

    def inserir_monitor(self, monitor: Monitor, senha_hash: bytes, senha_sal: bytes) -> None:
        """Grava um monitor. Lança RegistroDuplicado se a matrícula já existir."""
        self._inserir_usuario(monitor, "monitor", senha_hash, senha_sal)

    def inserir_administrador(self, administrador: Administrador,
                              senha_hash: bytes, senha_sal: bytes) -> None:
        """Grava um administrador. Lança RegistroDuplicado se a matrícula já existir."""
        self._inserir_usuario(administrador, "admin", senha_hash, senha_sal)

    def _inserir_usuario(self, usuario: Monitor | UsuarioCadastrado, papel: str,
                         senha_hash: bytes, senha_sal: bytes) -> None:
        """Grava a linha de usuarios. O papel vem do método público chamado."""
        self._executar_gravacao(
            "INSERT INTO usuarios (matricula, nome, email, papel, senha_hash, senha_sal) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (usuario.matricula, usuario.nome, usuario.email, papel,
             bytes(senha_hash), bytes(senha_sal)),
            "matrícula", usuario.matricula,
        )

    def buscar_usuario(self, matricula: str) -> Monitor | Administrador | None:
        """Devolve o Monitor ou o Administrador dessa matrícula, ou None.

        O objeto devolvido não carrega a senha: o hash fica na base e só sai
        por buscar_credenciais, usado apenas pelo login.
        """
        linha = self._conexao.execute(
            "SELECT matricula, nome, email, papel FROM usuarios WHERE matricula = ?",
            (matricula.strip(),),
        ).fetchone()
        if linha is None:
            return None
        classe = _CLASSE_POR_PAPEL[linha["papel"]]
        return classe(linha["matricula"], linha["nome"], linha["email"])

    def buscar_credenciais(self, matricula: str) -> tuple[bytes, bytes] | None:
        """Devolve (senha_hash, senha_sal) da matrícula, ou None se ela não existir."""
        linha = self._conexao.execute(
            "SELECT senha_hash, senha_sal FROM usuarios WHERE matricula = ?",
            (matricula.strip(),),
        ).fetchone()
        if linha is None:
            return None
        return bytes(linha["senha_hash"]), bytes(linha["senha_sal"])

    # ------------------------------------------------------------------
    # Disciplinas
    # ------------------------------------------------------------------

    def inserir_disciplina(self, disciplina: Disciplina) -> None:
        """Grava uma disciplina. Lança RegistroDuplicado se o código já existir."""
        self._executar_gravacao(
            "INSERT INTO disciplinas (codigo, nome) VALUES (?, ?)",
            (disciplina.codigo, disciplina.nome),
            "disciplina", disciplina.codigo,
        )

    def buscar_disciplina(self, codigo: str) -> Disciplina | None:
        """Devolve a disciplina com esse código, ou None."""
        linha = self._conexao.execute(
            "SELECT codigo, nome FROM disciplinas WHERE codigo = ?",
            (codigo.strip().upper(),),
        ).fetchone()
        return None if linha is None else Disciplina(linha["codigo"], linha["nome"])

    def listar_disciplinas(self) -> tuple[Disciplina, ...]:
        """Todas as disciplinas, ordenadas pelo código."""
        linhas = self._conexao.execute(
            "SELECT codigo, nome FROM disciplinas ORDER BY codigo"
        ).fetchall()
        return tuple(Disciplina(l["codigo"], l["nome"]) for l in linhas)

    # ------------------------------------------------------------------
    # Vínculos
    # ------------------------------------------------------------------

    def inserir_vinculo(self, matricula: str, codigo: str) -> None:
        """Grava o vínculo (monitor, disciplina).

        Lança RegistroDuplicado se o par já existir. Se a matrícula ou o código
        não existirem, a chave estrangeira recusa (sqlite3.IntegrityError): o
        cadastro deve ter conferido antes.
        """
        self._executar_gravacao(
            "INSERT INTO vinculos (matricula, codigo) VALUES (?, ?)",
            (matricula, codigo),
            "vínculo", f"{matricula}–{codigo}",
        )

    def excluir_vinculo(self, matricula: str, codigo: str) -> int:
        """Apaga o vínculo e, em cascata, só os horários dele (A4).

        Devolve:
            quantos atendimentos foram apagados junto (0 se o vínculo não existia).
        """
        self._exigir_transacao()
        quantos = self._conexao.execute(
            "SELECT COUNT(*) FROM atendimentos WHERE matricula = ? AND codigo = ?",
            (matricula, codigo),
        ).fetchone()[0]
        self._executar_gravacao(
            "DELETE FROM vinculos WHERE matricula = ? AND codigo = ?",
            (matricula, codigo), "vínculo", f"{matricula}–{codigo}",
        )
        return quantos

    def buscar_vinculo(self, matricula: str, codigo: str) -> Vinculo | None:
        """Devolve o vínculo com os seus atendimentos, ou None se não existir."""
        vinculos = self._montar_vinculos(
            "v.matricula = ? AND v.codigo = ?", (matricula, codigo)
        )
        return vinculos[0] if vinculos else None

    def vinculos_do_monitor(self, matricula: str) -> tuple[Vinculo, ...]:
        """Todos os vínculos do monitor, com os atendimentos.

        É o que a checagem de conflito precisa: todos os horários do monitor,
        em todas as disciplinas (R5).
        """
        return self._montar_vinculos("v.matricula = ?", (matricula,))

    def vinculos_da_disciplina(self, codigo: str) -> tuple[Vinculo, ...]:
        """Todos os vínculos da disciplina, com os atendimentos (usado pela F2)."""
        return self._montar_vinculos("v.codigo = ?", (codigo,))

    def _montar_vinculos(self, filtro: str, parametros: tuple) -> tuple[Vinculo, ...]:
        """Monta Vinculo(monitor, disciplina, atendimentos) a partir das tabelas.

        `filtro` é sempre um texto fixo escrito neste arquivo; os valores
        vindos de fora entram só por `parametros` (placeholders ?).
        """
        linhas = self._conexao.execute(
            "SELECT v.matricula, u.nome AS nome_usuario, u.email, "
            "       v.codigo, d.nome AS nome_disciplina "
            "FROM vinculos v "
            "JOIN usuarios u ON u.matricula = v.matricula "
            "JOIN disciplinas d ON d.codigo = v.codigo "
            f"WHERE {filtro} ORDER BY v.codigo, u.nome, v.matricula",
            parametros,
        ).fetchall()
        if not linhas:
            return ()

        # Um único SELECT traz os atendimentos de todos esses vínculos.
        linhas_atendimento = self._conexao.execute(
            f"SELECT {_COLUNAS_ATENDIMENTO} FROM atendimentos a "
            "JOIN vinculos v ON v.matricula = a.matricula AND v.codigo = a.codigo "
            f"WHERE {filtro} ORDER BY a.id",
            parametros,
        ).fetchall()
        por_vinculo: dict[tuple[str, str], list[Atendimento]] = {}
        for linha in linhas_atendimento:
            chave = (linha["matricula"], linha["codigo"])
            por_vinculo.setdefault(chave, []).append(self._atendimento_da_linha(linha))

        vinculos = []
        for linha in linhas:
            monitor = Monitor(linha["matricula"], linha["nome_usuario"], linha["email"])
            disciplina = Disciplina(linha["codigo"], linha["nome_disciplina"])
            atendimentos = por_vinculo.get((linha["matricula"], linha["codigo"]), [])
            vinculos.append(Vinculo(monitor, disciplina, tuple(atendimentos)))
        return tuple(vinculos)

    # ------------------------------------------------------------------
    # Atendimentos
    # ------------------------------------------------------------------

    def inserir_atendimento(self, matricula: str, codigo: str,
                            atendimento: Atendimento) -> Atendimento:
        """Grava um atendimento no vínculo (matricula, codigo).

        Devolve:
            o atendimento como ficou gravado, já com o id dado pela base.
        Lança:
            sqlite3.IntegrityError se o vínculo não existir (chave estrangeira).
        """
        cursor = self._executar_gravacao(
            "INSERT INTO atendimentos (matricula, codigo, dia, inicio, fim, modalidade, "
            "predio, sala, plataforma, link, registrado_em) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (matricula, codigo, *self._colunas_do_atendimento(atendimento)),
            "atendimento", f"{matricula}–{codigo}",
        )
        return self._buscar_atendimento_por_id(cursor.lastrowid)

    def buscar_atendimento(self, id_atendimento: int) -> tuple[Vinculo, Atendimento] | None:
        """Devolve (vínculo, atendimento) do id, ou None se não existir.

        O vínculo vem junto porque é por ele que o cadastro confere a
        titularidade (vinculo.monitor.matricula) e mostra a disciplina.
        """
        linha = self._conexao.execute(
            "SELECT matricula, codigo FROM atendimentos WHERE id = ?", (id_atendimento,)
        ).fetchone()
        if linha is None:
            return None
        vinculo = self.buscar_vinculo(linha["matricula"], linha["codigo"])
        atendimento = next(a for a in vinculo.atendimentos if a.id == id_atendimento)
        return vinculo, atendimento

    def atualizar_atendimento(self, id_atendimento: int, atendimento: Atendimento) -> Atendimento:
        """Troca os dados do atendimento `id_atendimento` pelos de `atendimento` (F1c).

        O vínculo (matrícula e disciplina) e o id não mudam.
        Devolve:
            o atendimento como ficou gravado.
        Lança:
            LookupError se não houver atendimento com esse id.
        """
        cursor = self._executar_gravacao(
            "UPDATE atendimentos SET dia = ?, inicio = ?, fim = ?, modalidade = ?, "
            "predio = ?, sala = ?, plataforma = ?, link = ?, registrado_em = ? "
            "WHERE id = ?",
            (*self._colunas_do_atendimento(atendimento), id_atendimento),
            "atendimento", str(id_atendimento),
        )
        if cursor.rowcount == 0:
            raise LookupError(f"Não há atendimento com id {id_atendimento}.")
        return self._buscar_atendimento_por_id(id_atendimento)

    def excluir_atendimento(self, id_atendimento: int) -> bool:
        """Apaga o atendimento (F1d). Devolve False se o id não existia."""
        cursor = self._executar_gravacao(
            "DELETE FROM atendimentos WHERE id = ?", (id_atendimento,),
            "atendimento", str(id_atendimento),
        )
        return cursor.rowcount == 1

    # ------------------------------------------------------------------
    # Tradução atendimento <-> linha
    # ------------------------------------------------------------------

    def _buscar_atendimento_por_id(self, id_atendimento: int) -> Atendimento:
        """Lê um atendimento que se sabe existir."""
        linha = self._conexao.execute(
            f"SELECT {_COLUNAS_ATENDIMENTO} FROM atendimentos a WHERE a.id = ?",
            (id_atendimento,),
        ).fetchone()
        return self._atendimento_da_linha(linha)

    @staticmethod
    def _colunas_do_atendimento(atendimento: Atendimento) -> tuple:
        """Valores de (dia, inicio, fim, modalidade, predio, sala, plataforma, link, registrado_em).

        A tabela tem colunas diferentes para cada modalidade, então esta
        tradução precisa saber qual é. Ela pergunta ao próprio objeto
        (modalidade(), polimórfico) e não testa a classe.
        """
        modalidade = atendimento.modalidade()
        if modalidade == "presencial":
            local = (atendimento.predio, atendimento.sala, None, None)
        else:
            local = (None, None, atendimento.plataforma, atendimento.link)
        return (atendimento.dia, atendimento.inicio, atendimento.fim, modalidade,
                *local, atendimento.registrado_em.isoformat())

    @staticmethod
    def _atendimento_da_linha(linha: sqlite3.Row) -> Atendimento:
        """Monta o AtendimentoPresencial ou AtendimentoOnline de uma linha.

        O objeto passa pelo construtor normal, então um registro inválido na
        base (editado à mão, por exemplo) gera DadosInvalidos em vez de virar
        um objeto inválido.
        """
        comum = dict(registrado_em=date.fromisoformat(linha["registrado_em"]),
                     id_atendimento=linha["id"])
        if linha["modalidade"] == "presencial":
            return AtendimentoPresencial(linha["dia"], linha["inicio"], linha["fim"],
                                         linha["predio"], linha["sala"], **comum)
        return AtendimentoOnline(linha["dia"], linha["inicio"], linha["fim"],
                                 linha["plataforma"], linha["link"], **comum)
