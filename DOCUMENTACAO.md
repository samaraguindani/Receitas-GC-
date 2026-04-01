# Documentação — Sistema de registro de receitas

## Parte 1 — Aplicação

### Escolhas técnicas

| Item | Escolha |
|------|---------|
| Linguagem | Python 3 |
| Framework web | Flask |
| Banco de dados | SQLite (arquivo `receitas.db`) |
| Servidor em produção (VM) | Gunicorn |

Motivo: instalação simples na VM (apenas Python e `pip`), sem serviço separado de banco; atende aos requisitos acadêmicos com clareza.

### Modelagem do banco de dados

**Tabela `usuario`**

| Campo | Tipo (SQLite) | Descrição |
|-------|----------------|-----------|
| id | INTEGER PK AUTOINCREMENT | Identificador |
| nome | TEXT NOT NULL | Nome exibido |
| login | TEXT NOT NULL UNIQUE | Usuário para login |
| senha | TEXT NOT NULL | Senha armazenada com hash (Werkzeug) |
| situacao | TEXT NOT NULL DEFAULT 'ativo' | Ex.: ativo, inativo |

**Tabela `receita`**

| Campo | Tipo (SQLite) | Descrição |
|-------|----------------|-----------|
| id | INTEGER PK AUTOINCREMENT | Identificador |
| nome | TEXT NOT NULL | Nome da receita |
| descricao | TEXT | Texto livre |
| data_registro | TEXT NOT NULL | Data no formato ISO (AAAA-MM-DD) |
| custo | REAL NOT NULL | Custo estimado em reais |
| tipo_receita | TEXT NOT NULL | Valores permitidos: `doce` ou `salgada` (CHECK) |

Relação: nesta versão não há chave estrangeira entre `receita` e `usuario` (todas as receitas são globais ao sistema após login).

### Arquivos de schema e dados

- `schema.sql` — DDL das tabelas.
- `seed_receitas.sql` — **10 inserts** na tabela `receita`, conforme enunciado (execução direta no banco).
- `init_db.py` — Cria o banco, aplica `schema.sql`, executa `seed_receitas.sql` e insere **1 usuário** (`admin` / `admin123`) com senha hasheada (recomendado em vez de senha em texto puro no SQL).

### Interface desenvolvida

1. **Tela de login** (`/login`): formulário com login e senha; mensagem de erro em caso de falha.
2. **Listagem de receitas** (`/`): tabela com nome, tipo, data, custo e trecho da descrição; exige usuário logado.
3. **CRUD de receitas (ponto extra)**:
   - **Criar**: `/receitas/nova`
   - **Ler**: listagem (e detalhes na própria linha)
   - **Atualizar**: `/receitas/<id>/editar`
   - **Excluir**: POST em `/receitas/<id>/excluir` (com confirmação no navegador)

### Como rodar localmente (Windows)

1. Instalar [Python 3](https://www.python.org/downloads/) (marcar opção de adicionar ao PATH, se disponível).
2. Abrir PowerShell na pasta do projeto (`Receitas`).
3. Criar ambiente virtual (recomendado):
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
4. Instalar dependências:
   ```powershell
   python -m pip install -r requirements.txt
   ```
5. Criar banco e dados iniciais:
   ```powershell
   python init_db.py
   ```
6. Subir a aplicação:
   ```powershell
   python app.py
   ```
7. Acessar no navegador: `http://127.0.0.1:5000` — faça login com **admin** / **admin123**.

---

## Parte 2 — Publicação na VM

### Como acessar a VM

No terminal do seu computador (PowerShell, CMD ou Git Bash):

```bash
ssh univates@177.44.248.89
```

Aceite a impressão digital do host, se for a primeira conexão. Use a senha ou chave SSH fornecida pela instituição.

### Instalação das ferramentas na VM (Linux — Debian/Ubuntu)

Ajuste `apt` se a VM for outra distribuição.

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip
```

Copiar o projeto para a VM (exemplos):

- **SCP a partir do Windows (PowerShell):**
  ```powershell
  scp -r "C:\Users\samil\OneDrive\Documentos\Receitas" univates@177.44.248.89:~/
  ```
- Ou clone via Git, se o projeto estiver em um repositório remoto.

Na VM:

```bash
cd ~/Receitas
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python init_db.py
```

### Implantação da aplicação (tornar público na rede da VM)

Defina uma chave secreta forte para sessões:

```bash
export FLASK_SECRET_KEY="altere-para-uma-string-longa-e-aleatoria"
```

**Opção A — Flask (desenvolvimento / teste rápido, porta 5000)**

```bash
cd ~/Receitas-GC-   # ou o nome da sua pasta do projeto
source .venv/bin/activate
export FLASK_USE_RELOADER=0
python app.py
```

O `app.py` já escuta em `0.0.0.0` na porta definida por `PORT` (padrão **5000**).  
**Importante:** `python app.py --host=0.0.0.0 --port=5000` **não altera** host/porta no Flask; esses argumentos são ignorados. Use `export PORT=5000` se quiser outra porta.

**Opção B — Gunicorn (recomendado para deixar rodando)**

```bash
source .venv/bin/activate
gunicorn -w 2 -b 0.0.0.0:5000 app:app
```

(Use `8000` no lugar de `5000` se preferir; a URL no navegador deve usar a mesma porta.)

Para manter o processo após sair do SSH, use `screen`, `tmux` ou um serviço `systemd`.

---

### Firewall: se o navegador “carrega infinito” ou não abre

O servidor pode estar ok **dentro da VM**, mas o **tráfego da internet até a porta** estar bloqueado.

1. **Na própria VM**, teste se responde:
   ```bash
   curl -sS -o /dev/null -w "%{http_code}" http://127.0.0.1:5000/login
   ```
   Se retornar `200`, a aplicação está no ar.

2. **Libere a porta no firewall** (Ubuntu/Debian com `ufw`):
   ```bash
   sudo ufw status
   sudo ufw allow 5000/tcp
   sudo ufw reload
   ```
   Se o `ufw` estiver **inactive**, o bloqueio pode ser outro (iptables, painel da nuvem, rede da faculdade).

3. **No seu PC**, teste (PowerShell ou terminal):
   ```bash
   curl -v --connect-timeout 5 http://177.44.248.89:5000/login
   ```
   - **Timeout / sem resposta:** porta fechada no firewall da VM, bloqueio no roteador/rede da instituição, ou IP/porta incorretos. Peça ao professor/infra se a porta **5000** é permitida de fora; às vezes só **80** ou **443** estão liberados (aí seria necessário Nginx na frente ou pedir liberação).

4. Mantenha o terminal SSH **aberto** enquanto testa com `python app.py`; se fechar o SSH sem `screen`/serviço, o processo encerra.

---

### URL de acesso

Com a aplicação em `0.0.0.0:5000` e firewall liberado:

**`http://177.44.248.89:5000`**

Se você usar Gunicorn em outra porta (ex.: 8000), use **`http://177.44.248.89:8000`**.

---

## Resumo de entregáveis do enunciado

| Requisito | Onde está |
|-----------|-----------|
| Projeto + BD | Flask + SQLite |
| Tabelas receita e usuario | `schema.sql` |
| 10 receitas via INSERT no banco | `seed_receitas.sql` |
| ≥1 usuário | `init_db.py` |
| Tela login + listagem | `templates/login.html`, `templates/receitas_lista.html` |
| CRUD receitas | Rotas em `app.py` + formulários |
| `.gitignore` | Raiz do projeto |

---

*Documento gerado para entrega acadêmica — sistema simples e funcional.*
