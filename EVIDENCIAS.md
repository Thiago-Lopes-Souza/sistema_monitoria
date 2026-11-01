# Evidências — cenários, testes e conferência do ZIP

Execução em **01/11/2026**, macOS, Python 3.13, com o código integrado das frentes A, B, C e D
(branch `frente-D`, a partir de `integracao` = A + B + C). As saídas completas estão em
`prototipo_monitoria/cenarios/saidas/`. Cada cenário começa com o programa recém-aberto
(só os dados fictícios).

Comando usado em cada cenário (de dentro de `prototipo_monitoria/`):
`python -m monitorias < cenarios/<arquivo>.txt`

---

## C1 — Válido, F1 + F2

- **Preparação:** dados fictícios de `criar_cadastro_demo()`. Ana (2026000001) tem terça 10:00–12:00 em DCC203; Caio (2026000002) é vinculado a DCC203, sem horário nela.
- **Entradas** (`c1_valido.txt`): opção 2 → `2026000001`, `DCC203`, presencial (1), `CAD 3`, `204`, quinta (4), `14:00`, `16:00`. Depois opção 1 → `DCC203`, todas (Enter). Opção 0.
- **Esperado:** "Horário cadastrado". Na consulta, Ana com dois horários, terça 10:00–12:00 antes de quinta 14:00–16:00 (este com a data da execução). Caio "sem horários cadastrados".
- **Observado:**
  ```
  Horário cadastrado: quinta 14:00–16:00 | presencial | CAD 3, sala 204 | registrado em 01/11/2026

  DCC203 — Programação e Desenvolvimento de Software I (modalidade: todas)
    Monitor(a): Ana Fictícia <ana.ficticia@ufmg.br>
      - terça 10:00–12:00 | presencial | CAD 3, sala 204 | registrado em 20/10/2026
      - quinta 14:00–16:00 | presencial | CAD 3, sala 204 | registrado em 01/11/2026
  ```
- **Conclusão: atendido em parte.** O cadastro e a ordem dos horários da Ana batem com o esperado. **Diverge:** o Caio não aparece na consulta. `consultar_monitorias` (frente C), na situação `COM_HORARIOS`, só inclui em `itens` os monitores que têm horário. Monitor vinculado sem horário fica de fora. O menu não tem como mostrá-lo sem acessar dados internos. **Pendente de decisão do grupo:** mudar o domínio para incluir esses monitores com `atendimentos=()`, ou ajustar o resultado esperado do C1.

## C2 — Rejeição, F1 (consultas antes e depois)

- **Preparação:** dados fictícios. Caio atende terça 14:00–16:00 em MAT001.
- **Entradas** (`c2_conflito.txt`): opção 1 → `MAT001`, todas. Opção 2 → `2026000002`, `DCC203`, presencial, `CAD 3`, `204`, terça (2), `15:00`, `17:00`. Opção 1 → `MAT001`, todas. Opção 1 → `DCC203`, todas. Opção 0.
- **Esperado:** "Conflito de horário: você já atende terça 14:00–16:00 em MAT001" + "Nenhum dado foi alterado". MAT001 igual à consulta anterior. DCC203 sem horário novo para o Caio.
- **Observado:**
  ```
  MAT001 — Cálculo Diferencial e Integral I (modalidade: todas)
    Monitor(a): Caio Exemplo <caio.exemplo@ufmg.br>
      - terça 14:00–16:00 | presencial | ICEx, sala 1010 | registrado em 20/10/2026
      - quinta 19:00–20:00 | online | Google Meet: https://meet.exemplo/mat001 | registrado em 20/10/2026

  Não foi possível concluir: Conflito de horário: você já atende terça 14:00–16:00 em MAT001.
  Nenhum dado foi alterado.

  MAT001 — Cálculo Diferencial e Integral I (modalidade: todas)
    Monitor(a): Caio Exemplo <caio.exemplo@ufmg.br>
      - terça 14:00–16:00 | presencial | ICEx, sala 1010 | registrado em 20/10/2026
      - quinta 19:00–20:00 | online | Google Meet: https://meet.exemplo/mat001 | registrado em 20/10/2026

  DCC203 — Programação e Desenvolvimento de Software I (modalidade: todas)
    Monitor(a): Ana Fictícia <ana.ficticia@ufmg.br>
      - terça 10:00–12:00 | presencial | CAD 3, sala 204 | registrado em 20/10/2026
  ```
- **Conclusão: aprovado.** A mensagem cita o horário e a disciplina do conflito. MAT001 ficou idêntica antes e depois, e DCC203 não ganhou horário do Caio.

## C3 — Limite e sequência, F1 + F2

