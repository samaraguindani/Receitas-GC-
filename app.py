import os
import smtplib
import sqlite3
from datetime import date
from email.message import EmailMessage
from functools import wraps
from io import BytesIO
from pathlib import Path

from flask import (
    Flask,
    Response,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from werkzeug.security import check_password_hash

ROOT = Path(__file__).resolve().parent
DEFAULT_DATABASE = ROOT / "receitas.db"
ALLOWED_TIPOS = {"doce", "salgada"}


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get(
            "FLASK_SECRET_KEY", "troque-esta-chave-em-producao-use-variavel-de-ambiente"
        ),
        DATABASE=os.environ.get("DATABASE_PATH", str(DEFAULT_DATABASE)),
        SMTP_HOST=os.environ.get("SMTP_HOST", "smtp.gmail.com"),
        SMTP_PORT=int(os.environ.get("SMTP_PORT", "587")),
        SMTP_USER=os.environ.get("SMTP_USER", ""),
        SMTP_PASSWORD=os.environ.get("SMTP_PASSWORD", ""),
        SMTP_FROM=os.environ.get("SMTP_FROM", ""),
        SMTP_TO=os.environ.get("SMTP_TO", ""),
    )

    if test_config:
        app.config.update(test_config)

    def get_db() -> sqlite3.Connection:
        if "db" not in g:
            g.db = sqlite3.connect(app.config["DATABASE"], timeout=10)
            g.db.row_factory = sqlite3.Row
            # Reduz erros intermitentes de lock quando rodando com multiplos workers.
            g.db.execute("PRAGMA journal_mode=WAL")
            g.db.execute("PRAGMA busy_timeout=5000")
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

    def parse_filtros() -> tuple[str, str]:
        filtro_data = request.args.get("data", "").strip()
        filtro_tipo = request.args.get("tipo", "").strip().lower()
        if filtro_tipo and filtro_tipo not in ALLOWED_TIPOS:
            filtro_tipo = ""
        return filtro_data, filtro_tipo

    def query_receitas(filtro_data: str = "", filtro_tipo: str = ""):
        sql = """
            SELECT id, nome, descricao, data_registro, custo, tipo_receita
            FROM receita
            WHERE 1=1
        """
        params: list[str] = []
        if filtro_data:
            sql += " AND data_registro = ?"
            params.append(filtro_data)
        if filtro_tipo:
            sql += " AND tipo_receita = ?"
            params.append(filtro_tipo)
        sql += " ORDER BY data_registro DESC, id DESC"
        return get_db().execute(sql, params).fetchall()

    def query_receita_por_id(rid: int):
        return get_db().execute(
            """
            SELECT id, nome, descricao, data_registro, custo, tipo_receita
            FROM receita
            WHERE id = ?
            """,
            (rid,),
        ).fetchone()

    def enviar_email_acao_receita(acao: str, receita_nome: str, receita_id: int | None = None) -> bool:
        smtp_user = app.config.get("SMTP_USER")
        smtp_password = app.config.get("SMTP_PASSWORD")
        smtp_to = app.config.get("SMTP_TO")

        if not smtp_user or not smtp_password or not smtp_to:
            return False

        msg = EmailMessage()
        msg["Subject"] = f"[Receitas] Receita {acao}: {receita_nome}"
        msg["From"] = app.config.get("SMTP_FROM") or smtp_user
        msg["To"] = smtp_to
        detalhe_id = f" (ID {receita_id})" if receita_id is not None else ""
        msg.set_content(f"A receita '{receita_nome}'{detalhe_id} foi {acao} no sistema.")

        with smtplib.SMTP(app.config["SMTP_HOST"], app.config["SMTP_PORT"], timeout=10) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        return True

    def exportar_receitas_pdf(receitas) -> bytes:
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4)
        _, height = A4
        y = height - 40

        pdf.setTitle("Relatorio de Receitas")
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(40, y, "Relatorio de Receitas")
        y -= 24

        pdf.setFont("Helvetica", 9)
        pdf.drawString(40, y, f"Gerado em: {date.today().isoformat()}")
        y -= 20

        pdf.setFont("Helvetica-Bold", 9)
        pdf.drawString(40, y, "Nome")
        pdf.drawString(180, y, "Tipo")
        pdf.drawString(240, y, "Data")
        pdf.drawString(310, y, "Descricao")
        pdf.drawRightString(560, y, "Custo")
        y -= 16

        pdf.setFont("Helvetica", 9)
        for r in receitas:
            if y <= 54:
                pdf.showPage()
                y = height - 40
                pdf.setFont("Helvetica-Bold", 9)
                pdf.drawString(40, y, "Nome")
                pdf.drawString(180, y, "Tipo")
                pdf.drawString(240, y, "Data")
                pdf.drawString(310, y, "Descricao")
                pdf.drawRightString(560, y, "Custo")
                y -= 16
                pdf.setFont("Helvetica", 9)
            nome = str(r["nome"])[:26]
            tipo = str(r["tipo_receita"])
            data_reg = str(r["data_registro"])
            descricao = (r["descricao"] or "").replace("\n", " ").strip()
            descricao = descricao[:48] if descricao else "-"

            pdf.drawString(40, y, nome)
            pdf.drawString(180, y, tipo)
            pdf.drawString(240, y, data_reg)
            pdf.drawString(310, y, descricao)
            pdf.drawRightString(560, y, f"R$ {float(r['custo']):.2f}")
            y -= 14

        pdf.save()
        buffer.seek(0)
        return buffer.read()

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if session.get("user_id"):
            return redirect(url_for("listar_receitas"))

        if request.method == "POST":
            login_val = request.form.get("login", "").strip()
            senha = request.form.get("senha", "")
            row = get_db().execute(
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
            flash("Login ou senha invalidos.", "danger")

        return render_template("login.html")

    @app.route("/logout")
    def logout():
        session.clear()
        return redirect(url_for("login"))

    @app.route("/health")
    def health():
        return {"status": "ok"}, 200

    @app.route("/")
    @login_required
    def listar_receitas():
        filtro_data, filtro_tipo = parse_filtros()
        rows = query_receitas(filtro_data=filtro_data, filtro_tipo=filtro_tipo)
        return render_template(
            "receitas_lista.html",
            receitas=rows,
            filtro_data=filtro_data,
            filtro_tipo=filtro_tipo,
        )

    @app.route("/receitas/exportar-pdf")
    @login_required
    def exportar_pdf():
        filtro_data, filtro_tipo = parse_filtros()
        try:
            rows = query_receitas(filtro_data=filtro_data, filtro_tipo=filtro_tipo)
            pdf_bytes = exportar_receitas_pdf(rows)
            return Response(
                pdf_bytes,
                mimetype="application/pdf",
                headers={"Content-Disposition": "attachment; filename=receitas.pdf"},
            )
        except Exception:
            app.logger.exception("Falha ao gerar PDF geral.")
            flash("Erro ao gerar PDF. Tente novamente.", "danger")
            return redirect(url_for("listar_receitas"))

    @app.route("/receitas/<int:rid>/exportar-pdf")
    @login_required
    def exportar_pdf_receita(rid: int):
        try:
            row = query_receita_por_id(rid)
            if not row:
                flash("Receita nao encontrada.", "warning")
                return redirect(url_for("listar_receitas"))

            pdf_bytes = exportar_receitas_pdf([row])
            return Response(
                pdf_bytes,
                mimetype="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename=receita-{rid}.pdf"
                },
            )
        except Exception:
            app.logger.exception("Falha ao gerar PDF individual (id=%s).", rid)
            flash("Erro ao gerar PDF da receita.", "danger")
            return redirect(url_for("listar_receitas"))

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
                flash("Custo invalido.", "danger")
                return render_template("receita_form.html", receita=None)

            if tipo not in ALLOWED_TIPOS:
                tipo = "doce"
            if not nome:
                flash("Nome e obrigatorio.", "danger")
                return render_template("receita_form.html", receita=None)

            db = get_db()
            cursor = db.execute(
                """
                INSERT INTO receita (nome, descricao, data_registro, custo, tipo_receita)
                VALUES (?, ?, ?, ?, ?)
                """,
                (nome, descricao or None, data_reg, custo, tipo),
            )
            db.commit()

            try:
                enviou = enviar_email_acao_receita("cadastrada", nome, cursor.lastrowid)
                if enviou:
                    flash("E-mail de notificacao enviado.", "info")
            except Exception:
                app.logger.exception("Falha ao enviar e-mail de notificacao (cadastro).")
                flash("Receita salva, mas houve erro no envio de e-mail.", "warning")

            flash("Receita cadastrada.", "success")
            return redirect(url_for("listar_receitas"))

        return render_template("receita_form.html", receita=None)

    @app.route("/receitas/<int:rid>/editar", methods=["GET", "POST"])
    @login_required
    def editar_receita(rid: int):
        db = get_db()
        row = db.execute("SELECT * FROM receita WHERE id = ?", (rid,)).fetchone()
        if not row:
            flash("Receita nao encontrada.", "warning")
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
                flash("Custo invalido.", "danger")
                return render_template("receita_form.html", receita=dict(row))

            if tipo not in ALLOWED_TIPOS:
                tipo = "doce"
            if not nome:
                flash("Nome e obrigatorio.", "danger")
                return render_template("receita_form.html", receita=dict(row))

            db.execute(
                """
                UPDATE receita
                SET nome=?, descricao=?, data_registro=?, custo=?, tipo_receita=?
                WHERE id=?
                """,
                (nome, descricao or None, data_reg, custo, tipo, rid),
            )
            db.commit()

            try:
                enviou = enviar_email_acao_receita("atualizada", nome, rid)
                if enviou:
                    flash("E-mail de notificacao enviado.", "info")
            except Exception:
                app.logger.exception("Falha ao enviar e-mail de notificacao (edicao).")
                flash("Receita atualizada, mas houve erro no envio de e-mail.", "warning")

            flash("Receita atualizada.", "success")
            return redirect(url_for("listar_receitas"))

        return render_template("receita_form.html", receita=dict(row))

    @app.route("/receitas/<int:rid>/excluir", methods=["POST"])
    @login_required
    def excluir_receita(rid: int):
        try:
            db = get_db()
            db.execute("DELETE FROM receita WHERE id = ?", (rid,))
            db.commit()
            flash("Receita excluida.", "info")
        except Exception:
            app.logger.exception("Falha ao excluir receita (id=%s).", rid)
            flash("Erro ao excluir receita. Tente novamente.", "danger")
        return redirect(url_for("listar_receitas"))

    return app


app = create_app()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    use_reloader = os.environ.get("FLASK_USE_RELOADER", "0") == "1"
    app.run(debug=True, host="0.0.0.0", port=port, use_reloader=use_reloader)