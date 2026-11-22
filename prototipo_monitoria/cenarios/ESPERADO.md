# Cenários — resultados esperados (escritos antes da execução)

Cada cenário roda numa base **nova**, criada pela carga fictícia
(`python -m monitorias.persistencia.seed_demo`), com
`python -m monitorias --db <base temporária> < cenarios/<ID>.txt`.
O roteiro `cenarios/rodar_cenarios.py` faz isso para todos e salva as saídas em
`cenarios/saidas/<ID>.txt`. Cada `.txt` tem uma resposta por linha (linha vazia = Enter)
e termina saindo do programa.

## Estado inicial (carga fictícia, igual para todos os cenários)

| Perfil | Matrícula | Senha | Vínculos e horários (ID do atendimento) |
|---|---|---|---|
| Administrador | 2026900001 | admin123 | — |
| Monitora Ana Fictícia | 2026000001 | ana123 | DCC203: terça 10:00–12:00, presencial, CAD 3 sala 204 (ID 1) · MAT002: quarta 10:00–12:00, presencial, ICEx sala 2033 (ID 2) |
| Monitor Caio Exemplo | 2026000002 | caio123 | DCC203: sem horário · MAT001: terça 14:00–16:00, presencial, ICEx sala 1010 (ID 3) e quinta 19:00–20:00, online, Google Meet (ID 4) |
| Monitora Duda Teste | 2026000003 | duda123 | FIS069: sem horário |

Disciplinas: DCC203, MAT001, MAT002, FIS069 e ELT001 (ELT001 sem vínculo). DCC999 tem formato
válido, mas fica fora do catálogo. Horários da carga: registrados em 20/10/2026.

Menu inicial: `1` consultar (F2) · `2` entrar (S1) · `3` listar disciplinas · `0` sair.
Sessão de monitor: `1` F2 · `2` F1a · `3` F1b · `4` F1c · `5` F1d · `0` sair da sessão.
Sessão de administrador: `1` F2 · `2` A1 · `3` A2 · `4` A3 · `5` A4 · `0` sair da sessão.
Dia por número: 1 segunda … 6 sábado.

Toda rejeição do domínio deve mostrar "Não foi possível concluir: …" e "Nenhum dado foi alterado.".

---

## S1 — Entrar e sair

| ID | Regra e entrada | Resultado e estado final esperados |
|---|---|---|
| S1-01 | Ana entra com `2026000001`/`ana123` e sai da sessão | "Sessão iniciada. Bem-vindo(a), Ana Fictícia."; submenu com F2, F1a–F1d e "Sair da sessão"; "Sessão encerrada."; base inalterada |
| S1-02 | Ana com senha errada | "Matrícula ou senha inválida."; nenhuma sessão aberta; volta ao menu inicial; base inalterada; a senha não aparece na transcrição (só `********`) |
| S1-03 | Matrícula inexistente `2026999999` | A **mesma** mensagem do S1-02; nenhuma sessão |
| S1-04 | Admin entra, sai da sessão e faz uma F2 sem login | Submenu com F2 e A1–A4 (sem F1); depois do logout, a consulta de DCC203 funciona no menu inicial |

## F1a — Cadastrar horário

