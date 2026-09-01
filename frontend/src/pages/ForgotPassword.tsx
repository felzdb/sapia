import { FormEvent, useState } from "react";
import {
    ArrowLeft,
    ArrowRight,
    FileText,
    Scale,
    ShieldCheck,
    Sparkles,
} from "lucide-react";

import { forgotPassword } from "../api";

type ForgotPasswordProps = {
    onBackToLogin: () => void;
};

export default function ForgotPassword({
    onBackToLogin,
}: ForgotPasswordProps) {
    const [email, setEmail] = useState("");
    const [error, setError] = useState("");
    const [success, setSuccess] = useState("");
    const [loading, setLoading] = useState(false);

    async function handleSubmit(event: FormEvent) {
        event.preventDefault();

        setError("");
        setSuccess("");

        if (!email.trim()) {
            setError("Informe seu endereço de e-mail.");
            return;
        }

        setLoading(true);

        try {
            const result = await forgotPassword(email);
            setSuccess(result.message);
        } catch (err) {
            setError(
                err instanceof Error
                    ? err.message
                    : "Falha ao solicitar recuperação de senha."
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
                        <h2>Recuperar senha</h2>

                        <p>
                            Informe seu e-mail para receber o link de recuperação.
                        </p>
                    </div>

                    <form onSubmit={handleSubmit} noValidate>
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

                        {error && <div className="error-box">{error}</div>}

                        {success && (
                            <div className="demo-credentials">
                                {success}
                            </div>
                        )}

                        <button
                            className={`primary-button${success ? " completed-button" : ""}`}
                            type="submit"
                            disabled={loading || Boolean(success)}
>
                            {loading
                                ? "Enviando..."
                                : success
                                    ? "Link enviado"
                                    : "Enviar link"}

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