import { useEffect, useState } from "react";
import {
  deletePetitionHistory,
  exportPetition,
  exportPetitionHistoryVersion,
  getPetitionHistoryVersions,
  getPetitionHistory,
  getPetitionHistoryDetail,
  type PetitionHistoryDetail,
  type PetitionHistoryItem,
  type PetitionHistoryVersion,
} from "../api";

type Props = { token: string; isAdmin: boolean };

function formatDateTimeBrazil(value: string): string {
  // The backend stores the Brazilian local wall-clock time without a timezone.
  // Display its components as-is to avoid browser timezone shifts.
  const match = value.match(/^(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2})(?::(\d{2}))?/);
  if (!match) return value;
  const [, year, month, day, hour, minute, second = "00"] = match;
  return `${day}/${month}/${year}, ${hour}:${minute}:${second}`;
}

export default function HistoryPage({ token, isAdmin }: Props) {
  const [items, setItems] = useState<PetitionHistoryItem[]>([]);
  const [clientName, setClientName] = useState("");
  const [cpf, setCpf] = useState("");
  const [benefitType, setBenefitType] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [detail, setDetail] = useState<PetitionHistoryDetail | null>(null);
  const [versions, setVersions] = useState<PetitionHistoryVersion[]>([]);
  const [versionsLoading, setVersionsLoading] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [busyId, setBusyId] = useState<number | null>(null);

  async function loadHistory() {
    setLoading(true);
    setError("");
    try {
      const data = await getPetitionHistory(token, {
        client_name: clientName,
        cpf,
        benefit_type: benefitType,
        start_date: startDate ? `${startDate}T00:00:00` : undefined,
        end_date: endDate ? `${endDate}T23:59:59` : undefined,
      });
      setItems(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Não foi possível carregar o histórico.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { void loadHistory(); }, []);

  async function openDetail(item: PetitionHistoryItem) {
    try {
      setDetail(await getPetitionHistoryDetail(token, item.petition_id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Não foi possível abrir a petição.");
    }
  }

  async function removeItem(item: PetitionHistoryItem) {
    if (!window.confirm(`Deseja realmente excluir a petição de ${item.client_name}? A ação será registrada.`)) return;
    setBusyId(item.petition_id);
    try {
      await deletePetitionHistory(token, item.petition_id);
      setItems(current => current.filter(row => row.petition_id !== item.petition_id));
      if (detail?.petition_id === item.petition_id) setDetail(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Não foi possível excluir a petição.");
    } finally {
      setBusyId(null);
    }
  }

  const fieldStyle: React.CSSProperties = {
    width: "100%", padding: "10px 12px", border: "1px solid #d7dce5",
    borderRadius: 8, background: "#fff", color: "#1f2937",
  };

  return (
    <section className="workspace-card">
      <div className="workspace-heading">
        <div>
          <span className="eyebrow">Documentos gerados</span>
          <h2>Histórico de petições</h2>
          <p>Consulte, visualize e exporte novamente as petições já geradas.</p>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))", gap: 12, margin: "20px 0" }}>
        <input aria-label="Nome do cliente" placeholder="Nome do cliente" value={clientName} onChange={e => setClientName(e.target.value)} style={fieldStyle} />
        <input aria-label="CPF" placeholder="CPF" value={cpf} onChange={e => setCpf(e.target.value)} style={fieldStyle} />
        <input aria-label="Tipo de benefício" placeholder="Tipo de benefício" value={benefitType} onChange={e => setBenefitType(e.target.value)} style={fieldStyle} />
        <label style={{ fontSize: 12, color: "#5b6474" }}>De<input type="date" value={startDate} onChange={e => setStartDate(e.target.value)} style={fieldStyle} /></label>
        <label style={{ fontSize: 12, color: "#5b6474" }}>Até<input type="date" value={endDate} onChange={e => setEndDate(e.target.value)} style={fieldStyle} /></label>
        <button className="primary-button" onClick={() => void loadHistory()} disabled={loading}>Pesquisar</button>
      </div>

      {error && <p role="alert" style={{ color: "#b42318" }}>{error}</p>}
      {loading ? <p>Carregando histórico...</p> : items.length === 0 ? <p>Nenhuma petição encontrada para os filtros informados.</p> : (
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left" }}>
            <thead><tr>
              <th style={{ padding: 12 }}>Cliente</th>
              <th style={{ padding: 12 }}>CPF</th>
              <th style={{ padding: 12 }}>Benefício</th>
              <th style={{ padding: 12 }}>Geração</th>
              <th style={{ padding: 12 }}>Status</th>
              {isAdmin && <th style={{ padding: 12 }}>Responsável</th>}
              <th style={{ padding: 12 }}>Ações</th>
            </tr></thead>
            <tbody>{items.map(item => (
              <tr key={item.petition_id} style={{ borderTop: "1px solid #e5e7eb" }}>
                <td style={{ padding: 12 }}>{item.client_name}</td>
                <td style={{ padding: 12 }}>{item.cpf ?? "—"}</td>
                <td style={{ padding: 12 }}>{item.benefit_type ?? "—"}</td>
                <td style={{ padding: 12 }}>{formatDateTimeBrazil(item.generated_at)}</td>
                <td style={{ padding: 12 }}>{item.status}</td>
                {isAdmin && <td style={{ padding: 12 }}>{item.owner_name ?? "—"}</td>}
                <td style={{ padding: 12, whiteSpace: "nowrap" }}>
                  <button onClick={() => void openDetail(item)}>Visualizar</button>{" "}
                  <button onClick={() => void exportPetition(token, item.document_id, "pdf")}>PDF</button>{" "}
                  <button onClick={() => void exportPetition(token, item.document_id, "docx")}>Word</button>{" "}
                  <button disabled={busyId === item.petition_id} onClick={() => void removeItem(item)}>Excluir</button>
                </td>
              </tr>
            ))}</tbody>
          </table>
        </div>
      )}

      {detail && (
        <div role="dialog" aria-modal="true" aria-label="Visualização da petição" style={{ position: "fixed", inset: 0, background: "rgba(15,23,42,.55)", zIndex: 1000, display: "grid", placeItems: "center", padding: 20 }}>
          <div style={{ background: "#fff", borderRadius: 12, width: "min(900px, 100%)", maxHeight: "85vh", overflow: "auto", padding: 24 }}>
            <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "center" }}>
              <h2>Petição — {detail.client_name}</h2>
              <button onClick={() => { setDetail(null); setVersions([]); }}>Fechar</button>
            </div>
            <h3>Versões salvas</h3>
            {versionsLoading ? <p>Carregando versões...</p> : versions.length === 0 ? <p>Nenhuma versão anterior foi registrada para esta petição.</p> : (
              <div style={{ display: "grid", gap: 8, marginBottom: 20 }}>
                {versions.map((version, index) => (
                  <div key={version.version_id} style={{ display: "flex", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between", gap: 8, border: "1px solid #e5e7eb", borderRadius: 8, padding: 12 }}>
                    <span>Versão {versions.length - index} — {formatDateTimeBrazil(version.created_at)}</span>
                    <span>
                      <button onClick={() => setDetail({ ...detail, content: version.content })}>Visualizar versão</button>{" "}
                      <button onClick={() => void exportPetitionHistoryVersion(token, detail.petition_id, version.version_id, "pdf")}>PDF</button>{" "}
                      <button onClick={() => void exportPetitionHistoryVersion(token, detail.petition_id, version.version_id, "docx")}>Word</button>
                    </span>
                  </div>
                ))}
              </div>
            )}
            <h3>Conteúdo da petição selecionada</h3>
            <pre style={{ whiteSpace: "pre-wrap", fontFamily: "inherit", lineHeight: 1.6 }}>{detail.content}</pre>
          </div>
        </div>
      )}
    </section>
  );
}
