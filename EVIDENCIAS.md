# Evidências da versão final — verificação

Execução em **22/11/2026**, macOS, **Python 3.13.0**, branch `integracao-final`, que junta as
frentes A, B e C e a frente D. A versão será identificada pela tag `v1.0-final`, que ainda
**não foi criada**. Os resultados esperados foram escritos antes da execução em
`prototipo_monitoria/cenarios/ESPERADO.md` (commit `5b0c0ef`).

**Como reproduzir**, de dentro de `prototipo_monitoria/`:

```
python cenarios/rodar_cenarios.py          # roda os 37 cenários e os testes
python -m unittest discover -s tests -v    # só os testes
```

`rodar_cenarios.py` cria uma base **nova** para cada cenário: um arquivo temporário com a
carga fictícia de `seed_demo.py`. Depois roda `python -m monitorias --db <base> <
cenarios/<ID>.txt` e salva a transcrição em `cenarios/saidas/<ID>.txt`. A base de
demonstração `dados/monitorias.db` não é usada. Os testes `unittest` usam bases
próprias, em `:memory:` ou em arquivo temporário, montadas no `setUp`.

**Coluna Evidência:** o arquivo da saída real do terminal, e o teste automático que verifica
a mesma regra, pelo nome que aparece em `cenarios/saidas/unittest.txt`. A numeração dos
cenários de terminal é própria (veja a pendência 3).

## Estado inicial de todos os cenários (carga fictícia)

| Perfil | Matrícula | Senha | Vínculos e horários (ID do atendimento) |
|---|---|---|---|
| Administrador | 2026900001 | admin123 | — |
| Ana Fictícia | 2026000001 | ana123 | DCC203 terça 10:00–12:00, presencial, CAD 3 sala 204 (ID 1) · MAT002 quarta 10:00–12:00, presencial, ICEx sala 2033 (ID 2) |
| Caio Exemplo | 2026000002 | caio123 | DCC203 sem horário · MAT001 terça 14:00–16:00, presencial, ICEx sala 1010 (ID 3) e quinta 19:00–20:00, online (ID 4) |
| Duda Teste | 2026000003 | duda123 | FIS069 sem horário |

Disciplinas: DCC203, MAT001, MAT002, FIS069 e ELT001 (esta sem vínculo). DCC999 tem formato
válido, mas está fora do catálogo. Os horários da carga têm data 20/10/2026; os cadastrados ou
alterados na execução têm a data do dia (22/11/2026).

Em toda rejeição do domínio o terminal mostrou "Não foi possível concluir: …" seguido de
"Nenhum dado foi alterado.". Nenhuma das 38 execuções mostrou traceback.

---

## S1 — Entrar e sair

**Preparação:** carga fictícia. **Estado inicial:** nenhuma sessão aberta.

| ID | Regra e entrada | Resultado e estado final esperados | Resultado e estado final observados | Situação | Evidência |
|---|---|---|---|---|---|
| S1-01 | Ana entra (`2026000001`/`ana123`) e sai da sessão | Sessão aberta; submenu com F2 e F1a–F1d; sessão encerrada | "Sessão iniciada. Bem-vindo(a), Ana Fictícia."; submenu: Consultar, Cadastrar horário, Ver meus horários, Alterar, Remover, Sair da sessão; "Sessão encerrada." Senha ecoada como `********` | Aprovado | `saidas/S1-01_login_monitor_valido.txt`; `test_s1_01_login_monitor_valido` |
| S1-02 | Ana com senha errada | Recusa; nenhuma sessão; volta ao menu inicial | "Não foi possível concluir: Matrícula ou senha inválida."; nenhuma linha "Sessão iniciada"; a senha digitada não aparece | Aprovado | `saidas/S1-02_senha_errada.txt`; `test_s1_03_senha_incorreta`, `test_int_04_senha_errada_volta_ao_menu_inicial` |
| S1-03 | Matrícula inexistente `2026999999` | Mesma mensagem do S1-02 | "Não foi possível concluir: Matrícula ou senha inválida." (idêntica) | Aprovado | `saidas/S1-03_matricula_inexistente.txt`; `test_s1_04_matricula_inexistente`, `test_s1_09_mensagem_generica_para_login_invalido` |
| S1-04 | Admin entra, sai da sessão e consulta DCC203 sem login | Submenu só com F2 e A1–A4; F2 funciona depois do logout | Submenu: Consultar, Cadastrar disciplina, Cadastrar monitor, Vincular, Desvincular, Sair da sessão; depois do logout, DCC203 mostra Ana terça 10:00–12:00 e Caio "(sem horários cadastrados nesta disciplina)" | Aprovado | `saidas/S1-04_login_admin_e_sair_da_sessao.txt`; `test_s1_02_login_administrador_valido`, `test_s1_08_permissoes_do_usuario_autenticado` |