| ID | Regra e entrada | Resultado e estado final esperados |
|---|---|---|
| F1A-01 | (C1 do protótipo) Ana: DCC203, presencial, CAD 3 sala 204, quinta 14:00–16:00; depois F1b e F2 de DCC203 | "Horário cadastrado (ID 5)"; F1b com 3 horários; F2: Ana com terça 10:00–12:00 e quinta 14:00–16:00 (data de hoje), Caio "(sem horários cadastrados nesta disciplina)" |
| F1A-02 | (C2 do protótipo) F2 MAT001; Caio tenta DCC203 terça 15:00–17:00 | "Conflito de horário: você já atende terça 14:00–16:00 em MAT001."; F1b do Caio igual (IDs 3 e 4); MAT001 igual antes e depois; DCC203 sem horário do Caio |
| F1A-03 | (C3 do protótipo) Caio: DCC203 terça 16:00–18:00, sala 205; F2 DCC203 online; F2 DCC203; F2 ELT001 | Aceito (encostar não é conflito); online: "Não há horário cadastrado com esse filtro" + contatos de Ana e Caio; todas: Caio com terça 16:00–18:00; ELT001: "Nenhuma monitoria cadastrada no sistema" + aviso |
| F1A-04 | Duda (vinculada só a FIS069) tenta DCC203 | "O monitor de matrícula 2026000003 não é monitor da disciplina DCC203."; F1b da Duda vazia |
| F1A-05 | Ana: DCC999; `dcc 20`; link `http://inseguro`; dia `7` (repete) e 16:00→14:00; início `8h`; prédio vazio | Seis rejeições com mensagem própria (fora do escopo, código inválido, link, início antes do fim, horário inválido, prédio e sala obrigatórios); dia `7` repete só a pergunta; F1b da Ana igual à inicial (IDs 1 e 2) |
| F1A-06 | Persistência após reinício. Execução 1: Ana cadastra DCC203 online sábado 09:00–10:00. Execução 2, **mesma base**: F2 DCC203 filtrada por sábado | Execução 1: "Horário cadastrado (ID 5)". Execução 2: o horário de sábado aparece |

## F1b — Ver meus horários

| ID | Regra e entrada | Resultado e estado final esperados |
|---|---|---|
| F1B-01 | Caio pede os próprios horários | ID 3 MAT001 terça 14:00–16:00 presencial e ID 4 MAT001 quinta 19:00–20:00 online, com disciplina e data; nada muda |
| F1B-02 | Duda (sem horários) | "Você ainda não tem horários cadastrados."; nada muda |

## F1c — Alterar dia e horário

| ID | Regra e entrada | Resultado e estado final esperados |
|---|---|---|
| F1C-01 | Caio altera o ID 3 de terça 14:00–16:00 para quarta 14:00–16:00 | "Horário alterado (ID 3)": quarta, mesmo local e modalidade, data de hoje; F2 MAT001 mostra quarta 14:00–16:00 e quinta 19:00–20:00 |
| F1C-02 | Ana tenta alterar o ID 3, que é do Caio | "O atendimento pertence a outro monitor."; F2 MAT001 com terça 14:00–16:00 intacta |
| F1C-03 | Ana altera o ID 2 (MAT002) para terça 11:00–13:00, que cruza com terça 10:00–12:00 em DCC203 | "Conflito de horário: você já atende terça 10:00–12:00 em DCC203."; F1b igual (ID 2 continua quarta 10:00–12:00) |
| F1C-04 | Caio altera o ID 3 para terça 15:00–17:00 (só cruza com ele mesmo) | Aceito: o próprio atendimento não conta como conflito; ID 3 passa a terça 15:00–17:00 |
| F1C-05 | Caio: ID `abc` (repete), ID 99; depois ID 3 com 17:00→15:00 | `abc`: "não é um número válido" e repete; 99: "Atendimento de ID 99 não encontrado."; 17→15: "O início (17:00) precisa ser antes do fim (15:00)."; F1b igual à inicial |

## F1d — Remover atendimento

| ID | Regra e entrada | Resultado e estado final esperados |
|---|---|---|
| F1D-01 | Ana remove o ID 1 (DCC203 terça) | "Atendimento de ID 1 removido."; F1b só com o ID 2; F2 DCC203: "Há monitor cadastrado, mas os horários ainda não foram informados." com Ana e Caio |
| F1D-02 | Ana tenta remover o ID 3 (do Caio) | "O atendimento pertence a outro monitor."; F1b da Ana igual (IDs 1 e 2) e F1b do Caio igual (IDs 3 e 4) |
| F1D-03 | Ana remove o ID 99 | "Atendimento de ID 99 não encontrado."; F1b igual |

