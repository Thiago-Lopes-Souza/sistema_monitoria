# Frente A — Persistência

Rascunho da seção **Base de dados** do relatório (item 8) e do contrato da camada de
dados para as frentes B, C e D.

## Base de dados

O sistema guarda os dados em **SQLite**, pelo módulo `sqlite3` da biblioteca padrão.
Nada precisa ser instalado. O SQLite é a única fonte dos dados: os dicionários em
memória do protótipo não continuam como uma segunda base. Cada leitura monta objetos
novos a partir das tabelas.

### Arquivos

| Arquivo | Responsabilidade |
|---|---|
| `persistencia/schema.sql` | `CREATE TABLE` das quatro tabelas, com chaves e `CHECK` |
| `persistencia/conexao.py` | Abre a base, liga `PRAGMA foreign_keys` e aplica o esquema |
| `persistencia/repositorio.py` | SQL parametrizado; converte linhas em objetos e objetos em linhas |
| `persistencia/seed_demo.py` | Carga dos dados fictícios de demonstração |
| `dominio/senha.py` | Hash da senha com sal (PBKDF2-HMAC-SHA256) |

### Esquema

| Tabela | Chave | Restrições |
|---|---|---|
| `usuarios` | `matricula` | e-mail terminado em `@ufmg.br`; `papel` só pode ser `monitor` ou `admin`; guarda só o hash e o sal da senha |
| `disciplinas` | `codigo` | código no formato `AAA999` |
| `vinculos` | `(matricula, codigo)` | um vínculo por par (R7); chaves estrangeiras para usuários e disciplinas |
| `atendimentos` | `id` (AUTOINCREMENT) | chave estrangeira para o vínculo com `ON DELETE CASCADE`; dia de segunda a sábado; `inicio < fim`; cada modalidade preenche só as suas colunas de local |

Os `CHECK` são uma rede de segurança. Quem valida e explica o erro ao usuário continua
sendo o domínio. Se um `CHECK` dispara, é sinal de defeito no código, e não de
entrada inválida.

### Inicialização

```
cd prototipo_monitoria
python -m monitorias.persistencia.seed_demo            # cria dados/monitorias.db, se ainda não existir
python -m monitorias.persistencia.seed_demo --recriar  # apaga e recria a base de demonstração
```

- O esquema usa `IF NOT EXISTS`, então aplicá-lo de novo numa base existente não apaga nada.
- A carga só roda numa base vazia e acontece numa única transação. Por isso pode ser
  executada várias vezes sem duplicar registros, e o programa não recarrega os dados a
  cada início.
- O arquivo `.db` não vai para o Git nem para o ZIP. Vão o `schema.sql` e o `seed_demo.py`.
- Os testes usam bases `:memory:` ou arquivos temporários, nunca a base de demonstração.

### Dados fictícios

| Perfil | Matrícula | Nome | Senha de demonstração |
|---|---|---|---|
| Administrador | 2026900001 | Admin Fictício | `admin123` |
| Monitor | 2026000001 | Ana Fictícia | `ana123` |
| Monitor | 2026000002 | Caio Exemplo | `caio123` |
| Monitor | 2026000003 | Duda Teste | `duda123` |

| Disciplina | Monitores e horários | Para que serve |
|---|---|---|
| DCC203 PDS I | Ana: terça 10–12, presencial · Caio: sem horário | F2 com horários e monitor sem horário na lista (C1 do protótipo) |
| MAT001 Cálculo I | Caio: terça 14–16, presencial · quinta 19–20, online | conflito entre disciplinas (C2), horário encostado (C3) |
| MAT002 GAAL | Ana: quarta 10–12, presencial | Ana atende em duas disciplinas: F1C-03 e A4-01 |
| FIS069 Física III | Duda: sem horários | situação "monitor sem horários" |
| ELT001 Circuitos I | ninguém | situação "nenhuma monitoria cadastrada" |

DCC999 fica de fora de propósito (rejeição "fora do escopo" da F2). DCC203 e MAT001
continuam como no protótipo, então os cenários C1 a C3 continuam valendo. MAT002 é a
única novidade: sem ela, nenhum monitor tinha horários em duas disciplinas.

### Decisões

1. **O repositório recebe uma conexão pronta**, e não o caminho do arquivo. Assim os
   testes usam `:memory:`, que só existe dentro da conexão que a criou.
2. **Toda gravação exige `with repositorio.transacao():`.** Fora disso, o repositório
   lança `RuntimeError`. O bloco faz commit se terminar bem e rollback se sair qualquer
   exceção, inclusive uma recusa do domínio. Uma transação dentro de outra entra na de
   fora. Quem abre a transação é o cadastro (camada de negócio), depois das validações.
