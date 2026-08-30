# SAPIA — Protótipo funcional

Protótipo do SAPIA — Sistema de Automação de Petição Inicial para Aposentadoria.

Funcionalidades atualmente disponíveis:

- Interface web;
- Cadastro de usuários;
- Confirmação de cadastro por e-mail;
- Login e controle de acesso;
- Backend FastAPI;
- Banco SQLite persistente;
- Sessões por token mantidas em memória;
- Tela inicial do sistema;
- Área de upload ainda não conectada ao processamento completo de documentos.

---

## Requisitos

### Backend

- Python 3.11 ou superior

### Frontend

- Node.js 20 ou superior
- npm

---

# Rodando o projeto pela primeira vez

O frontend e o backend devem permanecer rodando simultaneamente em dois terminais diferentes.

## 1. Backend

Entre na pasta:

```bash
cd backend
```

### Windows

Crie o ambiente virtual:

```bash
py -3.12 -m venv .venv
```

Instale as dependências:

```bash
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### macOS/Linux

Crie e ative o ambiente virtual:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

---

## 2. Configuração de e-mail

O cadastro de usuários envia um e-mail de confirmação. Para utilizar essa funcionalidade, crie:

```text
backend/.env
```

Use `backend/.env.example` como modelo:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=seu_email@gmail.com
SMTP_PASSWORD=sua_senha_de_aplicativo
SMTP_FROM=seu_email@gmail.com
APP_BASE_URL=http://127.0.0.1:8000
FRONTEND_URL=http://localhost:5173
```

### Importante

O arquivo `.env` contém credenciais e não deve ser enviado ao Git.

Ele já está incluído no `.gitignore`.

Para Gmail, utilize uma **senha de aplicativo**, e não a senha normal da conta Google.

Para gerar uma senha de aplicativo no Google, a verificação em duas etapas da conta deve estar ativada.

Nunca coloque credenciais reais dentro do `.env.example`.

---

## 3. Iniciar o backend

### Windows

```bash
cd backend
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### macOS/Linux

Com o ambiente virtual ativado:

```bash
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

A API ficará disponível em:

```text
http://127.0.0.1:8000
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

---

## 4. Iniciar o frontend

Em outro terminal:

```bash
cd frontend
npm install
npm run dev
```

A aplicação ficará normalmente disponível em:

```text
http://localhost:5173
```

---

# Preciso instalar tudo novamente?

Não.

A criação do ambiente virtual, `pip install` e `npm install` são necessários na primeira execução ou quando as dependências forem alteradas.

Nas execuções seguintes:

### Backend — Windows

```bash
cd backend
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### Frontend

```bash
cd frontend
npm run dev
```

---

# RF1 — Cadastro de usuários

O cadastro implementado permite:

- Informar nome completo;
- Informar e-mail;
- Informar senha;
- Repetir a senha;
- Validar o formato do e-mail;
- Validar nome entre 3 e 100 caracteres;
- Exigir senha com no mínimo 8 caracteres;
- Exigir letra maiúscula;
- Exigir letra minúscula;
- Exigir número;
- Exigir caractere especial;
- Impedir cadastro duplicado do mesmo e-mail;
- Criar a conta inicialmente com status `PENDENTE`;
- Gerar token de confirmação;
- Enviar e-mail de confirmação;
- Bloquear login antes da confirmação;
- Ativar a conta após uso do link;
- Registrar a data de confirmação;
- Impedir reutilização do token.

## Fluxo de teste

1. Acesse:

```text
http://localhost:5173
```

2. Clique em **Criar uma conta**.

3. Preencha:

```text
Nome completo
E-mail
Senha
Repita a senha
```

4. Clique em **Cadastrar**.

5. O sistema exibirá uma mensagem solicitando a confirmação do e-mail.

6. Antes de confirmar, tente realizar o login.

O sistema deverá informar que a conta ainda não foi confirmada.

7. Abra o e-mail recebido.

O assunto esperado é:

```text
Confirme seu cadastro no SAPIA
```