## F1a — Cadastrar horário

**Preparação:** carga fictícia; monitor autenticado. **Estado inicial:** a tabela acima.

| ID | Regra e entrada | Resultado e estado final esperados | Resultado e estado final observados | Situação | Evidência |
|---|---|---|---|---|---|
| F1A-01 | (C1 do protótipo) Ana: DCC203, presencial, CAD 3/204, quinta 14:00–16:00 | Aceito; F1b com 3 horários; F2 DCC203: Ana terça e quinta, Caio sem horários | "Horário cadastrado (ID 5): quinta 14:00–16:00 \| presencial \| CAD 3, sala 204 \| atualizado em 22/11/2026"; F1b: IDs 1, 2 e 5; F2: Ana terça 10:00–12:00 e quinta 14:00–16:00; Caio "(sem horários cadastrados nesta disciplina)" | Aprovado | `saidas/F1A-01_cadastro_valido.txt`; `test_f1a_01_cadastro_presencial_valido`, `test_int_01_f1a_pelo_menu_aparece_na_f2` |
| F1A-02 | (C2 do protótipo) Caio: DCC203 terça 15:00–17:00; ele já atende terça 14:00–16:00 em MAT001 | Conflito; nada gravado | "Conflito de horário: você já atende terça 14:00–16:00 em MAT001."; F1b do Caio igual (IDs 3 e 4); MAT001 idêntica antes e depois; DCC203 sem horário do Caio | Aprovado | `saidas/F1A-02_conflito_entre_disciplinas.txt`; `test_f1a_18_conflito_entre_disciplinas`, `test_int_02_f1a_com_conflito_nao_altera_a_base` |
| F1A-03 | (C3 do protótipo) Caio: DCC203 terça 16:00–18:00 (encosta); F2 online; F2 todas; F2 ELT001 | Aceito; online sem horário com contatos; todas mostra o novo; ELT001 sem monitoria | "Horário cadastrado (ID 5): terça 16:00–18:00 …"; online: "Não há horário cadastrado com esse filtro (modalidade e/ou dia)." + contatos de Ana e Caio; todas: Caio terça 16:00–18:00; ELT001: "Nenhuma monitoria cadastrada no sistema para esta disciplina." + aviso | Aprovado | `saidas/F1A-03_horario_encostado.txt`; `test_f1a_20_horario_encostado_ao_fim_e_permitido` |
| F1A-04 | Duda (só FIS069) tenta DCC203 | Rejeição por vínculo; nada gravado | "O monitor de matrícula 2026000003 não é monitor da disciplina DCC203."; F1b: "Você ainda não tem horários cadastrados." | Aprovado | `saidas/F1A-04_monitor_sem_vinculo.txt`; `test_f1a_11_monitor_sem_vinculo` |
| F1A-05 | Ana: DCC999; `dcc 20`; `http://inseguro`; dia `7` e 16:00→14:00; `8h`; prédio vazio | Seis rejeições; dia `7` repete a pergunta; F1b igual | Na ordem: "fora do escopo do sistema em 2026/2."; "Código de disciplina inválido: 'dcc 20'…"; "Link inválido: 'http://inseguro'…"; "Opção 7 não existe. Digite um número de 1 a 6." e "O início (16:00) precisa ser antes do fim (14:00)."; "Horário inválido: '8h'…"; "Prédio e sala são obrigatórios."; F1b: IDs 1 e 2, iguais aos iniciais | Aprovado | `saidas/F1A-05_dados_invalidos.txt`; `test_f1a_09` a `test_f1a_15` |
| F1A-06 | Persistência: execução 1 cadastra DCC203 online sábado 09:00–10:00; execução 2 **na mesma base** consulta DCC203 por sábado | O horário aparece na segunda execução | Execução 1: "Horário cadastrado (ID 5): sábado 09:00–10:00 \| online \| Google Meet: https://meet.exemplo/ana …". Execução 2: DCC203 (dia: sábado) com Ana sábado 09:00–10:00 | Aprovado | `saidas/F1A-06_persistencia_apos_reinicio.txt`; `test_f1a_24_persistencia_apos_reinicio`, `test_int_03_horario_persiste_apos_reiniciar` |

