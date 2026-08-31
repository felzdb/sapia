import { FormEvent, useState } from "react";
import {
    ArrowLeft,
    ArrowRight,
    FileText,
    Scale,
    ShieldCheck,
    Sparkles,
} from "lucide-react";

import { register } from "../api";

type RegisterProps = {
    onBackToLogin: () => void;
};

export default function Register({ onBackToLogin }: RegisterProps) {
    const [name, setName] = useState("");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [passwordConfirmation, setPasswordConfirmation] = useState("");
    const [error, setError] = useState("");
    const [success, setSuccess] = useState("");
    const [loading, setLoading] = useState(false);

    async function handleSubmit(event: FormEvent) {
        event.preventDefault();

        setError("");
        setSuccess("");

        if (
            !name.trim() ||
            !email.trim() ||
            !password ||
            !passwordConfirmation
        ) {
            setError(
                "Campos obrigatórios não preenchidos. Verifique os dados e tente novamente."
            );
            return;
        }

        setLoading(true);

        try {
            await register(
                name,
                email,
                password,
                passwordConfirmation
            );

            setSuccess(
                "Cadastro realizado. Verifique seu e-mail para confirmar sua conta."
            );
        } catch (err) {
            setError(
                err instanceof Error
                    ? err.message
                    : "Falha ao realizar cadastro."
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
                        <span className="brand-subtitle">
                            Tecnologia aplicada ao jurídico
                        </span>
                    </div>
                </div>

                <div className="hero-copy">
                    <span className="eyebrow">Protótipo funcional</span>

                    <h1>
                        Automação inteligente para petições previdenciárias.
                    </h1>

                    <p>
                        Centralize o envio do documento, a leitura automatizada
                        e a geração da petição inicial em um único fluxo.
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
                            Novo usuário
                        </span>

                        <h2>Crie sua conta</h2>

                        <p>
                            Preencha seus dados para acessar o SAPIA.
                        </p>
                    </div>

                    <form onSubmit={handleSubmit} noValidate>
                        <label>
                            Nome completo
                            <input
                                value={name}
                                onChange={(event) => setName(event.target.value)}
                                type="text"
                                autoComplete="name"
                                required
                            />
                        </label>

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
                                autoComplete="new-password"
                                required
                            />
                        </label>

                        <label>
                            Repita a senha
                            <input
                                value={passwordConfirmation}
                                onChange={(event) =>
                                    setPasswordConfirmation(event.target.value)
                                }
                                type="password"
                                autoComplete="new-password"
                                required
                            />
                        </label>

                        {error && <div className="error-box">{error}</div>}

                        {success && (
                            <div className="demo-credentials">
                                {success}
                            </div>
                        )}

                        <button
                            className="primary-button"
                            type="submit"
                            disabled={loading || Boolean(success)}
                        >
                            {loading ? "Cadastrando..." : "Cadastrar"}
                            {!loading && !success && <ArrowRight size={18} />}
                        </button>

                        <button
                            className="secondary-button"
                            type="button"
                            onClick={onBackToLogin}
                        >
                            <ArrowLeft size={16} />
                            Voltar para o login
                        </button>
                    </form>
                </div>
            </section>
        </main>
    );
}