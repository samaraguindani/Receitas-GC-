import os
import sqlite3
from datetime import date
from functools import wraps
from pathlib import Path

from flask import (
    Flask,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash

ROOT = Path(__file__).resolve().parent
DATABASE = ROOT / "receitas.db"

app = Flask(__name__)
app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY", "troque-esta-chave-em-producao-use-variavel-de-ambiente"
)


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("listar_receitas"))

    if request.method == "POST":
        login_val = request.form.get("login", "").strip()
        senha = request.form.get("senha", "")
        db = get_db()
        row = db.execute(
            "SELECT id, nome, senha, situacao FROM usuario WHERE login = ?",
            (login_val,),
        ).fetchone()
        if (
            row
            and row["situacao"] == "ativo"
            and check_password_hash(row["senha"], senha)
        ):
            session.clear()
            session["user_id"] = row["id"]
            session["user_nome"] = row["nome"]
            nxt = request.args.get("next") or url_for("listar_receitas")
            return redirect(nxt)
        flash("Login ou senha inválidos.", "danger")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
@login_required
def listar_receitas():
    db = get_db()
    rows = db.execute(
        """
        SELECT id, nome, descricao, data_registro, custo, tipo_receita
        FROM receita
        ORDER BY data_registro DESC, id DESC
        """
    ).fetchall()
    return render_template("receitas_lista.html", receitas=rows)


@app.route("/receitas/nova", methods=["GET", "POST"])
@login_required
def nova_receita():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        descricao = request.form.get("descricao", "").strip()
        custo_raw = request.form.get("custo", "0").replace(",", ".")
        tipo = request.form.get("tipo_receita", "doce")
        data_reg = request.form.get("data_registro") or date.today().isoformat()

        try:
            custo = float(custo_raw)
        except ValueError:
            flash("Custo inválido.", "danger")
            return render_template("receita_form.html", receita=None)

        if tipo not in ("doce", "salgada"):
            tipo = "doce"
        if not nome:
            flash("Nome é obrigatório.", "danger")
            return render_template("receita_form.html", receita=None)

        db = get_db()
        db.execute(
            """
            INSERT INTO receita (nome, descricao, data_registro, custo, tipo_receita)
            VALUES (?, ?, ?, ?, ?)
            """,
            (nome, descricao or None, data_reg, custo, tipo),
        )
        db.commit()
        flash("Receita cadastrada.", "success")
        return redirect(url_for("listar_receitas"))

    return render_template("receita_form.html", receita=None)


@app.route("/receitas/<int:rid>/editar", methods=["GET", "POST"])
@login_required
def editar_receita(rid: int):
    db = get_db()
    row = db.execute("SELECT * FROM receita WHERE id = ?", (rid,)).fetchone()
    if not row:
        flash("Receita não encontrada.", "warning")
        return redirect(url_for("listar_receitas"))

    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        descricao = request.form.get("descricao", "").strip()
        custo_raw = request.form.get("custo", "0").replace(",", ".")
        tipo = request.form.get("tipo_receita", "doce")
        data_reg = request.form.get("data_registro") or date.today().isoformat()

        try:
            custo = float(custo_raw)
        except ValueError:
            flash("Custo inválido.", "danger")
            return render_template("receita_form.html", receita=dict(row))

        if tipo not in ("doce", "salgada"):
            tipo = "doce"
        if not nome:
            flash("Nome é obrigatório.", "danger")
            return render_template("receita_form.html", receita=dict(row))

        db.execute(
            """
            UPDATE receita SET nome=?, descricao=?, data_registro=?, custo=?, tipo_receita=?
            WHERE id=?
            """,
            (nome, descricao or None, data_reg, custo, tipo, rid),
        )
        db.commit()
        flash("Receita atualizada.", "success")
        return redirect(url_for("listar_receitas"))

    return render_template("receita_form.html", receita=dict(row))


@app.route("/receitas/<int:rid>/excluir", methods=["POST"])
@login_required
def excluir_receita(rid: int):
    db = get_db()
    db.execute("DELETE FROM receita WHERE id = ?", (rid,))
    db.commit()
    flash("Receita excluída.", "info")
    return redirect(url_for("listar_receitas"))


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