## F1b — Ver meus horários

**Preparação:** carga fictícia; monitor autenticado. **Estado inicial:** a tabela acima.

| ID | Regra e entrada | Resultado e estado final esperados | Resultado e estado final observados | Situação | Evidência |
|---|---|---|---|---|---|
| F1B-01 | Caio pede os próprios horários | IDs 3 e 4, com disciplina, local e data; nada muda | "ID 3 \| MAT001 — Cálculo Diferencial e Integral I \| terça 14:00–16:00 \| presencial \| ICEx, sala 1010 \| atualizado em 20/10/2026" e "ID 4 \| MAT001 … quinta 19:00–20:00 \| online \| Google Meet: https://meet.exemplo/mat001 …" | Aprovado | `saidas/F1B-01_ver_meus_horarios.txt`; `test_f1b_03_caio_tem_presencial_e_online`, `test_f1b_09_consulta_nao_altera_dados` |
| F1B-02 | Duda (sem horários) | Lista vazia | "Você ainda não tem horários cadastrados." | Aprovado | `saidas/F1B-02_monitor_sem_horarios.txt`; `test_f1b_04_monitor_sem_horarios_devolve_tupla_vazia` |

## F1c — Alterar dia e horário

**Preparação:** carga fictícia; monitor autenticado. **Estado inicial:** a tabela acima. O menu mostra a F1b antes de pedir o ID.

| ID | Regra e entrada | Resultado e estado final esperados | Resultado e estado final observados | Situação | Evidência |
|---|---|---|---|---|---|
| F1C-01 | Caio altera o ID 3 de terça 14:00–16:00 para quarta 14:00–16:00 | Aceito; mesmo ID, local e modalidade; data de hoje | "Horário alterado (ID 3): quarta 14:00–16:00 \| presencial \| ICEx, sala 1010 \| atualizado em 22/11/2026"; F2 MAT001: quarta 14:00–16:00 e quinta 19:00–20:00 | Aprovado | `saidas/F1C-01_alteracao_valida.txt`; `test_f1c_01_alteracao_presencial_valida` |
| F1C-02 | Ana tenta alterar o ID 3, que é do Caio | Recusa por titularidade; ID 3 intacto | "O atendimento pertence a outro monitor."; F2 MAT001 ainda com terça 14:00–16:00 | Aprovado | `saidas/F1C-02_atendimento_de_outro_monitor.txt`; `test_f1c_07_outro_monitor_nao_pode_alterar` |
| F1C-03 | Ana altera o ID 2 (MAT002 quarta) para terça 11:00–13:00, que cruza com DCC203 terça 10:00–12:00 | Conflito; ID 2 continua quarta 10:00–12:00 | "Conflito de horário: você já atende terça 10:00–12:00 em DCC203."; F1b: ID 2 continua quarta 10:00–12:00, data 20/10/2026 | Aprovado | `saidas/F1C-03_conflito_com_outra_disciplina.txt`; `test_f1c_05_conflito_entre_disciplinas` |
| F1C-04 | Caio altera o ID 3 para terça 15:00–17:00 (cruza só com ele mesmo) | Aceito | "Horário alterado (ID 3): terça 15:00–17:00 …"; F1b mostra o ID 3 com o novo horário | Aprovado | `saidas/F1C-04_ignora_o_proprio_atendimento.txt`; `test_f1c_03_ignora_proprio_atendimento_no_conflito` |
| F1C-05 | ID `abc`; ID 99; ID 3 com 17:00→15:00 | `abc` repete; 99 inexistente; horário inválido; F1b igual | "'abc' não é um número válido. Digite um número inteiro a partir de 1."; "Atendimento de ID 99 não encontrado."; "O início (17:00) precisa ser antes do fim (15:00)."; F1b: IDs 3 e 4 como no início | Aprovado | `saidas/F1C-05_id_e_horario_invalidos.txt`; `test_f1c_10_id_inexistente`, `test_f1c_12_dia_e_horarios_invalidos` |

