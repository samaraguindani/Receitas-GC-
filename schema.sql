-- Modelagem: Receitas (salgados e doces) + usuarios do sistema

CREATE TABLE IF NOT EXISTS usuario (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    login TEXT NOT NULL UNIQUE,
    senha TEXT NOT NULL,
    situacao TEXT NOT NULL DEFAULT 'ativo'
);

CREATE TABLE IF NOT EXISTS receita (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    descricao TEXT,
    data_registro TEXT NOT NULL,
    custo REAL NOT NULL,
    tipo_receita TEXT NOT NULL CHECK (tipo_receita IN ('doce', 'salgada'))
);