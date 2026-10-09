import { useState } from "react";

import {
    CheckCircle2,
    FileClock,
    FileText,
    History,
    LogOut,
    Scale,
    UploadCloud,
} from "lucide-react";

import { logout, type User } from "../api";
import Sidebar from "../components/Sidebar";
import UploadArea from "../components/UploadArea";

type HomeProps = {
    user: User;
    token: string;
    onLogout: () => void;
};

export default function Home({
    user,
    token,
    onLogout,
}: HomeProps) {

    const [processedDocuments, setProcessedDocuments] =
    useState(0);

    const [processingDocuments, setProcessingDocuments] =
    useState(0);

    const [generatedPetitions, setGeneratedPetitions] =
    useState(0);

    const flowStep =
    generatedPetitions > 0
        ? 4
        : processedDocuments > 0
          ? 3
          : processingDocuments > 0
            ? 2
            : 1;

    async function handleLogout() {
        await logout(token);
        onLogout();
    }

    return (
        <div className="app-shell">
            <Sidebar
                user={user}
                onLogout={handleLogout}
            />
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
                            <strong>{processedDocuments}</strong>
                        </div>
                    </article>

                    <article className="metric-card">
                        <div className="metric-icon">
                            <FileClock size={21} />
                        </div>
                        <div>
                            <span>Em processamento</span>
                            <strong>{processingDocuments}</strong>
                        </div>
                    </article>

                    <article className="metric-card">
                        <div className="metric-icon">
                            <CheckCircle2 size={21} />
                        </div>
                        <div>
                            <span>Petições geradas</span>
                            <strong>{generatedPetitions}</strong>
                        </div>
                    </article>
                </section>

                <section className="workspace-card">
                    <div className="workspace-heading">
                        <div>
                            <span className="eyebrow">Nova análise</span>
                            <h2>Enviar documento do INSS</h2>
                            <p>
                                Envie um documento do INSS para análise automática e conferência dos dados extraídos.
                            </p>
                        </div>
                    </div>

                    <UploadArea
                        token={token}
                        onProcessingChange={(processing) =>
                            setProcessingDocuments(processing ? 1 : 0)
                        }
                        onDocumentProcessed={() =>
                            setProcessedDocuments((current) => current + 1)
                        }
                        onPetitionGenerated={() =>
                            setGeneratedPetitions((current) => current + 1)
                        }
                    />

                    <div className="flow-steps">
                        <div className={`flow-step ${flowStep > 1 ? "completed" : "active"}`}>
                            <span>01</span>
                            <div>
                                <strong>Enviar PDF</strong>
                                <small>Documento do INSS</small>
                            </div>
                        </div>
                        <div className="flow-line" />
                        <div
                            className={`flow-step ${
                                flowStep > 2
                                    ? "completed"
                                    : flowStep === 2
                                    ? "active"
                                    : ""
                            }`}
                        >
                            <span>02</span>
                            <div>
                                <strong>Analisar</strong>
                                <small>Extração de dados</small>
                            </div>
                        </div>
                        <div className="flow-line" />
                        <div
                            className={`flow-step ${
                                flowStep > 3
                                    ? "completed"
                                    : flowStep === 3
                                    ? "active"
                                    : ""
                            }`}
                        >
                            <span>03</span>
                            <div>
                                <strong>Conferir</strong>
                                <small>Validação humana</small>
                            </div>
                        </div>
                        <div className="flow-line" />
                        <div
                            className={`flow-step ${
                                flowStep === 4 ? "completed" : ""
                            }`}
                        >
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