## F1d — Remover atendimento

**Preparação:** carga fictícia; monitor autenticado. **Estado inicial:** a tabela acima.

| ID | Regra e entrada | Resultado e estado final esperados | Resultado e estado final observados | Situação | Evidência |
|---|---|---|---|---|---|
| F1D-01 | Ana remove o ID 1 (DCC203 terça) | Removido; F2 DCC203 sem horários, com contatos | "Atendimento de ID 1 removido."; F1b só com o ID 2; F2 DCC203: "Há monitor cadastrado, mas os horários ainda não foram informados." + Ana e Caio | Aprovado | `saidas/F1D-01_remover_valido.txt`; `test_f1d_01_remocao_valida_retorna_none`, `test_f1d_08_preserva_vinculo_e_demais_horarios` |
| F1D-02 | Ana tenta remover o ID 3 (do Caio) | Recusa; atendimentos dos dois iguais | "O atendimento pertence a outro monitor."; F1b da Ana: IDs 1 e 2; F1b do Caio, depois de ele entrar: IDs 3 e 4 | Aprovado | `saidas/F1D-02_remover_de_outro_monitor.txt`; `test_f1d_02_outro_monitor_nao_pode_remover` |
| F1D-03 | Ana remove o ID 99 | Recusa; nada muda | "Atendimento de ID 99 não encontrado."; F1b igual | Aprovado | `saidas/F1D-03_id_inexistente.txt`; `test_f1d_05_id_inexistente` |

## F2 — Consultar monitorias

**Preparação:** carga fictícia; sem login. **Estado inicial:** a tabela acima. As quatro situações são respostas válidas, não rejeições; só código mal formatado ou fora do catálogo é rejeição.

