# Documentação — Registro de Receitas (Flask)

## 1) O que foi implementado

Aplicação web em **Python + Flask + SQLite** com:

- Login (`/login`)
- Listagem de receitas (`/`)
- CRUD de receitas
- **Filtros** por **data** e **status** (ativa/inativa)
- **Exportação para PDF**
- **Envio de e-mail (Gmail SMTP)** após **criar** ou **editar** receita
- **20 testes unitários**

---

## 2) Modelagem do banco

### Tabela `usuario`
- `id` INTEGER PK AUTOINCREMENT
- `nome` TEXT NOT NULL
- `login` TEXT NOT NULL UNIQUE
- `senha` TEXT NOT NULL (hash)
- `situacao` TEXT NOT NULL DEFAULT `ativo`

### Tabela `receita`
- `id` INTEGER PK AUTOINCREMENT
- `nome` TEXT NOT NULL
- `descricao` TEXT
- `data_registro` TEXT NOT NULL
- `custo` REAL NOT NULL
- `tipo_receita` TEXT NOT NULL (`doce`/`salgada`)
- `status_receita` TEXT NOT NULL (`ativa`/`inativa`)

Arquivos:
- `schema.sql`
- `seed_receitas.sql` (10 inserts)
- `init_db.py` (recria banco + seed + usuário admin)

---

## 3) Interface desenvolvida

- `templates/login.html` — tela de login
- `templates/receitas_lista.html` — listagem + filtros + botão exportar PDF
- `templates/receita_form.html` — criar/editar com tipo e status

---

## 4) Rodar local (Windows)

```powershell
cd "C:\Users\samil\OneDrive\Documentos\Receitas"
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
py init_db.py
py app.py
```

Acesse: `http://127.0.0.1:5000`

Login padrão:
- usuário: `admin`
- senha: `admin123`

---

## 5) Configurar e-mail Gmail (obrigatório para envio)

A aplicação envia e-mail ao criar/editar receita **somente** se as variáveis SMTP estiverem definidas.

### Passos no Google
1. Entrar na conta Google que enviará os e-mails.
2. Ativar **Verificação em 2 Etapas**.
3. Criar uma **Senha de app** (App Password) para "Mail".
4. Guardar a senha de app (16 caracteres).

### Variáveis de ambiente (Linux/VM)

```bash
export SMTP_HOST="smtp.gmail.com"
export SMTP_PORT="587"
export SMTP_USER="seu_email@gmail.com"
export SMTP_PASSWORD="SENHA_DE_APP_GOOGLE"
export SMTP_FROM="seu_email@gmail.com"
export SMTP_TO="destino@gmail.com"
```

> Se não configurar essas variáveis, a aplicação continua funcionando, mas não envia e-mail.

---

## 6) Testes unitários (20)

Arquivo: `tests/test_app.py`

Executar:

```bash
python -m unittest -v
```

Os testes cobrem login, CRUD, filtros, exportação PDF e envio de e-mail (com mock).

---

## 7) Subir no GitHub (passo a passo)

> Faça no seu computador local, na pasta do projeto.

```bash
git status
git add .
git commit --trailer "Made-with: Cursor" -m "Implementa email, filtros, PDF e 20 testes"
```

Criar repositório no GitHub (site) e copiar a URL HTTPS/SSH.

```bash
git remote add origin <URL_DO_REPOSITORIO>
git branch -M main
git push -u origin main
```

---

## 8) Publicação na VM via GitHub

VM correta:
- IP: `177.44.248.89`
- SSH: `ssh univates@177.44.248.89`

### 8.1 Acessar VM e instalar dependências

```bash
ssh univates@177.44.248.89
sudo apt update
sudo apt install -y git python3 python3-venv python3-pip
```

### 8.2 Clonar projeto na VM

```bash
git clone <URL_DO_REPOSITORIO> Receitas-GC-
cd Receitas-GC-
```

### 8.3 Ambiente virtual + dependências

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python init_db.py
```

### 8.4 Configurar variáveis de ambiente (app + e-mail)

```bash
export FLASK_SECRET_KEY="uma-chave-longa-e-segura"
export PORT="5000"
export FLASK_USE_RELOADER="0"

export SMTP_HOST="smtp.gmail.com"
export SMTP_PORT="587"
export SMTP_USER="seu_email@gmail.com"
export SMTP_PASSWORD="SENHA_DE_APP_GOOGLE"
export SMTP_FROM="seu_email@gmail.com"
export SMTP_TO="destino@gmail.com"
```

### 8.5 Subir aplicação

Opção A (simples):

```bash
python app.py
```

Opção B (recomendado):

```bash
gunicorn -w 2 -b 0.0.0.0:5000 app:app
```

### 8.6 Liberar porta no firewall (se `ufw` ativo)

```bash
sudo ufw status
sudo ufw allow 5000/tcp
sudo ufw reload
```

### 8.7 Testar acesso

Na VM:

```bash
curl -v http://127.0.0.1:5000/login
```

No seu PC:

```bash
curl -v http://177.44.248.89:5000/login
```

URL final esperada:
- `http://177.44.248.89:5000`

---

## 9) Estrutura principal do projeto

- `app.py`
- `init_db.py`
- `schema.sql`
- `seed_receitas.sql`
- `requirements.txt`
- `templates/`
- `static/`
- `tests/test_app.py`

---

## 10) Observações importantes

- A senha de e-mail do Gmail deve ser **senha de app**, não a senha normal da conta.
- Em produção, não deixe segredos fixos no código; use sempre variável de ambiente.
- Se a URL externa não abrir, normalmente é firewall/rede (não o Flask).