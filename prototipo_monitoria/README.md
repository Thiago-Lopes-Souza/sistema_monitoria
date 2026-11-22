# Consulta centralizada de monitorias — versão final

Trabalho da disciplina ELE631 — Análise, Projeto e Programação Orientados a Objetos
(UFMG, 2026/2, turma TAPO, Profa. Luiza Bernardes Real). Grupo: Felipe de Oliveira Mafra,
Gabriel Augusto Maia Lara, Luiz Filipe Fonseca Ballstaedt e Thiago Lopes Rodrigues Souza.

Sistema de terminal para o aluno saber se uma disciplina de Engenharia de Sistemas tem
monitoria, com quem, quando e onde. Os dados ficam numa base SQLite.

| ID | Funcionalidade | Quem usa |
|---|---|---|
| F2 | Consultar monitorias de uma disciplina, com filtro opcional por modalidade e por dia | Qualquer pessoa, sem login |
| S1 | Entrar com matrícula e senha e sair da sessão | Monitor e administrador |
| F1a–F1d | Cadastrar, ver, alterar (dia e horário) e remover os próprios horários | Monitor |
| A1–A4 | Cadastrar disciplina, cadastrar monitor, vincular e desvincular monitor | Administrador |

## Requisitos

- **Python 3.10 ou mais novo** (testado com Python 3.13.0).
- **Nenhuma biblioteca externa:** só a biblioteca padrão (`sqlite3`, `hashlib`, `getpass`
  etc.). Não há nada para instalar nem ambiente virtual para criar.

No Windows, o comando pode ser `python` ou `py`; no macOS/Linux, `python3`.
Os exemplos usam `python`. **Todos os comandos são rodados de dentro desta pasta**, a que
contém este README.

## 1. Preparar a base de dados (uma vez)

```
python -m monitorias.persistencia.seed_demo
```

Cria `dados/monitorias.db` com os dados fictícios abaixo. Pode rodar de novo sem duplicar
nada: se a base já tem dados, a carga não faz nada.

Para **apagar e recriar** a base do zero, voltando aos dados iniciais:

```
python -m monitorias.persistencia.seed_demo --recriar
```

Também dá para simplesmente apagar o arquivo `dados/monitorias.db` e rodar a carga de novo.

## 2. Iniciar o sistema

```
python -m monitorias
```

Se a base não existir ou estiver vazia, o programa não cria dados: mostra o comando do
passo 1 e sai. Para usar outro arquivo de base (por exemplo, uma cópia para testes):
`python -m monitorias --db outro.db`.

Menu inicial: `1` consultar monitorias (sem login) · `2` entrar como monitor ou administrador ·
`3` listar disciplinas · `0` sair. Depois do login, o menu mostra só as opções do perfil e
"Sair da sessão". O dia da semana é escolhido por número (1 = segunda … 6 = sábado) e os
horários são digitados como `hh:mm`. Entradas inválidas geram uma mensagem explicativa, e
nenhum dado é alterado.

**As alterações ficam salvas** na base e continuam lá na próxima execução.

## 3. Rodar os testes

```
python -m unittest discover -s tests -v
```

Os testes não usam a base de demonstração: cada um cria a sua, em memória ou num arquivo
temporário.

## 4. Rodar os cenários de verificação (opcional)

```
python cenarios/rodar_cenarios.py
```

Roda cada cenário de `cenarios/` numa base nova e temporária e grava as transcrições em
`cenarios/saidas/`. Os resultados esperados estão em `cenarios/ESPERADO.md`. Para rodar um
cenário à mão numa base de sua escolha:

```
python -m monitorias --db outro.db < cenarios/F1A-01_cadastro_valido.txt
```

No PowerShell: `Get-Content cenarios\F1A-01_cadastro_valido.txt | python -m monitorias --db outro.db`.

## Dados de demonstração — todos FICTÍCIOS

Nomes, matrículas, e-mails, links e **senhas** existem só para a demonstração.

| Perfil | Matrícula | Nome | Senha |
|---|---|---|---|
| Administrador | 2026900001 | Admin Fictício | `admin123` |
| Monitor | 2026000001 | Ana Fictícia | `ana123` |
| Monitor | 2026000002 | Caio Exemplo | `caio123` |
| Monitor | 2026000003 | Duda Teste | `duda123` |

| Disciplina | Monitores e horários iniciais |
|---|---|
| DCC203 Programação e Desenvolvimento de Software I | Ana: terça 10:00–12:00, presencial, CAD 3 sala 204 · Caio: vinculado, sem horário |
| MAT001 Cálculo Diferencial e Integral I | Caio: terça 14:00–16:00, presencial, ICEx sala 1010 · quinta 19:00–20:00, online, Google Meet |
| MAT002 Geometria Analítica e Álgebra Linear | Ana: quarta 10:00–12:00, presencial, ICEx sala 2033 |
| FIS069 Física III | Duda: vinculada, sem horário |
| ELT001 Circuitos Elétricos I | sem monitor |

`DCC999` tem formato válido, mas fica fora do catálogo de propósito (rejeição "fora do escopo
do sistema em 2026/2").

**O que é simulado:** a lista de monitores e vínculos que, num uso real, viria dos
departamentos. Aqui ela vem da carga fictícia e das operações do administrador (A1–A4). Não
há integração com sistemas da UFMG.

## Estrutura

```
monitorias/
├── __main__.py        # ponto de entrada: abre a base e chama o menu
├── menu.py            # terminal: único lugar com print/input
├── dominio/           # regras; não imprime, não lê, não tem SQL
│   ├── cadastro.py    # CadastroMonitorias: única porta de escrita
│   ├── usuario.py     # Usuario (abstrata) → Aluno, UsuarioCadastrado → Monitor, Administrador
│   ├── atendimento.py # Atendimento (abstrata) → AtendimentoPresencial, AtendimentoOnline
│   ├── vinculo.py, disciplina.py, monitor.py, consulta.py, horario.py, senha.py, excecoes.py
└── persistencia/      # SQLite: conexao.py, repositorio.py, schema.sql, seed_demo.py
tests/                 # unittest (um arquivo por funcionalidade ou camada)
cenarios/              # entradas dos cenários, ESPERADO.md e rodar_cenarios.py
```
