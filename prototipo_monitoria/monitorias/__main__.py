"""Ponto de entrada: python -m monitorias [--db caminho].

Único lugar fora do domínio que monta a conexão e o repositório, para
entregá-los ao CadastroMonitorias. Não cria dados: se a base não existir ou
estiver vazia, mostra o comando que a prepara e sai.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .dominio.cadastro import CadastroMonitorias
from .menu import executar
from .persistencia.conexao import CAMINHO_PADRAO, abrir_base
from .persistencia.repositorio import RepositorioMonitorias

COMANDO_PREPARAR = "python -m monitorias.persistencia.seed_demo"


def iniciar(argumentos: list[str] | None = None) -> int:
    """Abre a base, monta o cadastro e roda o menu.

    Recebe:
        argumentos: linha de comando (None = sys.argv). --db escolhe outro
            arquivo de base, por exemplo uma cópia para rodar os cenários.
    Devolve:
        0 se o menu rodou; 1 se a base não existe ou está vazia.
    """
    leitor = argparse.ArgumentParser(prog="python -m monitorias",
                                     description="Consulta centralizada de monitorias.")
    leitor.add_argument("--db", type=Path, default=CAMINHO_PADRAO,
                        help="arquivo da base de dados (padrão: dados/monitorias.db)")
    caminho = leitor.parse_args(argumentos).db

    preparar = COMANDO_PREPARAR + ("" if caminho == CAMINHO_PADRAO else f" --caminho {caminho}")
    if not caminho.exists():
        print(f"A base de dados {caminho} não existe.\nPrepare-a com: {preparar}")
        return 1

    conexao = abrir_base(caminho)
    try:
        repositorio = RepositorioMonitorias(conexao)
        if repositorio.esta_vazia():
            print(f"A base de dados {caminho} está vazia.\nPrepare-a com: {preparar}")
            return 1
        print(f"Base de dados: {caminho}")
        executar(CadastroMonitorias(repositorio))
        return 0
    finally:
        conexao.close()


if __name__ == "__main__":
    sys.exit(iniciar())
