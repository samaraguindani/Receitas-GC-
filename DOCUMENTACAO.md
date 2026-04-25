# Documentacao - Registro de Receitas (Flask)

## 1) Implementacao pronta

Aplicacao web em Python + Flask + SQLite com:
- Login
- CRUD de receitas
- Filtros por data e status
- Exportacao para PDF
- Envio de e-mail apos criar/editar receita (SMTP Gmail)
- 20 testes unitarios

---

## 2) Melhor forma recomendada para VM

Use este padrao:
- Gunicorn para servir a app
- systemd para manter o processo sempre ativo
- arquivo de ambiente separado para segredos

Arquivos criados no projeto para facilitar:
- `deploy/receitas.env.example`
- `deploy/receitas.service.example`

---

## 3) Passo a passo (GitHub -> VM)

### 3.1 No seu computador (subir para GitHub)

```bash
cd "C:\Users\samil\OneDrive\Documentos\Receitas"
git status
git add .
git commit --trailer "Made-with: Cursor" -m "Configura deploy recomendado com systemd e env file"
git push origin main
```

### 3.2 Na VM (177.44.248.89)

```bash
ssh univates@177.44.248.89
sudo apt update
sudo apt install -y git python3 python3-venv python3-pip
```

Se ainda nao clonou:

```bash
git clone <URL_DO_REPOSITORIO> Receitas-GC-
cd Receitas-GC-
```

Se ja clonou:

```bash
cd Receitas-GC-
git pull origin main
```

### 3.3 Ambiente Python

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python init_db.py
```

---

## 4) Configurar segredos (arquivo env seguro)

Crie pasta para configuracao e proteja permissao:

```bash
sudo mkdir -p /etc/receitas
sudo cp deploy/receitas.env.example /etc/receitas/receitas.env
sudo chown root:root /etc/receitas/receitas.env
sudo chmod 600 /etc/receitas/receitas.env
```

Edite o arquivo:

```bash
sudo nano /etc/receitas/receitas.env
```

Preencha com seus dados reais:

```env
FLASK_SECRET_KEY=chave-grande-segura
PORT=5000
FLASK_USE_RELOADER=0
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=boardlabgames@gmail.com
SMTP_PASSWORD=SENHA_DE_APP_GOOGLE
SMTP_FROM=boardlabgames@gmail.com
SMTP_TO=samara.guindani@universo.univates.br
```

Importante: `SMTP_PASSWORD` deve ser senha de app do Google, nao senha normal.

---

## 5) Configurar service no systemd

Copie o service de exemplo:

```bash
sudo cp deploy/receitas.service.example /etc/systemd/system/receitas.service
```

Se seu caminho do projeto for diferente de `/home/univates/Receitas-GC-`, edite:

```bash
sudo nano /etc/systemd/system/receitas.service
```

Valide estes campos:
- `WorkingDirectory`
- `ExecStart`
- `User`

Depois ative:

```bash
sudo systemctl daemon-reload
sudo systemctl enable receitas
sudo systemctl restart receitas
```

Ver status/log:

```bash
sudo systemctl status receitas --no-pager
sudo journalctl -u receitas -n 100 --no-pager
```

---

## 6) Liberar porta e testar

```bash
sudo ufw allow 5000/tcp
sudo ufw reload
sudo ufw status
```

Teste na VM:

```bash
curl -v http://127.0.0.1:5000/login
```

Teste no seu PC:

```bash
curl -v http://177.44.248.89:5000/login
```

URL:
- http://177.44.248.89:5000

---

## 7) Atualizar app no futuro

Sempre que mudar codigo no GitHub:

```bash
cd ~/Receitas-GC-
git pull origin main
source .venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart receitas
sudo systemctl status receitas --no-pager
```

---

## 8) Gmail (resumo rapido)

1. Conta Google com verificacao em 2 etapas ativa
2. Criar senha de app
3. Colar senha de app em `SMTP_PASSWORD` no arquivo `/etc/receitas/receitas.env`
4. Reiniciar service: `sudo systemctl restart receitas`

---

## 9) Checklist final

- [ ] Projeto atualizado no GitHub
- [ ] Dependencias instaladas na VM
- [ ] Banco criado com `python init_db.py`
- [ ] `/etc/receitas/receitas.env` preenchido
- [ ] `receitas.service` ativo no systemd
- [ ] Porta 5000 liberada
- [ ] URL abre externamente
- [ ] Criar/editar receita envia e-mail