| ID | Regra e entrada | Resultado e estado final esperados | Resultado e estado final observados | Situação | Evidência |
|---|---|---|---|---|---|
| F2-01 | DCC203, sem filtros | Ana com horário; Caio sem horários | "Monitor(a): Ana Fictícia … terça 10:00–12:00 …"; "Monitor(a): Caio Exemplo … (sem horários cadastrados nesta disciplina)" | Aprovado | `saidas/F2-01_sem_filtro.txt`; `test_f2_01_sem_filtro_lista_monitores_e_horarios_ordenados`, `test_f2_06_sem_filtro_monitor_sem_horario_tambem_aparece` |
| F2-02 | MAT001, online | Só quinta 19:00–20:00 | "(modalidade: online \| dia: todos)"; só "quinta 19:00–20:00 \| online …" | Aprovado | `saidas/F2-02_filtro_modalidade.txt`; `test_f2_02_filtro_online_mostra_so_horarios_online` |
| F2-03 | MAT001, terça | Só terça 14:00–16:00 | "(modalidade: todas \| dia: terça)"; só "terça 14:00–16:00 \| presencial …" | Aprovado | `saidas/F2-03_filtro_dia.txt`; `test_f2_03_filtro_por_dia_mostra_so_horarios_do_dia` |
| F2-04 | MAT001, sexta (sem atendimento nesse dia) | Resposta válida sem horário, com e-mails; nada muda | "Não há horário cadastrado com esse filtro (modalidade e/ou dia)."; "Contato: Caio Exemplo <caio.exemplo@ufmg.br>" | Aprovado | `saidas/F2-04_dia_sem_horario.txt`; `test_f2_04_filtro_por_dia_sem_atendimento_nesse_dia` |
| F2-05 | FIS069 | Monitor sem horários, com contato | "Há monitor cadastrado, mas os horários ainda não foram informados."; "Contato: Duda Teste <duda.teste@ufmg.br>" | Aprovado | `saidas/F2-05_monitor_sem_horarios.txt`; `test_f2_07_monitores_sem_nenhum_horario` |
| F2-06 | ELT001 | Nenhuma monitoria cadastrada, com aviso | "Nenhuma monitoria cadastrada no sistema para esta disciplina." + "Atenção: a ausência no sistema não garante que não exista monitoria…" | Aprovado | `saidas/F2-06_nenhuma_monitoria.txt`; `test_f2_09_nenhuma_monitoria_cadastrada` |
| F2-07 | DCC999; `dcc 20`; `mat001` com modalidade `x` e dia `9` (repetem), depois terça | Duas rejeições; minúsculas aceitas; nada muda | "A disciplina DCC999 está fora do escopo do sistema em 2026/2."; "Código de disciplina inválido: 'dcc 20'…"; "'x' não é um número válido…"; "Opção 9 não existe. Digite um número de 1 a 6."; MAT001 (dia: terça) com terça 14:00–16:00 | Aprovado | `saidas/F2-07_rejeicoes_e_normalizacao.txt`; `test_f2_10`, `test_f2_11`, `test_f2_22_codigo_em_minusculas_e_com_espacos_e_aceito`, `test_f2_15_consultar_varias_vezes_nao_muda_dados` |

## A1 — Cadastrar disciplina

**Preparação:** carga fictícia; administrador autenticado. **Estado inicial:** 5 disciplinas.

| ID | Regra e entrada | Resultado e estado final esperados | Resultado e estado final observados | Situação | Evidência |
|---|---|---|---|---|---|
| A1-01 | DCC205 "Estruturas de Dados"; listar; F2 DCC205 | Gravada; aparece na lista; F2 sem monitoria | "Disciplina cadastrada: DCC205 — Estruturas de Dados"; lista com 6 disciplinas; F2 DCC205: "Nenhuma monitoria cadastrada no sistema…" | Aprovado | `saidas/A1-01_cadastro_valido.txt`; `test_a1_01_cadastro_valido_persiste_e_normaliza` |
| A1-02 | DCC203 (já existe); `DC20`; DCC206 sem nome | Três rejeições; lista igual | "Registro duplicado: já existe disciplina DCC203 no sistema."; "Código de disciplina inválido: 'DC20'…"; "O nome da disciplina é obrigatório!"; lista com as 5 iniciais | Aprovado | `saidas/A1-02_rejeicoes.txt`; `test_a1_02_codigo_invalido_nao_grava`, `test_a1_03_disciplina_duplicada_e_rejeitada` |
| A1-03 | Monitora Ana entra | O submenu não oferece A1–A4 | Submenu da Ana só com F2 e F1a–F1d (ver S1-01). O cadastro também recusa A1 chamado com um monitor | Aprovado | `saidas/A1-03_monitor_sem_acesso.txt`; `test_a1_04_monitor_sem_permissao`, `test_int_05_monitor_nao_ve_nem_executa_operacoes_de_admin` |