3. **Chave repetida vira `RegistroDuplicado`**, filha de `ErroMonitorias`. Outras
   violações da base (CHECK, chave estrangeira) seguem como `sqlite3.IntegrityError`,
   porque indicam defeito, e escondê-las atrapalharia achar o erro.
4. **O hash da senha não entra nos objetos.** `buscar_usuario` devolve `Monitor` ou
   `Administrador` sem a senha; o hash só sai por `buscar_credenciais`, que apenas o
   login usa. Assim um objeto passado ao menu nunca carrega a senha.
5. **O papel escolhe a classe sem `if`**: um dicionário liga `"monitor"` a `Monitor` e
   `"admin"` a `Administrador`. Na gravação, há um método para cada perfil
   (`inserir_monitor`, `inserir_administrador`), então ninguém passa o papel como texto.
6. **A tradução atendimento ↔ linha** pergunta `modalidade()` ao próprio objeto, porque
   a tabela tem colunas diferentes por modalidade. Na leitura, o objeto passa pelo
   construtor normal, então um registro inválido gera `DadosInvalidos` em vez de um
   objeto inválido.
7. **`AUTOINCREMENT` no id dos atendimentos**: um id apagado nunca é reaproveitado,
   então um id antigo não passa a apontar para outro horário (F1c e F1d).
8. **A carga verifica se a base está vazia, em vez de só usar `INSERT OR IGNORE`.** O
   `INSERT OR IGNORE` não impede horários duplicados, porque o id é gerado pela base, e
   ainda faria voltar um horário de demonstração que o monitor tivesse removido.
9. **A carga grava pelo repositório, e não pelo cadastro.** O primeiro administrador
   não pode ser criado pelo cadastro, que exige um administrador para cadastrar
   usuários. Os objetos ainda passam pelos construtores (validação) e um teste confere
   que os horários da carga não se sobrepõem.
10. **SQL só com placeholders `?`.** Um teste confere que `x' OR '1'='1` não encontra nada.

## Contrato do repositório (para B e C)

Todos os métodos de gravação são chamados só pelo `CadastroMonitorias`, dentro de
`repositorio.transacao()`, depois de todas as validações.

| Método | Devolve | Observação |
|---|---|---|
| `transacao()` | gerenciador de contexto | commit ou rollback |
| `esta_vazia()` | `bool` | usado pela carga |
| `inserir_monitor(monitor, senha_hash, senha_sal)` | — | `RegistroDuplicado` se a matrícula existir |
| `inserir_administrador(admin, senha_hash, senha_sal)` | — | idem |
| `buscar_usuario(matricula)` | `Monitor` / `Administrador` / `None` | sem a senha |
| `buscar_credenciais(matricula)` | `(hash, sal)` / `None` | só para `entrar()` |
| `inserir_disciplina(disciplina)` | — | `RegistroDuplicado` |
| `buscar_disciplina(codigo)` | `Disciplina` / `None` | |
| `listar_disciplinas()` | `tuple[Disciplina, ...]` | ordenadas pelo código |
| `inserir_vinculo(matricula, codigo)` | — | `RegistroDuplicado` |
| `excluir_vinculo(matricula, codigo)` | `int` | nº de horários apagados em cascata (A4) |
| `buscar_vinculo(matricula, codigo)` | `Vinculo` / `None` | com os atendimentos |
| `vinculos_do_monitor(matricula)` | `tuple[Vinculo, ...]` | todos os horários do monitor (R5) |
| `vinculos_da_disciplina(codigo)` | `tuple[Vinculo, ...]` | para a F2 |
| `inserir_atendimento(matricula, codigo, atendimento)` | `Atendimento` com `id` | |
| `buscar_atendimento(id)` | `(Vinculo, Atendimento)` / `None` | titularidade: `vinculo.monitor.matricula` |
| `atualizar_atendimento(id, atendimento)` | `Atendimento` | F1c; mantém id e vínculo |
| `excluir_atendimento(id)` | `bool` | F1d |

Hash de senha: `gerar_hash_senha(senha) -> (hash, sal)` e
`conferir_senha(senha, hash, sal) -> bool`, em `dominio/senha.py`.

## Mudanças pequenas em arquivos de outras frentes

Necessárias para o repositório montar os objetos. Nenhum teste existente mudou.

- `atendimento.py` (B): parâmetro opcional `id_atendimento` e property `id`
  (só leitura; `None` antes de gravar).
- `vinculo.py` (B): parâmetro opcional `atendimentos` no construtor, usado só pelo
  repositório ao remontar o vínculo. Isso permite que `adicionar_atendimento` vire
  `_adicionar_atendimento` sem que o repositório precise chamar o método privado.
- `excecoes.py`: nova exceção `RegistroDuplicado`.
