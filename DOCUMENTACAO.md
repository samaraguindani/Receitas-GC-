# Documentacao - Projeto Receitas (Flask)

## 1) Escopo implementado

Aplicacao web em Python + Flask + SQLite com:
- Login
- CRUD de receitas
- Filtro por data
- Filtro por tipo (`doce` ou `salgada`)
- Exportacao PDF de todas as receitas filtradas
- Exportacao PDF individual por receita (botao por linha)
- Envio de e-mail apos criar/editar receita (SMTP Gmail)
- Testes automatizados (21 testes)

---

## 2) Estrutura principal do projeto

- `app.py` - rotas, regras, e-mail, PDF
- `schema.sql` - schema do banco
- `seed_receitas.sql` - inserts iniciais
- `init_db.py` - recria banco e popula dados
- `templates/` - telas HTML
- `tests/test_app.py` - testes automatizados
- `test_email.py` - teste direto de SMTP
- `test_local.ps1` - diagnostico rapido local no Windows
- `requirements.txt` - dependencias

---

## 3) Banco de dados

### Tabela `usuario`
- `id` INTEGER PRIMARY KEY AUTOINCREMENT
- `nome` TEXT NOT NULL
- `login` TEXT NOT NULL UNIQUE
- `senha` TEXT NOT NULL
- `situacao` TEXT NOT NULL DEFAULT `ativo`

### Tabela `receita`
- `id` INTEGER PRIMARY KEY AUTOINCREMENT
- `nome` TEXT NOT NULL
- `descricao` TEXT
- `data_registro` TEXT NOT NULL
- `custo` REAL NOT NULL
- `tipo_receita` TEXT NOT NULL (`doce`/`salgada`)

---

## 4) Rotas principais

- `/login` - login
- `/logout` - logout
- `/` - listagem com filtros
- `/receitas/nova` - criar receita
- `/receitas/<id>/editar` - editar receita
- `/receitas/<id>/excluir` - excluir receita
- `/receitas/exportar-pdf` - PDF com todas as receitas (respeita filtros)
- `/receitas/<id>/exportar-pdf` - PDF da receita individual
- `/health` - health check

---

## 5) Como rodar local (Windows)

### 5.1 Preparar ambiente

```powershell
cd "C:\Users\samil\OneDrive\Documentos\Receitas"
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
py init_db.py
```

### 5.2 Rodar aplicacao

```powershell
$env:FLASK_SECRET_KEY="local-secret-key"
$env:PORT="5000"
$env:FLASK_USE_RELOADER="0"
py app.py
```

Acesso local:
- `http://127.0.0.1:5000`

Login padrao:
- usuario: `admin`
- senha: `admin123`

---

## 6) E-mail (Gmail SMTP)

### 6.1 Configurar variaveis no terminal local

```powershell
$env:SMTP_HOST="smtp.gmail.com"
$env:SMTP_PORT="587"
$env:SMTP_USER="seu_email@gmail.com"
$env:SMTP_PASSWORD="SENHA_DE_APP_GOOGLE"
$env:SMTP_FROM="seu_email@gmail.com"
$env:SMTP_TO="destino@exemplo.com"
```

### 6.2 Teste direto de SMTP

```powershell
.\.venv\Scripts\python.exe test_email.py
```

Se funcionar, deve imprimir:
- `E-mail de teste enviado com sucesso.`

Observacao:
- `SMTP_PASSWORD` deve ser senha de app do Google (nao a senha normal da conta).

---

## 7) Testes automatizados

### 7.1 Rodar todos os testes

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v
```

Estado atual esperado:
- 21 testes
- resultado `OK`

### 7.2 Script de diagnostico local rapido

```powershell
.\test_local.ps1
```

Esse script:
- instala deps
- recria banco
- sobe app temporariamente
- testa endpoints basicos
- finaliza processo

---

## 8) Subir para GitHub

No seu computador:

```bash
cd "C:\Users\samil\OneDrive\Documentos\Receitas"
git status
git add .
git commit --trailer "Made-with: Cursor" -m "Atualiza PDF completo e documentacao final"
git push origin main
```

---

## 9) Publicar na VM (177.44.248.89)

SSH:

```bash
ssh univates@177.44.248.89
```

### 9.1 Instalar ferramentas (uma vez)

```bash
sudo apt update
sudo apt install -y git python3 python3-venv python3-pip
```

### 9.2 Obter codigo

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

### 9.3 Ambiente e banco

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python init_db.py
```

---

## 10) Deploy recomendado na VM (gunicorn + systemd)

### 10.1 Arquivo seguro de variaveis

```bash
sudo mkdir -p /etc/receitas
sudo cp deploy/receitas.env.example /etc/receitas/receitas.env
sudo chown root:root /etc/receitas/receitas.env
sudo chmod 600 /etc/receitas/receitas.env
sudo nano /etc/receitas/receitas.env
```

Preencher com valores reais:

```env
FLASK_SECRET_KEY=chave-grande-segura
PORT=5000
FLASK_USE_RELOADER=0
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=seu_email@gmail.com
SMTP_PASSWORD=SENHA_DE_APP_GOOGLE
SMTP_FROM=seu_email@gmail.com
SMTP_TO=destino@exemplo.com
```

### 10.2 Service systemd

```bash
sudo cp deploy/receitas.service.example /etc/systemd/system/receitas.service
sudo nano /etc/systemd/system/receitas.service
```

Validar:
- `WorkingDirectory=/home/univates/Receitas-GC-`
- `ExecStart=/home/univates/Receitas-GC-/.venv/bin/gunicorn --workers 2 --bind 0.0.0.0:${PORT} app:app`

Ativar:

```bash
sudo systemctl daemon-reload
sudo systemctl enable receitas
sudo systemctl restart receitas
```

Logs/status:

```bash
sudo systemctl status receitas --no-pager
sudo journalctl -u receitas -n 100 --no-pager
```

---

## 11) Liberar porta e testar na VM

```bash
sudo ufw allow 5000/tcp
sudo ufw reload
sudo ufw status
```

Teste dentro da VM:

```bash
curl -v http://127.0.0.1:5000/login
curl -v http://127.0.0.1:5000/health
```

Teste externo (do seu PC):

```bash
curl -v http://177.44.248.89:5000/login
```

URL final:
- `http://177.44.248.89:5000`

---

## 12) Comandos uteis de operacao

Atualizar app em producao:

```bash
cd ~/Receitas-GC-
git pull origin main
source .venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart receitas
sudo systemctl status receitas --no-pager
```

Ver erro de e-mail no log da app:

```bash
sudo journalctl -u receitas -n 200 --no-pager
```

---

## 13) Checklist final (100% funcionamento)

- [ ] Local abre em `http://127.0.0.1:5000`
- [ ] Login com `admin/admin123`
- [ ] CRUD funcionando
- [ ] Filtro por data funcionando
- [ ] Filtro por tipo (`doce`/`salgada`) funcionando
- [ ] PDF geral exporta `Nome | Tipo | Data | Descricao | Custo`
- [ ] PDF individual por linha funcionando
- [ ] `test_email.py` envia e-mail
- [ ] `python -m unittest ...` retorna `OK` (21 testes)
- [ ] VM acessivel em `http://177.44.248.89:5000`