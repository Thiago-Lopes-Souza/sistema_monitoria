"""Executa todos os cenários pelo menu e salva as saídas.

Uso, de dentro de prototipo_monitoria/:

    python cenarios/rodar_cenarios.py

Para cada cenário, cria uma base nova num diretório temporário (carga
fictícia), roda `python -m monitorias --db <base> < cenarios/<ID>.txt` e salva
a transcrição em cenarios/saidas/<ID>.txt. Cenários com partes numeradas
(<ID>.1.txt, <ID>.2.txt) rodam em sequência na MESMA base: é o caso do teste de
persistência após reinício. No fim, roda os testes e salva a saída em
cenarios/saidas/unittest.txt. A base de demonstração (dados/monitorias.db)
nunca é usada.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

PASTA_CENARIOS = Path(__file__).resolve().parent
RAIZ = PASTA_CENARIOS.parent
PASTA_SAIDAS = PASTA_CENARIOS / "saidas"


def agrupar_cenarios() -> dict[str, list[Path]]:
    """Devolve {nome do cenário: arquivos de entrada, na ordem de execução}."""
    grupos: dict[str, list[Path]] = defaultdict(list)
    for arquivo in sorted(PASTA_CENARIOS.glob("*.txt")):
        nome = arquivo.stem.split(".")[0]   # F1A-06_x.1 -> F1A-06_x
        grupos[nome].append(arquivo)
    return dict(sorted(grupos.items()))


def rodar(comando: list[str], entrada: str | None = None) -> str:
    """Roda um comando a partir de prototipo_monitoria/ e devolve stdout + stderr."""
    resultado = subprocess.run(comando, cwd=RAIZ, input=entrada, capture_output=True,
                               text=True, encoding="utf-8")
    return resultado.stdout + resultado.stderr


def rodar_cenario(nome: str, partes: list[Path]) -> str:
    """Prepara uma base nova e roda as partes do cenário nela, em sequência."""
    with tempfile.TemporaryDirectory() as pasta:
        base = Path(pasta) / "cenario.db"
        rodar([sys.executable, "-m", "monitorias.persistencia.seed_demo", "--caminho", str(base)])
        blocos = []
        for numero, parte in enumerate(partes, start=1):
            saida = rodar([sys.executable, "-m", "monitorias", "--db", str(base)],
                          parte.read_text(encoding="utf-8"))
            saida = saida.replace(str(base), "<base temporária do cenário>")
            if len(partes) > 1:
                saida = f"===== Execução {numero} de {len(partes)} ({parte.name}) =====\n{saida}"
            blocos.append(saida)
    return "\n".join(blocos)


def main() -> None:
    """Roda todos os cenários e os testes, salvando as saídas em cenarios/saidas/."""
    PASTA_SAIDAS.mkdir(exist_ok=True)
    for nome, partes in agrupar_cenarios().items():
        (PASTA_SAIDAS / f"{nome}.txt").write_text(rodar_cenario(nome, partes), encoding="utf-8")
        print(f"ok  {nome}")
    testes = rodar([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"])
    (PASTA_SAIDAS / "unittest.txt").write_text(testes, encoding="utf-8")
    print("ok  unittest:", testes.strip().splitlines()[-1])


if __name__ == "__main__":
    main()
