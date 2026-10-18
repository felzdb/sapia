import type { PetitionResponse } from "../api";

const fields = [
  ["insalubridade", "Atividade insalubre"],
  ["periculosidade", "Atividade perigosa"],
  ["gratuidade", "Pedido de justiça gratuita"],
  ["tutela_urgencia", "Pedido de tutela de urgência"],
] as const;

function clauseName(title: string) {
  return title
    .replace(/^\s*(?:\[\s*DEMO(?:\s+RF8)?\s*\]\s*)+/i, "")
    .replace(/(?:\s*\(v\d+\))+\s*$/i, "")
    .trim();
}

function answer(value: boolean | null | undefined) {
  return value === true ? "Sim" : value === false ? "Não" : "Não informado";
}

export default function PetitionSummary({ petition }: { petition: PetitionResponse }) {
  const clauses = petition.clauses ?? [];
  const benefitClauses = clauses.filter((clause) => Object.keys(clause.conditions ?? {}).length === 0);
  const conditionalClauses = clauses.filter((clause) => Object.keys(clause.conditions ?? {}).length > 0);

  return (
    <div className="petition-summary">
      <section className="petition-summary-section" aria-label="Cláusulas do benefício incluídas">
        <h4>Cláusulas do benefício incluídas:</h4>
        {benefitClauses.length > 0 ? (
          <ul>
            {benefitClauses.map((clause) => (
              <li key={`${clause.id}-${clause.version}`}>
                {clauseName(clause.title)}
              </li>
            ))}
          </ul>
        ) : <p>Nenhuma cláusula sem condições adicionais foi incluída.</p>}
      </section>

      <section className="petition-summary-section" aria-label="Particularidades do caso">
        <h4>Particularidades do caso:</h4>
        <dl className="petition-particulars-list">
          {fields.map(([key, label]) => (
            <div key={key}>
              <dt>{label}</dt>
              <dd>{answer(petition.case_details?.[key])}</dd>
            </div>
          ))}
        </dl>
      </section>
    </div>
  );
}