## A2 — Cadastrar monitor

**Preparação:** carga fictícia; administrador autenticado. **Estado inicial:** 3 monitores.

| ID | Regra e entrada | Resultado e estado final esperados | Resultado e estado final observados | Situação | Evidência |
|---|---|---|---|---|---|
| A2-01 | Eva (2026000004, eva.exemplo@ufmg.br, senha eva123); Eva entra e vê seus horários | Gravada sem vínculo; login aceito; F1b vazia | "Monitor cadastrado: Eva Exemplo (2026000004) <eva.exemplo@ufmg.br>. Ainda sem vínculo com disciplinas."; "Sessão iniciada. Bem-vindo(a), Eva Exemplo."; "Você ainda não tem horários cadastrados." | Aprovado | `saidas/A2-01_cadastro_valido_e_login.txt`; `test_a2_01_cadastro_valido_persiste_e_permite_login` |
| A2-02 | 2026000001 (já existe); e-mail gmail; senha vazia; depois login como 2026000005 | Três rejeições; 2026000005 não existe | "Registro duplicado: já existe matrícula 2026000001 no sistema."; "O e-mail deve ser institucional e terminar em '@ufmg.br'."; "A senha não pode ser vazia."; login de 2026000005: "Matrícula ou senha inválida." | Aprovado | `saidas/A2-02_rejeicoes.txt`; `test_a2_02_email_invalido_nao_grava`, `test_a2_03_senha_vazia_nao_grava`, `test_a2_04_matricula_duplicada_e_rejeitada` |

## A3 — Vincular monitor a disciplina

**Preparação:** carga fictícia; administrador autenticado. **Estado inicial:** a tabela acima.

| ID | Regra e entrada | Resultado e estado final esperados | Resultado e estado final observados | Situação | Evidência |
|---|---|---|---|---|---|
| A3-01 | Vincula Duda a DCC203; Duda cadastra DCC203 sexta 08:00–10:00; F2 DCC203 | Vínculo criado; cadastro aceito; aparece na F2 | "Vínculo criado: Duda Teste agora é monitor(a) de DCC203 …"; "Horário cadastrado (ID 5): sexta 08:00–10:00 …"; F2 DCC203 com Ana, Caio e Duda (sexta 08:00–10:00) | Aprovado | `saidas/A3-01_vincular_e_cadastrar_horario.txt`; `test_a3_01_criar_vinculo_e_persistir` |
| A3-02 | Ana–DCC203 (já existe); 2026999999; DCC999 | Três rejeições; DCC203 igual | "Registro duplicado: já existe vínculo 2026000001-DCC203 no sistema."; "A matrícula 2026999999 não pertence a nenhum monitor cadastrado no sistema."; "A disciplina DCC999 está fora do escopo do sistema em 2026/2."; F2 DCC203 igual à inicial | Aprovado | `saidas/A3-02_rejeicoes.txt`; `test_a3_03`, `test_a3_04`, `test_a3_05` |

## A4 — Desvincular monitor

**Preparação:** carga fictícia; administrador autenticado. **Estado inicial:** a tabela acima.

