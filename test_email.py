import os
import smtplib
from email.message import EmailMessage

required = [
    "SMTP_HOST",
    "SMTP_PORT",
    "SMTP_USER",
    "SMTP_PASSWORD",
    "SMTP_TO",
]

missing = [k for k in required if not os.environ.get(k)]
if missing:
    raise SystemExit(f"Variaveis faltando: {', '.join(missing)}")

host = os.environ["SMTP_HOST"]
port = int(os.environ["SMTP_PORT"])
user = os.environ["SMTP_USER"]
password = os.environ["SMTP_PASSWORD"]
to = os.environ["SMTP_TO"]
from_addr = os.environ.get("SMTP_FROM", user)

msg = EmailMessage()
msg["Subject"] = "[Receitas] Teste SMTP local"
msg["From"] = from_addr
msg["To"] = to
msg.set_content("Teste SMTP enviado com sucesso a partir do projeto Receitas.")

with smtplib.SMTP(host, port, timeout=15) as server:
    server.starttls()
    server.login(user, password)
    server.send_message(msg)

print("E-mail de teste enviado com sucesso.")