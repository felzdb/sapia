import { useEffect, useState } from "react";
import { clauseRequest, type Clause, type ClauseOptions } from "../api";

type Draft = {title: string; text: string; section: string; benefit_types: string[]; conditions: Record<string, boolean>; display_order: number};
const empty: Draft = {title: "", text: "", section: "direito", benefit_types: [], conditions: {}, display_order: 0};
const sectionLabels: Record<string, string> = {fatos: "Dos fatos", direito: "Do direito", pedidos: "Dos pedidos"};
export default function ClauseManager({token}: {token: string}) {
  const [clauses, setClauses] = useState<Clause[]>([]);
  const [options, setOptions] = useState<ClauseOptions | null>(null);
  const [draft, setDraft] = useState<Draft>(empty);
  const [editing, setEditing] = useState<Clause | null>(null);
  const [history, setHistory] = useState<Clause[]>([]);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  async function load() { setClauses(await clauseRequest<Clause[]>(token)); }
  useEffect(() => {
    Promise.all([clauseRequest<ClauseOptions>(token, "/options"), clauseRequest<Clause[]>(token)])
      .then(([o, c]) => {setOptions(o); setClauses(c);}).catch(e => setMessage(e.message));
  }, [token]);
  async function action(run: () => Promise<void>) {
    setBusy(true); setMessage("");
    try { await run(); } catch(e) { setMessage(e instanceof Error ? e.message : "Falha na operação."); }
    finally { setBusy(false); }
  }
  return <section className="workspace-card clause-manager">
    <h2>Banco de cláusulas</h2>
    <p>Cadastre os textos e as condições de inclusão. Cada edição cria uma nova versão; a exclusão preserva o histórico.</p>
    {message && <p role="alert">{message}</p>}
    <form onSubmit={e => {e.preventDefault(); void action(async () => {
      await clauseRequest(token, editing ? `/${editing.id}` : "", editing ? "PUT" : "POST",
        {...draft, ...(editing ? {expected_version: editing.version} : {})});
      setEditing(null); setDraft(empty); await load(); setMessage("Cláusula salva.");
    });}}>
      <h3>{editing ? `Editar cláusula ${editing.id} — versão ${editing.version}` : "Nova cláusula"}</h3>
      <label>Título<input required maxLength={255} value={draft.title} onChange={e => setDraft({...draft, title: e.target.value})}/></label>
      <label>Texto<textarea required rows={7} maxLength={30000} value={draft.text} onChange={e => setDraft({...draft, text: e.target.value})}/></label>
      <details className="clause-help">
        <summary>Como inserir dados do cliente</summary>
        <p>Use os marcadores no texto da cláusula. O sistema os substituirá pelos dados do cliente ao gerar a petição.</p>
        <p>{options?.placeholders.map((campo) => `\${${campo}}`).join(", ")}</p>
        <p>Para escrever um cifrão no texto final, use <code>$$</code>.</p>
      </details>
      <div className="clause-grid">
        <label>Seção<select value={draft.section} onChange={e => setDraft({...draft, section: e.target.value})}>
          {options?.sections.map(s => <option key={s} value={s}>{sectionLabels[s]}</option>)}</select></label>
        <label>Ordem<input type="number" required min={0} max={10000} value={draft.display_order} onChange={e => setDraft({...draft, display_order: Number(e.target.value)})}/></label>
      </div>
      <fieldset className="benefits-fieldset">
        <legend>Benefícios vinculados — selecione pelo menos um</legend>
        <div className="benefits-options">
          {options?.benefit_types.map((benefit) => (
            <label className="clause-check" key={benefit}>
              <input
                type="checkbox"
                checked={draft.benefit_types.includes(benefit)}
                onChange={(event) => setDraft({
                  ...draft,
                  benefit_types: event.target.checked
                    ? [...draft.benefit_types, benefit]
                    : draft.benefit_types.filter((value) => value !== benefit),
                })}
              />
              <span>{benefit.replace(/_/g, " ")}</span>
            </label>
          ))}
        </div>
      </fieldset>
      <fieldset><legend>Condições — todas as condições escolhidas devem ser atendidas</legend>
        {Object.entries(options?.case_fields ?? {}).map(([key, title]) => <label key={key}>{title}
          <select value={key in draft.conditions ? String(draft.conditions[key]) : ""} onChange={e => {
            const conditions = {...draft.conditions};
            if(e.target.value === "") delete conditions[key]; else conditions[key] = e.target.value === "true";
            setDraft({...draft, conditions});
          }}><option value="">Não depende desta condição</option><option value="true">Exige sim</option><option value="false">Exige não</option></select>
        </label>)}
      </fieldset>
      <button className="primary-button" disabled={busy || !draft.benefit_types.length}>Salvar cláusula</button>
      {editing && <button type="button" disabled={busy} onClick={() => {setEditing(null); setDraft(empty);}}>Cancelar edição</button>}
    </form>
    <h3>Cláusulas cadastradas</h3>
    {!clauses.length && <p>Nenhuma cláusula cadastrada. Adicione os textos antes de gerar uma petição.</p>}
    {clauses.map(c => <article className="clause-record" key={c.id}>
      <h4>{c.title} · v{c.version} {c.active ? "" : "· Excluída"}</h4>
      <p>{sectionLabels[c.section]} · Ordem {c.display_order} · {c.benefit_types.join(", ")}</p>
      <p>{Object.entries(c.conditions).map(([k,v]) => `${options?.case_fields[k] ?? k}: ${v ? "sim" : "não"}`).join("; ") || "Sem condições adicionais"}</p>
      <pre>{c.text}</pre>
      {c.active && <><button disabled={busy} onClick={() => {setEditing(c); setDraft({title:c.title,text:c.text,section:c.section,benefit_types:c.benefit_types,conditions:c.conditions,display_order:c.display_order}); setHistory([]);}}>Editar</button>
        <button disabled={busy} onClick={() => {if(window.confirm(`Excluir a cláusula “${c.title}” das próximas gerações?`)) void action(async () => {await clauseRequest(token, `/${c.id}`, "DELETE"); await load(); if(editing?.id === c.id) {setEditing(null);setDraft(empty);}});}}>Excluir</button></>}
      <button disabled={busy} onClick={() => void action(async () => setHistory(await clauseRequest<Clause[]>(token, `/${c.id}/versions`)))}>Ver versões</button>
    </article>)}
    {history.length > 0 && <section aria-label="Histórico de versões"><h3>Versões de {history[0].title}</h3><button onClick={() => setHistory([])}>Fechar histórico</button>
      {history.map(v => <article className="clause-record" key={v.version}><h4>Versão {v.version} · {new Date(v.created_at).toLocaleString("pt-BR")}</h4><p>{v.benefit_types.join(", ")} · {JSON.stringify(v.conditions)}</p><pre>{v.text}</pre></article>)}
    </section>}
  </section>;
}
