# SAPIA — Protótipo inicial

Primeira versão funcional do protótipo do SAPIA, focada em:

- Interface web apresentável;
- Login de usuário;
- Backend FastAPI;
- Banco SQLite temporário, recriado a cada inicialização;
- Sessão por token mantida em memória;
- Tela inicial do sistema com área de upload ainda não conectada ao processamento de documentos.

## Rodando o projeto pela primeira vez

Abaixo deixo a listagem de comandos que uso para inicialização do projeto no MacOS, talvez seja necessário adaptar algo se estiver rodando no Windows:

Frontend:
cd frontend
npm install
npm run dev

Backend:
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

O Frontend e o Backend devem permanecer rodando simultaneamente, utilize dois terminais.

## Preciso rodar todos esses comandos sempre?

Não. A criação do ambiente virtual e a instalação das dependências são
necessárias apenas na primeira execução ou quando as dependências do projeto
forem alteradas.

Frontend:
cd frontend
npm run dev

Backend:
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000

## Credenciais de demonstração

- E-mail: `admin@sapia.com`
- Senha: `Sapia@123`

## Estrutura

```text
sapia-prototype/
├── backend/
│   ├── app/
│   │   ├── auth.py
│   │   ├── database.py
│   │   ├── main.py
│   │   ├── models.py
│   │   └── schemas.py
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── api.ts
    │   ├── App.tsx
    │   ├── index.css
    │   └── main.tsx
    ├── index.html
    ├── package.json
    ├── tsconfig.json
    └── vite.config.ts
```

## Backend

Requer Python 3.11+.

```bash
cd backend
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Instale:

```bash
pip install -r requirements.txt
```

Execute:

```bash
uvicorn app.main:app --reload --port 8000
```

A API ficará em:

```text
http://localhost:8000
```

Documentação Swagger:

```text
http://localhost:8000/docs
```

## Frontend

Requer Node.js 20+.

```bash
cd frontend
npm install
npm run dev
```

A aplicação ficará normalmente em:

```text
http://localhost:5173
```

## Banco temporário

O arquivo `sapia_demo.db` é recriado toda vez que o backend é iniciado.
Isso significa que os dados do protótipo não são persistentes entre execuções.

O usuário demonstrativo é inserido automaticamente no startup.

## Endpoints existentes

### GET /health

Verifica se o backend está ativo.

### POST /auth/login

Autentica usuário.

Exemplo:

```json
{
  "email": "admin@sapia.com",
  "password": "Sapia@123"
}
```

### GET /auth/me

Retorna o usuário autenticado.

Requer:

```text
Authorization: Bearer <token>
```

### POST /auth/logout

Invalida o token atual.

## Próxima etapa sugerida

1. Upload real de PDF;
2. Criação da tabela DOCUMENTO;
3. Extração de texto com PyMuPDF;
4. Tela de revisão dos dados extraídos;
5. Integração com LLM;
6. Geração de DOCX com docxtpl.