| ID | Regra e entrada | Resultado e estado final esperados | Resultado e estado final observados | Situação | Evidência |
|---|---|---|---|---|---|
| A4-01 | Desvincula Ana de MAT002 (ela atende em DCC203 e MAT002) | 1 horário removido; MAT002 sem monitoria; DCC203 da Ana intacta | "Vínculo removido. Horários apagados junto com ele: 1."; F2 MAT002: "Nenhuma monitoria cadastrada no sistema…"; F2 DCC203: Ana terça 10:00–12:00 | Aprovado | `saidas/A4-01_desvincular_quem_atende_em_duas.txt`; `test_a4_01_desvincula_quem_atende_em_duas_disciplinas`, `test_a4_02_so_apaga_os_horarios_daquele_vinculo` |
| A4-02 | Desvincula Duda de DCC203 (vínculo inexistente) | Rejeição; FIS069 igual | "O monitor de matrícula 2026000003 não é monitor da disciplina DCC203."; F2 FIS069 com Duda | Aprovado | `saidas/A4-02_vinculo_inexistente.txt`; `test_a4_04_vinculo_inexistente_e_rejeitado` |
| A4-03 | Desvincula Caio de DCC203 (sem horários); Caio tenta cadastrar em DCC203 | 0 horários removidos; cadastro recusado; MAT001 intacta | "Horários apagados junto com ele: 0."; "O monitor de matrícula 2026000002 não é monitor da disciplina DCC203."; F1b do Caio: IDs 3 e 4 | Aprovado | `saidas/A4-03_desvinculado_nao_cadastra_na_disciplina.txt`; `test_a4_03_vinculo_sem_horarios`, `test_a4_13_monitor_desvinculado_nao_cadastra_horario_na_disciplina` |

---

## Testes automáticos

`python -m unittest discover -s tests -v`: **222 testes, 222 OK, nenhuma falha.** Saída
completa em `prototipo_monitoria/cenarios/saidas/unittest.txt`.

| Arquivo | Frente | Testes | O que cobre |
|---|---|---|---|
| `test_F1.py` | B | 61 | F1a–F1d (`test_f1a_*` … `test_f1d_*`) |
| `test_entrar.py` | B | 9 | S1 |
| `test_admin.py` | B/C | 15 | A1–A3 |
| `test_desvincular.py` | C | 15 | A4 |
| `test_consultar_monitorias.py` | C | 24 | F2 |
| `test_usuarios.py` | C | 19 | hierarquia de perfis, `pode()`, `opcoes_menu()`, setter de e-mail |
| `test_persistencia.py` | A | 34 | reconexão, unicidade, cascade do A4, rollback |
| `test_senha.py` | A/B | 4 | hash com sal |
| `test_atendimento.py`, `test_entidades.py` | A/B | 34 | `Atendimento`, polimorfismo, `Disciplina`, `Monitor` |
| `test_integracao.py` | D | 7 | menu + cadastro + SQLite (`test_int_01` a `07`) |

## Registro de defeitos

| # | Defeito | Como reproduzir | Consequência | Correção | Reexecução |
|---|---|---|---|---|---|
| 1 | Menu do protótipo quebrado depois dos merges | Na ponta da `frente-c-usuarios`: `printf '0\n' \| python -m monitorias` | `TypeError: CadastroMonitorias.__init__() missing 1 required positional argument: 'repositorio'`; `dados_demo.py` ainda chamava `adicionar_atendimento`, que não existe mais | Menu e `__main__.py` reescritos sobre a base SQLite; `dados_demo.py` removido (commit `8db5139`) | 37 cenários e `test_int_01` a `07`: OK |
| 2 | O cadastro decidia permissões com `isinstance(usuario, Administrador/Monitor)`, contra o guia (autorização polimórfica) | `grep -n isinstance monitorias/dominio/cadastro.py` na `frente-c-usuarios` | Fere o requisito de polimorfismo (item 5) | `_exigir_permissao` usa só `usuario.pode()` e recusa também `None` e textos (commit `43f3ebf`) | 215 testes (regressão) e depois 222: OK |
| 3 | Testes de A1–A3, parte da F2 e parte do A4 sem o ID do cenário no nome | `grep "def test_a1_" tests/test_admin.py` | A coluna Evidência não apontaria para uma linha com ID | Testes renomeados, sem mudar o conteúdo (commit `d68ad58`) | 215 testes: OK |

Nenhum dos 37 cenários de terminal divergiu do resultado esperado.

## Pendências