8. Clique no link de confirmação.

Para testes locais, o link utiliza `127.0.0.1`, portanto deve ser aberto no mesmo computador em que o backend está sendo executado.

9. A página:

```text
Conta confirmada com sucesso!
```

será exibida.

10. Clique em **Ir para o SAPIA**.

11. Faça login com o usuário recém-confirmado.

O acesso deverá ser liberado.

### Observação

Dependendo do provedor de e-mail e da reputação da conta remetente utilizada nos testes, o e-mail de confirmação pode ser direcionado para a pasta de spam ou lixo eletrônico.

---

# Credenciais de demonstração

O usuário demonstrativo continua disponível:

```text
E-mail: admin@sapia.com
Senha: Sapia@123
```

---

# Banco de dados

O protótipo utiliza SQLite.

O arquivo utilizado é:

```text
backend/sapia_demo.db
```

O banco é criado automaticamente quando necessário.

Diferentemente da versão inicial do protótipo, o banco **não é mais apagado sempre que o backend reinicia**.

Isso permite manter usuários cadastrados entre as execuções.

O arquivo `.db` está ignorado pelo Git, portanto cada desenvolvedor terá seu próprio banco local.

Alterações necessárias para compatibilidade com bancos criados em versões anteriores são aplicadas durante a inicialização quando necessário.

---

# Estrutura principal

```text
sapia/
├── backend/
│   ├── app/
│   │   ├── auth.py
│   │   ├── database.py
│   │   ├── email_service.py
│   │   ├── main.py
│   │   ├── models.py
│   │   └── schemas.py
│   ├── .env.example
│   └── requirements.txt
│
└── frontend/
    ├── src/
    │   ├── pages/
    │   │   ├── Login.tsx
    │   │   ├── Register.tsx
    │   │   └── Home.tsx
    │   ├── components/
    │   │   └── Sidebar.tsx
    │   ├── api.ts
    │   ├── App.tsx
    │   ├── index.css
    │   └── main.tsx
    ├── package.json
    ├── tsconfig.json
    └── vite.config.ts
```

---

# Endpoints existentes

## GET /health

Verifica se o backend está ativo.

---

## POST /auth/register

Realiza o cadastro de um novo usuário.

Exemplo:

```json
{
  "name": "Usuario Teste",
  "email": "usuario@exemplo.com",
  "password": "Teste@123",
  "password_confirmation": "Teste@123"
}
```

O usuário é inicialmente criado com:

```text
status = PENDENTE
```

Um token de confirmação é gerado e enviado por e-mail.

---

## GET /auth/confirm

Confirma a conta utilizando o token recebido por e-mail.

Exemplo:

```text
/auth/confirm?token=<token>
```

Após uma confirmação válida:

```text
status = ATIVO
token = utilizado
confirmed_at = data/hora da confirmação
```

O mesmo token não pode ser utilizado novamente.

---

## POST /auth/login

Autentica o usuário.

Exemplo:

```json
{
  "email": "admin@sapia.com",
  "password": "Sapia@123"
}
```

Uma conta ainda não confirmada não pode realizar login.

---

## GET /auth/me

Retorna o usuário autenticado.

Requer:

```text
Authorization: Bearer <token>
```

---

## POST /auth/logout

Invalida a sessão atual.

---

# Observações de segurança

Nunca enviar ao Git:

```text
backend/.env
backend/sapia_demo.db
backend/.venv/
frontend/node_modules/
```

Nunca incluir senhas de aplicativo, senhas pessoais ou tokens de sessão em commits.

O arquivo:

```text
backend/.env.example
```

deve conter somente exemplos e nomes das variáveis.

---

# Próximas etapas

A continuidade do projeto poderá incluir:

1. Upload real de PDF;
2. Persistência e gerenciamento de documentos;
3. Extração de dados do documento;
4. Processamento por IA;
5. Revisão dos dados extraídos;
6. Geração da petição;
7. Exportação;
8. Histórico de documentos.
