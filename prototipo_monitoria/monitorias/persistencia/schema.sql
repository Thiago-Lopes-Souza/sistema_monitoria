-- Esquema da base de dados do sistema de monitorias (SQLite).
--
-- Pode ser executado várias vezes: tudo usa IF NOT EXISTS, então rodar de novo
-- numa base que já existe não apaga nem duplica nada.
--
-- Os CHECK são uma rede de segurança. Quem valida e explica o erro ao usuário
-- é o domínio (Atendimento, Disciplina, UsuarioCadastrado, CadastroMonitorias);
-- se um CHECK disparar, é sinal de defeito no código, não de entrada inválida.
--
-- As chaves estrangeiras só valem com PRAGMA foreign_keys = ON, que conexao.py
-- liga em toda conexão.

CREATE TABLE IF NOT EXISTS usuarios (
    matricula   TEXT PRIMARY KEY CHECK (length(trim(matricula)) > 0),
    nome        TEXT NOT NULL    CHECK (length(trim(nome)) > 0),
    email       TEXT NOT NULL    CHECK (email LIKE '%@ufmg.br'),
    papel       TEXT NOT NULL    CHECK (papel IN ('monitor', 'admin')),
    senha_hash  BLOB NOT NULL,
    senha_sal   BLOB NOT NULL
);

CREATE TABLE IF NOT EXISTS disciplinas (
    codigo  TEXT PRIMARY KEY CHECK (codigo GLOB '[A-Z][A-Z][A-Z][0-9][0-9][0-9]'),
    nome    TEXT NOT NULL    CHECK (length(trim(nome)) > 0)
);

-- Um vínculo por par (monitor, disciplina): R7.
CREATE TABLE IF NOT EXISTS vinculos (
    matricula  TEXT NOT NULL REFERENCES usuarios(matricula),
    codigo     TEXT NOT NULL REFERENCES disciplinas(codigo),
    PRIMARY KEY (matricula, codigo)
);

-- Cada atendimento pertence a exatamente um vínculo (composição da Etapa 2).
-- ON DELETE CASCADE: desvincular (A4) apaga só os horários daquele vínculo.
-- AUTOINCREMENT: um id apagado nunca é reaproveitado, então um id antigo
-- guardado pelo menu nunca passa a apontar para outro atendimento.
CREATE TABLE IF NOT EXISTS atendimentos (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    matricula      TEXT NOT NULL,
    codigo         TEXT NOT NULL,
    dia            TEXT NOT NULL CHECK (dia IN ('segunda', 'terça', 'quarta',
                                                'quinta', 'sexta', 'sábado')),
    inicio         TEXT NOT NULL CHECK (inicio GLOB '[0-2][0-9]:[0-5][0-9]'),
    fim            TEXT NOT NULL CHECK (fim GLOB '[0-2][0-9]:[0-5][0-9]'),
    modalidade     TEXT NOT NULL CHECK (modalidade IN ('presencial', 'online')),
    predio         TEXT,
    sala           TEXT,
    plataforma     TEXT,
    link           TEXT,
    registrado_em  TEXT NOT NULL,   -- data ISO (aaaa-mm-dd) do cadastro ou da última alteração
    -- 'hh:mm' com zero à esquerda: comparar como texto dá a mesma ordem que
    -- comparar os horários (R1: início estritamente antes do fim).
    CHECK (inicio < fim),
    -- Cada modalidade preenche só as suas colunas de local (R4).
    CHECK (
        (modalidade = 'presencial' AND predio IS NOT NULL AND sala IS NOT NULL
                                   AND plataforma IS NULL AND link IS NULL)
     OR (modalidade = 'online'     AND plataforma IS NOT NULL AND link LIKE 'https://_%'
                                   AND predio IS NULL AND sala IS NULL)
    ),
    FOREIGN KEY (matricula, codigo) REFERENCES vinculos(matricula, codigo)
        ON DELETE CASCADE
);

-- A checagem de conflito lê todos os horários de um monitor.
CREATE INDEX IF NOT EXISTS idx_atendimentos_matricula ON atendimentos(matricula);
CREATE INDEX IF NOT EXISTS idx_atendimentos_codigo    ON atendimentos(codigo);
