"""
Cria o banco, aplica o schema, executa seed_receitas.sql e insere um usuário (senha hasheada).
Uso: python init_db.py
"""
import sqlite3
from pathlib import Path

from werkzeug.security import generate_password_hash

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "receitas.db"


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(
        "DROP TABLE IF EXISTS receita;\nDROP TABLE IF EXISTS usuario;\n"
    )
    conn.executescript(ROOT.joinpath("schema.sql").read_text(encoding="utf-8"))

    seed = ROOT.joinpath("seed_receitas.sql").read_text(encoding="utf-8")
    conn.executescript(seed)

    senha_hash = generate_password_hash("admin123")
    conn.execute(
        """
        INSERT INTO usuario (nome, login, senha, situacao)
        VALUES (?, ?, ?, ?)
        """,
        ("Administrador", "admin", senha_hash, "ativo"),
    )
    conn.commit()
    conn.close()
    print(f"Banco criado em {DB_PATH}")
    print("Usuário: admin | Senha: admin123")


if __name__ == "__main__":
    main()
