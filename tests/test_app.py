import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from werkzeug.security import generate_password_hash

from app import create_app

ROOT = Path(__file__).resolve().parent.parent


class ReceitasAppTests(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp_dir.name) / "test_receitas.db"

        self.app = create_app(
            {
                "TESTING": True,
                "SECRET_KEY": "test-secret",
                "DATABASE": str(self.db_path),
            }
        )
        self.client = self.app.test_client()
        self._init_db()

    def tearDown(self):
        self.tmp_dir.cleanup()

    def _init_db(self):
        schema = (ROOT / "schema.sql").read_text(encoding="utf-8")
        seed = (ROOT / "seed_receitas.sql").read_text(encoding="utf-8")
        conn = sqlite3.connect(self.db_path)
        conn.executescript(schema)
        conn.executescript(seed)
        conn.execute(
            "INSERT INTO usuario (nome, login, senha, situacao) VALUES (?, ?, ?, ?)",
            ("Administrador", "admin", generate_password_hash("admin123"), "ativo"),
        )
        conn.execute(
            "INSERT INTO usuario (nome, login, senha, situacao) VALUES (?, ?, ?, ?)",
            ("Bloqueado", "bloq", generate_password_hash("abc123"), "inativo"),
        )
        conn.commit()
        conn.close()

    def _login(self, login="admin", senha="admin123"):
        return self.client.post(
            "/login",
            data={"login": login, "senha": senha},
            follow_redirects=True,
        )

    def test_login_page_loads(self):
        resp = self.client.get("/login")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Acesso", resp.get_data(as_text=True))

    def test_root_requires_login(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login", resp.location)

    def test_login_success(self):
        resp = self._login()
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Receitas cadastradas", resp.get_data(as_text=True))

    def test_login_invalid_password(self):
        resp = self._login(senha="errada")
        self.assertIn("Login ou senha inval", resp.get_data(as_text=True))

    def test_login_inactive_user(self):
        resp = self._login(login="bloq", senha="abc123")
        self.assertIn("Login ou senha inval", resp.get_data(as_text=True))

    def test_logout_clears_session(self):
        self._login()
        resp = self.client.get("/logout", follow_redirects=True)
        self.assertIn("Acesso", resp.get_data(as_text=True))

    def test_list_has_seed_data(self):
        self._login()
        resp = self.client.get("/")
        text = resp.get_data(as_text=True)
        self.assertIn("Coxinha de frango", text)
        self.assertIn("Brownie", text)

    def test_filter_by_date(self):
        self._login()
        resp = self.client.get("/?data=2024-06-01")
        text = resp.get_data(as_text=True)
        self.assertIn("Brownie", text)
        self.assertNotIn("Coxinha de frango", text)

    def test_filter_by_tipo_doce(self):
        self._login()
        resp = self.client.get("/?tipo=doce")
        text = resp.get_data(as_text=True)
        self.assertIn("Brownie", text)
        self.assertNotIn("Coxinha de frango", text)

    def test_filter_by_tipo_salgada(self):
        self._login()
        resp = self.client.get("/?tipo=salgada")
        text = resp.get_data(as_text=True)
        self.assertIn("Coxinha de frango", text)
        self.assertNotIn("Brownie", text)

    def test_invalid_tipo_filter_is_ignored(self):
        self._login()
        resp = self.client.get("/?tipo=zzz")
        text = resp.get_data(as_text=True)
        self.assertIn("Coxinha de frango", text)
        self.assertIn("Brownie", text)

    def test_create_recipe_success_without_email_config(self):
        self._login()
        resp = self.client.post(
            "/receitas/nova",
            data={
                "nome": "Teste Nova",
                "descricao": "desc",
                "data_registro": "2026-04-25",
                "custo": "9.90",
                "tipo_receita": "doce",
            },
            follow_redirects=True,
        )
        self.assertIn("Receita cadastrada.", resp.get_data(as_text=True))

    def test_create_recipe_validates_name(self):
        self._login()
        resp = self.client.post(
            "/receitas/nova",
            data={
                "nome": "",
                "descricao": "desc",
                "data_registro": "2026-04-25",
                "custo": "9.90",
                "tipo_receita": "doce",
            },
            follow_redirects=True,
        )
        self.assertIn("Nome", resp.get_data(as_text=True))

    def test_create_recipe_validates_cost(self):
        self._login()
        resp = self.client.post(
            "/receitas/nova",
            data={
                "nome": "Receita X",
                "descricao": "desc",
                "data_registro": "2026-04-25",
                "custo": "abc",
                "tipo_receita": "doce",
            },
            follow_redirects=True,
        )
        self.assertIn("Custo", resp.get_data(as_text=True))

    def test_update_recipe_success(self):
        self._login()
        resp = self.client.post(
            "/receitas/1/editar",
            data={
                "nome": "Coxinha Atualizada",
                "descricao": "ok",
                "data_registro": "2024-01-15",
                "custo": "2.20",
                "tipo_receita": "salgada",
            },
            follow_redirects=True,
        )
        self.assertIn("Receita atualizada.", resp.get_data(as_text=True))

    def test_update_recipe_not_found(self):
        self._login()
        resp = self.client.get("/receitas/999/editar", follow_redirects=True)
        self.assertIn("encontrada", resp.get_data(as_text=True))

    def test_delete_recipe_success(self):
        self._login()
        resp = self.client.post("/receitas/1/excluir", follow_redirects=True)
        self.assertIn("Receita exclu", resp.get_data(as_text=True))

    def test_export_pdf_requires_login(self):
        resp = self.client.get("/receitas/exportar-pdf")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login", resp.location)

    def test_export_pdf_success(self):
        self._login()
        resp = self.client.get("/receitas/exportar-pdf")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, "application/pdf")
        self.assertIn("attachment; filename=receitas.pdf", resp.headers.get("Content-Disposition", ""))

    def test_export_single_receita_pdf_success(self):
        self._login()
        resp = self.client.get("/receitas/1/exportar-pdf")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, "application/pdf")
        self.assertIn("attachment; filename=receita-1.pdf", resp.headers.get("Content-Disposition", ""))

    @patch("app.smtplib.SMTP")
    def test_email_is_sent_on_create_when_configured(self, smtp_mock):
        self.app.config.update(
            SMTP_USER="user@gmail.com",
            SMTP_PASSWORD="app-password",
            SMTP_TO="destino@gmail.com",
            SMTP_FROM="user@gmail.com",
        )
        self._login()
        resp = self.client.post(
            "/receitas/nova",
            data={
                "nome": "Com Email",
                "descricao": "desc",
                "data_registro": "2026-04-25",
                "custo": "11.50",
                "tipo_receita": "doce",
            },
            follow_redirects=True,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(smtp_mock.called)


if __name__ == "__main__":
    unittest.main()