1. **Tag `v1.0-final`:** não criada. Depende do ok do Luiz e do grupo.
2. **Decisões do grupo registradas no código:**
   - `registrado_em` passa a ser a data da alteração na F1c, como o guia sugeria;
   - F1b devolve pares `(Disciplina, Atendimento)`;
   - a exceção de autorização é `PermissaoNegada` (o guia dizia `AcessoNegado`).
3. **Numeração dos cenários de terminal × testes:** os IDs dos cenários de terminal (por
   exemplo F1C-02) não coincidem com os números dos testes da mesma regra (por exemplo
   `test_f1c_07_outro_monitor_nao_pode_alterar`). Cada linha da tabela aponta o teste pelo
   nome completo.
4. **A carga fictícia grava pelo repositório, não por `cadastrar_*`.** O guia pedia que ela
   passasse pelo cadastro. Os dados são validados pelos construtores e gravados numa única
   transação, e a data fixa (20/10/2026) mantém as saídas reproduzíveis. O `setUp` de
   `test_consultar_monitorias.py` também grava direto pelo repositório.
5. **F1c com ID inexistente** só é recusada depois que o monitor digita o novo dia e horário.
   A regra fica no cadastro; o menu não consulta o ID antes.
6. **Contatos em "sem horário com esse filtro":** o domínio devolve a lista vazia, e o menu faz
   uma segunda consulta, só de leitura, para mostrar os e-mails.

## Trechos de código para captura no PDF

| Trecho | Arquivo e linhas |
|---|---|
| `try/except ValueError` na conversão das opções | `prototipo_monitoria/monitorias/menu.py`, `ler_opcao()`, linhas 80–105 (try/except nas linhas 97–101) |
| Leitura da senha com `isatty` (getpass só no terminal) | `prototipo_monitoria/monitorias/menu.py`, `ler_senha()`, linhas 63–77 |
| Ponto único `try/except ErroMonitorias` | `prototipo_monitoria/monitorias/menu.py`, `_executar_acao()`, linhas 357–371; `executar()` (linhas 395–415), com `EOFError`/`KeyboardInterrupt` na linha 413 |
| Submenu montado por `opcoes_menu()`, sem `isinstance` | `prototipo_monitoria/monitorias/menu.py`, `ACOES_DA_SESSAO` (linha 325), `opcoes_da_sessao()` (338–344) e `entrar()` (374–392) |
| Autorização polimórfica no cadastro | `prototipo_monitoria/monitorias/dominio/cadastro.py`, `_exigir_permissao()`, linhas 263–273 |
| Ponto de entrada que não cria dados | `prototipo_monitoria/monitorias/__main__.py`, `iniciar()`, linhas 22–52 |

## Conferência do ZIP

Arquivo: `sistema-monitorias-final.zip`, na raiz do repositório e fora do Git. Tem 78 entradas,
todas dentro de `prototipo_monitoria/`. Não contém `.git`, `__pycache__`, `.db`, `dados/` nem
`cenarios/saidas/`. Foi extraído numa pasta temporária limpa, e só o README foi seguido, com
`python` 3.13.5:

| Passo do README | Resultado observado |
|---|---|
| 1. `python -m monitorias.persistencia.seed_demo` | "Base de demonstração criada em …/dados/monitorias.db." Rodado de novo: "… já tem dados; nada foi alterado." |
| 2. `python -m monitorias`: F2 de FIS069, login da Duda e F1a em FIS069 quarta 18:00–19:00 online | F2: "Há monitor cadastrado, mas os horários ainda não foram informados."; "Sessão iniciada. Bem-vindo(a), Duda Teste."; "Horário cadastrado (ID 5): quarta 18:00–19:00 \| online …"; a F2 seguinte mostra o horário |
| 2 de novo, em nova execução | A F2 de FIS069 ainda mostra quarta 18:00–19:00: persistiu |
| 3. `python -m unittest discover -s tests -v` | "Ran 222 tests … OK" |

Conclusão: **aprovado**. O programa inicia, as funcionalidades rodam e os testes executam
seguindo só o README.
