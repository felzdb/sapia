import { FormEvent, useState } from "react";
import {
    ArrowRight,
    FileText,
    Scale,
    ShieldCheck,
    Sparkles,
} from "lucide-react";

import { login, type User } from "../api";

type LoginProps = {
    onAuthenticated: (user: User, token: string) => void;
};

export default function Login({ onAuthenticated }: LoginProps) {
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

            onAuthenticated(
                result.user,
                result.access_token
            );
        } catch (err) {
            setError(
                err instanceof Error
                    ? err.message
                    : "Falha ao autenticar."
            );
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