- **Preparação:** dados fictícios. Caio atende terça 14:00–16:00 em MAT001.
- **Entradas** (`c3_limite_sequencia.txt`): opção 2 → `2026000002`, `DCC203`, presencial, `CAD 3`, `205`, terça (2), `16:00`, `18:00`. Opção 1 → `DCC203`, online (2). Opção 1 → `DCC203`, todas. Opção 1 → `ELT001`, todas. Opção 0.
- **Esperado:** cadastro aceito (encostar não é conflito). DCC203 online: "Não há horário cadastrado nessa modalidade". DCC203 todas: Caio com terça 16:00–18:00. ELT001: "Nenhuma monitoria cadastrada no sistema", resposta válida, sem alteração.
- **Observado:**
  ```
  Horário cadastrado: terça 16:00–18:00 | presencial | CAD 3, sala 205 | registrado em 01/11/2026

  DCC203 — Programação e Desenvolvimento de Software I (modalidade: online)
    Não há horário cadastrado nessa modalidade.
    Contato: Ana Fictícia <ana.ficticia@ufmg.br>
    Contato: Caio Exemplo <caio.exemplo@ufmg.br>

  DCC203 — Programação e Desenvolvimento de Software I (modalidade: todas)
    Monitor(a): Ana Fictícia <ana.ficticia@ufmg.br>
      - terça 10:00–12:00 | presencial | CAD 3, sala 204 | registrado em 20/10/2026
    Monitor(a): Caio Exemplo <caio.exemplo@ufmg.br>
      - terça 16:00–18:00 | presencial | CAD 3, sala 205 | registrado em 01/11/2026

  ELT001 — Circuitos Elétricos I (modalidade: todas)
    Nenhuma monitoria cadastrada no sistema para esta disciplina.
    Atenção: a ausência no sistema não garante que não exista monitoria; confirme com o departamento que oferta a disciplina.
  ```
- **Conclusão: aprovado.** As consultas vazias (DCC203 online, ELT001) são respostas válidas pelo contrato, não rejeições.

## Roteiro extra — entradas inválidas

Arquivo `extra_entradas_invalidas.txt`. Saída completa em `cenarios/saidas/extra_entradas_invalidas.txt`.

| Entrada | Mensagem observada | Resultado |
|---|---|---|
| opção `abc` | `'abc' não é um número válido. Digite um número de 0 a 3.` (repete a pergunta) | ok |
| opção `9` | `Opção 9 não existe. Digite um número de 0 a 3.` | ok |
| código `dcc 20` | `Código de disciplina inválido: 'dcc 20'. Use três letras e três números, ex.: DCC203.` | ok |
| `DCC999` | `A disciplina DCC999 está fora do escopo do Sistema em 2026/2 !` | ok |
| `fis069` (minúsculas) | consulta funciona: FIS069 com "Há monitor cadastrado, mas os horários ainda não foram informados." + e-mail da Duda | ok |
| modalidade `x` | `'x' não é um número válido. Digite um número de 1 a 2.` (repete) | ok |
| dia `7` | `Opção 7 não existe. Digite um número de 1 a 6.` (repete) | ok |
| 16:00 → 14:00 | `O início (16:00) precisa ser antes do fim (14:00).` | ok |
| matrícula `2026999999` | `A matricula 2026999999 não pertence a nenhum monitor cadastrado no Sistema!` | ok |
| Duda (2026000003) em DCC203 | `O monitor de matricula 2026000003 não é monitor da disciplina DCC203.` | ok |
| link `http://inseguro` | `Link inválido: 'http://inseguro'. Ele precisa começar com https://.` | ok |
| início `8h` | `Horário inválido: '8h'. Use o formato hh:mm, ex.: 14:30.` | ok |

Toda rejeição de domínio termina com "Nenhum dado foi alterado.". **No fim, DCC203 continua só com terça 10:00–12:00 da Ana**: estado preservado. Fim da entrada sem `0` (Ctrl+D/Ctrl+Z) também encerra sem traceback.

## Testes automáticos

`python -m unittest discover -s tests -v`: **71 testes, todos OK.** Saída completa em
`cenarios/saidas/testes.txt`.

```
----------------------------------------------------------------------
Ran 71 tests in 0.002s

OK
```

## Conferência do ZIP

`prototipo-monitorias.zip` (27 arquivos: código, testes, cenários e README; sem `__pycache__`,
`.git`, venv nem `saidas/`). Foi extraído numa pasta limpa e só o README foi seguido:

- `python -m monitorias` iniciou;
- o cenário C1 rodou de ponta a ponta (F1 cadastrou, F2 mostrou o horário novo);
- `python -m unittest discover -s tests -v` rodou os 71 testes: OK.

## Trechos de código para captura (frente D)

- `monitorias/menu.py`, linhas 58–82: `ler_opcao()`, com o `try/except ValueError` da falha de conversão (linhas 73–78).
- `monitorias/menu.py`, linhas 226–258: `executar()`, com o ponto único que captura `ConflitoDeHorario`/`ErroMonitorias` (linhas 248–255) e `EOFError`/`KeyboardInterrupt` (linha 256).

## Pontos para levar ao grupo

1. **C1 / frente C:** o monitor vinculado sem horário (Caio em DCC203) não aparece em `COM_HORARIOS`. Veja o C1 acima.
2. **Frente C:** em `SEM_HORARIOS_NA_MODALIDADE` os `itens` vêm vazios. Para mostrar os e-mails pedidos na seção 7, o menu faz uma segunda consulta, só de leitura, sem filtro. Se o domínio passar a incluir os monitores nessa situação, essa chamada extra sai do menu.
3. **Frente A, texto de mensagens:**
   - `DisciplinaForaDoEscopo`: "fora do escopo do Sistema em 2026/2 !" tem espaço antes do "!" e "Sistema" com maiúscula.
   - `MatriculaNaoCadastrada` e `VinculoInexistente`: "matricula" está sem acento.
4. **Estrutura:** a pasta do projeto no repositório é `prototipo_monitoria/`. O CLAUDE.md fala em `prototipo-monitorias/`. Os comandos funcionam igual.
