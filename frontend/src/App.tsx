import { FormEvent, useEffect, useState } from "react";
import {
  ArrowRight,
  CheckCircle2,
  FileClock,
  FileText,
  History,
  LogOut,
  Scale,
  ShieldCheck,
  Sparkles,
  UploadCloud,
} from "lucide-react";

import { getMe, login, logout, type User } from "./api";

const TOKEN_KEY = "sapia_token";

function LoginScreen({
  onAuthenticated,
}: {
  onAuthenticated: (user: User, token: string) => void;
}) {
  const [email, setEmail] = useState("admin@sapia.com");
  const [password, setPassword] = useState("Sapia@123");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setLoading(true);

    try {
      const result = await login(email, password);
      onAuthenticated(result.user, result.access_token);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao autenticar.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-brand-panel">
        <div className="brand-lockup">
          <div className="brand-icon">
            <Scale size={30} />
          </div>
          <div>
            <span className="brand-name">SAPIA</span>
            <span className="brand-subtitle">Tecnologia aplicada ao jurídico</span>
          </div>
        </div>

        <div className="hero-copy">
          <span className="eyebrow">Protótipo funcional</span>
          <h1>Automação inteligente para petições previdenciárias.</h1>
          <p>
            Centralize o envio do documento, a leitura automatizada e a geração
            da petição inicial em um único fluxo.
          </p>
        </div>

        <div className="feature-list">
          <div className="feature-row">
            <Sparkles size={20} />
            <span>Extração assistida por IA</span>
          </div>
          <div className="feature-row">
            <ShieldCheck size={20} />
            <span>Conferência antes da geração</span>
          </div>
          <div className="feature-row">
            <FileText size={20} />
            <span>Exportação estruturada de documentos</span>
          </div>
        </div>

        <div className="auth-footer">
          SAPIA · Sistema de Automação de Petição Inicial para Aposentadoria
        </div>
      </section>

      <section className="auth-form-panel">
        <div className="login-card">
          <div className="login-heading">
            <span className="status-pill">
              <span className="status-dot" />
              Ambiente demonstrativo
            </span>
            <h2>Acesse o SAPIA</h2>
            <p>Utilize as credenciais demonstrativas para entrar no sistema.</p>
          </div>

          <form onSubmit={handleSubmit}>
            <label>
              E-mail
              <input
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                type="email"
                autoComplete="email"
                required
              />
            </label>

            <label>
              Senha
              <input
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                type="password"
                autoComplete="current-password"
                required
              />
            </label>

            {error && <div className="error-box">{error}</div>}

            <button className="primary-button" type="submit" disabled={loading}>
              {loading ? "Entrando..." : "Entrar"}
              {!loading && <ArrowRight size={18} />}
            </button>
          </form>

          <div className="demo-credentials">
            <strong>Credenciais do protótipo</strong>
            <span>admin@sapia.com · Sapia@123</span>
          </div>
        </div>
      </section>
    </main>
  );
}

function Dashboard({
  user,
  token,
  onLogout,
}: {
  user: User;
  token: string;
  onLogout: () => void;
}) {
  async function handleLogout() {
    await logout(token);
    onLogout();
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="sidebar-logo">
            <Scale size={22} />
          </div>
          <div>
            <strong>SAPIA</strong>
          </div>
        </div>

        <nav className="nav-list">
          <button className="nav-item active">
            <UploadCloud size={19} />
            Enviar documento
          </button>
          <button className="nav-item">
            <History size={19} />
            Histórico
          </button>
        </nav>

        <div className="sidebar-bottom">
          <div className="user-mini-card">
            <div className="avatar">{user.name.charAt(0)}</div>
            <div>
              <strong>{user.name}</strong>
              <span>{user.role}</span>
            </div>
          </div>
          <button className="logout-button" onClick={handleLogout}>
            <LogOut size={18} />
            Sair
          </button>
        </div>
      </aside>

      <main className="dashboard">
        <header className="dashboard-header">
          <div>
            <span className="eyebrow">Painel principal</span>
            <h1>Olá, {user.name.split(" ")[0]}</h1>
            <p>Envie um documento do INSS para iniciar uma nova análise.</p>
          </div>
          <div className="environment-badge">
            <span className="status-dot" />
            Backend conectado
          </div>
        </header>

        <section className="metrics-grid">
          <article className="metric-card">
            <div className="metric-icon">
              <FileText size={21} />
            </div>
            <div>
              <span>Documentos processados</span>
              <strong>0</strong>
            </div>
          </article>

          <article className="metric-card">
            <div className="metric-icon">
              <FileClock size={21} />
            </div>
            <div>
              <span>Em processamento</span>
              <strong>0</strong>
            </div>
          </article>

          <article className="metric-card">
            <div className="metric-icon">
              <CheckCircle2 size={21} />
            </div>
            <div>
              <span>Petições geradas</span>
              <strong>0</strong>
            </div>
          </article>
        </section>

        <section className="workspace-card">
          <div className="workspace-heading">
            <div>
              <span className="eyebrow">Nova análise</span>
              <h2>Enviar documento do INSS</h2>
              <p>
                Nesta primeira versão, o componente visual já está pronto. O
                endpoint de upload será conectado na próxima etapa.
              </p>
            </div>
          </div>

          <button className="dropzone" type="button">
            <div className="dropzone-icon">
              <UploadCloud size={30} />
            </div>
            <strong>Arraste o PDF aqui ou clique para selecionar</strong>
            <span>PDF de até 20 MB</span>
          </button>

          <div className="flow-steps">
            <div className="flow-step active">
              <span>01</span>
              <div>
                <strong>Enviar PDF</strong>
                <small>Documento do INSS</small>
              </div>
            </div>
            <div className="flow-line" />
            <div className="flow-step">
              <span>02</span>
              <div>
                <strong>Analisar</strong>
                <small>Extração de dados</small>
              </div>
            </div>
            <div className="flow-line" />
            <div className="flow-step">
              <span>03</span>
              <div>
                <strong>Conferir</strong>
                <small>Validação humana</small>
              </div>
            </div>
            <div className="flow-line" />
            <div className="flow-step">
              <span>04</span>
              <div>
                <strong>Gerar</strong>
                <small>Petição inicial</small>
              </div>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}

export default function App() {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(() =>
    localStorage.getItem(TOKEN_KEY)
  );
  const [booting, setBooting] = useState(Boolean(token));

  useEffect(() => {
    if (!token) {
      setBooting(false);
      return;
    }

    getMe(token)
      .then(setUser)
      .catch(() => {
        localStorage.removeItem(TOKEN_KEY);
        setToken(null);
      })
      .finally(() => setBooting(false));
  }, [token]);

  if (booting) {
    return (
      <div className="loading-screen">
        <div className="loading-logo">
          <Scale size={28} />
        </div>
        <span>Carregando SAPIA...</span>
      </div>
    );
  }

  if (!user || !token) {
    return (
      <LoginScreen
        onAuthenticated={(user, token) => {
          localStorage.setItem(TOKEN_KEY, token);
          setToken(token);
          setUser(user);
        }}
      />
    );
  }

  return (
    <Dashboard
      user={user}
      token={token}
      onLogout={() => {
        localStorage.removeItem(TOKEN_KEY);
        setUser(null);
        setToken(null);
      }}
    />
  );
}
