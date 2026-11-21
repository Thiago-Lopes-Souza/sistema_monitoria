"""Abertura da conexão com o SQLite e criação do esquema.

Só esta camada sabe onde fica o arquivo da base. O resto do sistema recebe
uma conexão pronta (o repositório) ou um repositório pronto (o cadastro).
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

#: Base de uso: prototipo_monitoria/dados/monitorias.db. O caminho é calculado a
#: partir deste arquivo, então funciona de qualquer pasta. Não vai para o Git.
CAMINHO_PADRAO = Path(__file__).resolve().parents[2] / "dados" / "monitorias.db"

#: Arquivo com o CREATE TABLE de todas as tabelas.
ARQUIVO_ESQUEMA = Path(__file__).with_name("schema.sql")

#: Valor especial do sqlite3: base só em memória, que some ao fechar a conexão.
#: Usado pelos testes, para nunca tocar na base de demonstração.
EM_MEMORIA = ":memory:"


def abrir_conexao(caminho: str | Path = CAMINHO_PADRAO) -> sqlite3.Connection:
    """Abre (ou cria) a base e configura a conexão.

    Recebe:
        caminho: arquivo .db, ou EM_MEMORIA para uma base temporária.
    Devolve:
        conexão com chaves estrangeiras ligadas e linhas acessíveis pelo nome
        da coluna (linha["matricula"]).
    Lança:
        RuntimeError se o SQLite não aceitar ligar as chaves estrangeiras.
    """
    if str(caminho) != EM_MEMORIA:
        Path(caminho).parent.mkdir(parents=True, exist_ok=True)
    conexao = sqlite3.connect(caminho)
    conexao.row_factory = sqlite3.Row
    # Precisa ser ligado em TODA conexão: o SQLite não guarda isso no arquivo.
    # Sem ele, o ON DELETE CASCADE do A4 e as REFERENCES não funcionam.
    conexao.execute("PRAGMA foreign_keys = ON")
    if conexao.execute("PRAGMA foreign_keys").fetchone()[0] != 1:
        conexao.close()
        raise RuntimeError("Este SQLite não suporta chaves estrangeiras.")
    return conexao


def criar_esquema(conexao: sqlite3.Connection) -> None:
    """Cria as tabelas que ainda não existem. Não apaga nem altera dados."""
    conexao.executescript(ARQUIVO_ESQUEMA.read_text(encoding="utf-8"))


def abrir_base(caminho: str | Path = CAMINHO_PADRAO) -> sqlite3.Connection:
    """Abre a conexão e garante o esquema. É o que o programa e os testes usam."""
    conexao = abrir_conexao(caminho)
    criar_esquema(conexao)
    return conexao
