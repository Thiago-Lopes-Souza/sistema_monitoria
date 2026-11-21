# Protótipo — Consulta centralizada de monitorias

Trabalho da disciplina ELE631 — Análise, Projeto e Programação Orientados a Objetos
(UFMG, 2026/2, turma TAPO). Grupo: Felipe de Oliveira Mafra, Gabriel Augusto Maia Lara,
Luiz Filipe Fonseca Ballstaedt e Thiago Lopes Rodrigues Souza.

O protótipo implementa duas funcionalidades ligadas:

- **F1 — Cadastrar horário de atendimento** (monitor vinculado à disciplina);
- **F2 — Consultar monitorias de uma disciplina**, com filtro opcional por modalidade (aluno).

O horário aceito na F1 aparece na consulta seguinte da F2; o recusado não aparece.

## Requisitos

- **Python 3.10 ou mais novo** (testado com Python 3.13). O código usa a sintaxe `str | None`.
- Só a biblioteca padrão: **não há nada para instalar** e não é preciso criar ambiente virtual.

No Windows, o comando pode ser `python` ou `py`; no macOS/Linux, `python3`.
Os exemplos abaixo usam `python`.

## Como iniciar

Todos os comandos são rodados **de dentro desta pasta** (a que contém este README):

```
python -m monitorias
```

Abre um menu no terminal:

```
1 - Consultar monitorias de uma disciplina (aluno)      -> F2
2 - Cadastrar horário de atendimento (monitor)          -> F1
3 - Listar disciplinas do sistema
0 - Sair
```

No cadastro, o dia da semana é escolhido por número (1 = segunda ... 6 = sábado) e os
horários são digitados como `hh:mm` (horário local). Entradas inválidas geram uma mensagem
explicativa e nenhum dado é alterado.

## Como rodar os testes

```
python -m unittest discover -s tests -v
```

## Dados de demonstração (todos fictícios)

Não há preparação manual: ao iniciar, o programa carrega os dados de
`monitorias/dados_demo.py`. **Nomes, matrículas, e-mails e links são fictícios.** Eles simulam
a lista de vínculos que o departamento enviaria ao sistema.

| Disciplina | Monitor (matrícula) | Horários já carregados |
|---|---|---|
| DCC203 Programação e Desenvolvimento de Software I | Ana Fictícia (2026000001) | terça 10:00–12:00, presencial, CAD 3 sala 204 |
| DCC203 (mesma) | Caio Exemplo (2026000002) | nenhum nesta disciplina |
| MAT001 Cálculo Diferencial e Integral I | Caio Exemplo (2026000002) | terça 14:00–16:00, presencial, ICEx sala 1010 · quinta 19:00–20:00, online, Google Meet |
| FIS069 Física III | Duda Teste (2026000003) | nenhum |
| ELT001 Circuitos Elétricos I | nenhum | nenhum |

`DCC999` tem formato válido, mas fica fora do catálogo de propósito (rejeição de escopo).

**Os dados ficam só em memória:** tudo o que for cadastrado se perde ao sair do programa.
Os testes não usam esses dados: cada classe de teste monta os seus no `setUp`.

## Cenários sem digitar

A pasta `cenarios/` tem as entradas dos cenários planejados, uma resposta por linha:

| Arquivo | Cenário |
|---|---|
| `c1_valido.txt` | C1 — cadastro válido (F1) seguido de consulta (F2) |
| `c2_conflito.txt` | C2 — rejeição por conflito de horário, com consultas antes e depois |
| `c3_limite_sequencia.txt` | C3 — horário que só encosta (aceito), consulta vazia por modalidade e disciplina sem monitoria |
| `extra_entradas_invalidas.txt` | Entradas inválidas, incluindo falhas de conversão |

Para rodar um deles:

```
python -m monitorias < cenarios/c1_valido.txt
```

No PowerShell:

```
Get-Content cenarios\c1_valido.txt | python -m monitorias
```

## Estrutura

```
monitorias/
├── __main__.py        # ponto de entrada (python -m monitorias)
├── menu.py            # terminal: único lugar com print/input
├── dados_demo.py      # dados fictícios de demonstração
└── dominio/           # regras e classes; não imprime nem lê nada
    ├── excecoes.py    # hierarquia de exceções (base: ErroMonitorias)
    ├── horario.py     # validação de dia, hh:mm e código de disciplina
    ├── atendimento.py # Atendimento (abstrata), AtendimentoPresencial, AtendimentoOnline
    ├── disciplina.py, monitor.py, vinculo.py
    ├── consulta.py    # resultado da consulta (F2)
    └── cadastro.py    # CadastroMonitorias: ponto de entrada do domínio
tests/                 # unittest das funcionalidades e classes
cenarios/              # entradas dos cenários C1–C3 e do roteiro de entradas inválidas
```
