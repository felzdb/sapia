# SAPIA — Protótipo funcional

Protótipo do SAPIA — Sistema de Automação de Petição Inicial para Aposentadoria.

Funcionalidades atualmente disponíveis:

- Interface web;
- Cadastro de usuários;
- Confirmação de cadastro por e-mail;
- Login e controle de acesso;
- Backend FastAPI;
- Banco SQLite;
- Sessões por token mantidas em memória;
- Tela inicial do sistema;
- Upload de documentos PDF do INSS;
- Leitura e análise do conteúdo do documento;
- Análise documental assistida por IA com Google Gemini;
- Extração dos dados pessoais e previdenciários do cliente;
- Identificação automática do tipo de benefício;
- Correção manual do benefício identificado;
- Conferência e correção manual dos dados extraídos;
- Validação de CPF por dígitos verificadores;
- Geração automática da petição inicial conforme o tipo de benefício;
- Pré-visualização e finalização da petição;
- Indicadores visuais das etapas de processamento.

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
GEMINI_API_KEY=sua_chave_da_api_gemini
```

### Importante

O arquivo `.env` contém credenciais e não deve ser enviado ao Git.

Ele já está incluído no `.gitignore`.

Para Gmail, utilize uma **senha de aplicativo**, e não a senha normal da conta Google.

Para gerar uma senha de aplicativo no Google, a verificação em duas etapas da conta deve estar ativada.

Nunca coloque credenciais reais dentro do `.env.example`.

Para utilizar a análise documental assistida por IA, informe uma chave válida da API do Google Gemini na variável `GEMINI_API_KEY`.

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

# RF7 — Geração Automática da Petição Inicial

A implementação permite:

- Utilizar os dados extraídos do documento e conferidos pelo usuário;
- Utilizar o tipo de benefício identificado para selecionar o conteúdo da petição;
- Exigir confirmação dos dados antes da geração;
- Gerar automaticamente a petição inicial com partes fixas e variáveis;
- Gerar a estrutura jurídica com:
  - endereçamento;
  - qualificação;
  - dos fatos;
  - do direito;
  - dos pedidos;
  - valor da causa;
- Adaptar o conteúdo da petição ao tipo de benefício identificado;
- Exibir a petição gerada para pré-visualização antes da finalização;
- Salvar a petição no banco de dados vinculada ao documento;
- Permitir a finalização da petição;
- Atualizar visualmente as etapas do fluxo no painel.

## Fluxo de teste

1. Faça login no sistema.

2. Envie um documento PDF do INSS.

3. Aguarde a análise do documento e a extração dos dados.

4. Confira os dados extraídos e faça correções manuais, se necessário.

5. Confirme que os dados foram conferidos.

6. Clique em **Gerar petição**.

7. Confira o conteúdo na pré-visualização.

8. Clique em **Finalizar petição**.

A petição é registrada no banco de dados com seu conteúdo, status e vínculo ao documento processado durante a execução atual do backend.

### Observação

A geração e a pré-visualização da petição estão implementadas no protótipo.

A formatação específica conforme o tribunal de destino ainda depende da definição e disponibilização dessas informações no fluxo do sistema.

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

O banco é criado automaticamente durante a inicialização do backend.

Na configuração atual do protótipo, o banco local é recriado quando o backend é iniciado.

O arquivo `.db` está ignorado pelo Git, portanto cada desenvolvedor possui seu próprio banco local.

---

# Estrutura principal

```text
sapia/
├── backend/
│   ├── app/
│   │   ├── auth.py
│   │   ├── benefit_identifier.py
│   │   ├── client_data.py
│   │   ├── database.py
│   │   ├── documents.py
│   │   ├── email_service.py
│   │   ├── gemini_service.py
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── pdf_reader.py
│   │   ├── petition_generator.py
│   │   ├── schemas.py
│   │   ├── storage.py
│   │   └── __init__.py
│   ├── .env.example
│   └── requirements.txt
│
└── frontend/
    ├── src/
    │   ├── pages/
    │   │   ├── ForgotPassword.tsx
    │   │   ├── Home.tsx
    │   │   ├── Login.tsx
    │   │   ├── Register.tsx
    │   │   └── ResetPassword.tsx
    │   ├── components/
    │   │   ├── Sidebar.tsx
    │   │   └── UploadArea.tsx
    │   ├── api.ts
    │   ├── App.tsx
    │   ├── index.css
    │   ├── main.tsx
    │   └── vite-env.d.ts
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

## POST /auth/forgot-password

Solicita a recuperação de senha por e-mail.

---

## POST /auth/reset-password

Redefine a senha utilizando o token de recuperação recebido por e-mail.

---

# Endpoints de documentos

As rotas abaixo exigem usuário autenticado.

## POST /documents/upload

Realiza o upload do documento PDF do INSS para processamento e análise.

O documento é associado ao usuário autenticado.

---

## PATCH /documents/{document_id}/benefit

Permite corrigir manualmente o tipo de benefício identificado para o documento.

---

## POST /documents/{document_id}/petition

Gera a petição inicial com base:

- no documento processado;
- no tipo de benefício identificado;
- nos dados do cliente conferidos pelo usuário.

A petição gerada é registrada no banco de dados e vinculada ao documento.

---

## PATCH /documents/{document_id}/petition/finalize

Finaliza a petição previamente gerada, atualizando seu status no sistema.

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

1. Suporte completo a documentos escaneados por OCR;
2. Banco de cláusulas configurável e versionado;
3. Formatação da petição conforme o tribunal de destino;
4. Exportação da petição nos formatos Word e PDF;
5. Histórico de documentos e petições geradas;
6. Persistência durável dos dados e documentos entre reinicializações do backend.