## F2 — Consultar monitorias

| ID | Regra e entrada | Resultado e estado final esperados |
|---|---|---|
| F2-01 | DCC203, sem filtros | `COM_HORARIOS`: Ana com terça 10:00–12:00; Caio "(sem horários cadastrados nesta disciplina)" |
| F2-02 | MAT001, online | Só Caio quinta 19:00–20:00 online |
| F2-03 | MAT001, terça | Só Caio terça 14:00–16:00 presencial |
| F2-04 | MAT001, sexta | Resposta válida: "Não há horário cadastrado com esse filtro" + contato do Caio |
| F2-05 | FIS069 | "Há monitor cadastrado, mas os horários ainda não foram informados." + contato da Duda |
| F2-06 | ELT001 | "Nenhuma monitoria cadastrada no sistema para esta disciplina." + aviso de que isso não garante que não exista |
| F2-07 | DCC999; `dcc 20`; `mat001` com modalidade `x` (repete) e dia `9` (repete) → terça | DCC999: "fora do escopo do sistema em 2026/2."; `dcc 20`: código inválido; `mat001` aceito em minúsculas, mostra terça 14:00–16:00; nada muda |

## A1 — Cadastrar disciplina

| ID | Regra e entrada | Resultado e estado final esperados |
|---|---|---|
| A1-01 | Admin cadastra DCC205 "Estruturas de Dados"; lista; F2 DCC205 | "Disciplina cadastrada"; DCC205 na lista; F2: nenhuma monitoria cadastrada |
| A1-02 | Admin: DCC203 (já existe); `DC20`; DCC206 sem nome | Três rejeições (duplicada, código inválido, nome obrigatório); lista igual à inicial (5 disciplinas) |
| A1-03 | Monitora Ana entra | O submenu não oferece A1–A4 (a checagem no cadastro está no teste `test_a1_04_monitor_sem_permissao`) |

## A2 — Cadastrar monitor

| ID | Regra e entrada | Resultado e estado final esperados |
|---|---|---|
| A2-01 | Admin cadastra Eva (2026000004, eva.exemplo@ufmg.br, senha eva123); Eva entra e vê seus horários | "Monitor cadastrado … Ainda sem vínculo"; login da Eva aceito; F1b vazia |
| A2-02 | Admin: matrícula 2026000001 (já existe); e-mail gmail; senha vazia; depois tenta entrar como 2026000005 | Três rejeições; o login de 2026000005 falha (o monitor não foi criado) |

## A3 — Vincular monitor a disciplina

| ID | Regra e entrada | Resultado e estado final esperados |
|---|---|---|
| A3-01 | Admin vincula Duda a DCC203; Duda cadastra DCC203 sexta 08:00–10:00; F2 DCC203 | "Vínculo criado"; cadastro aceito; F2 mostra Duda com sexta 08:00–10:00 |
| A3-02 | Admin: Ana–DCC203 (já existe); matrícula 2026999999; disciplina DCC999 | Três rejeições; F2 DCC203 igual à inicial |

## A4 — Desvincular monitor

| ID | Regra e entrada | Resultado e estado final esperados |
|---|---|---|
| A4-01 | Admin desvincula Ana de MAT002 (ela atende em DCC203 e MAT002) | "Horários apagados junto com ele: 1"; F2 MAT002: nenhuma monitoria cadastrada; F2 DCC203: Ana com terça 10:00–12:00 preservada |
| A4-02 | Admin desvincula Duda de DCC203 (vínculo inexistente) | Rejeição; F2 FIS069 igual (Duda continua lá) |
| A4-03 | Admin desvincula Caio de DCC203 (0 horários); Caio tenta cadastrar em DCC203 | "Horários apagados junto com ele: 0"; o cadastro é recusado por falta de vínculo; F1b do Caio com IDs 3 e 4 intactos |
