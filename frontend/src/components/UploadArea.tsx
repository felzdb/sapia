import {
  DragEvent,
  useRef,
  useState,
  useEffect,
} from "react";

import {
  CheckCircle2,
  FileText,
  Files,
  ScanText,
  UploadCloud,
} from "lucide-react";

import {
  clauseRequest,
  type ClauseOptions,
  type CaseSuggestion,
  correctDocumentBenefit,
  exportPetition,
  finalizePetition,
  generatePetition,
  uploadDocument,
  type ClientData,
  type DocumentResponse,
  type PetitionResponse,
} from "../api";


import PetitionSummary from "./PetitionSummary";

function formatWarning(message: string): string {
  return message.replace(/\[\s*DEMO(?:\s+RF8)?\s*\]\s*/gi, "")
    .replace(/\s*\(v\d+\)/gi, "").trim();
}

type UploadAreaProps = {
  token: string;
  onProcessingChange: (processing: boolean) => void;
  onDocumentProcessed: () => void;
  onPetitionGenerated: () => void;
};

const benefitLabels: Record<string, string> = {
  APOSENTADORIA_IDADE: "Aposentadoria por Idade",
  APOSENTADORIA_TEMPO_CONTRIBUICAO: "Aposentadoria por Tempo de Contribuição",
  APOSENTADORIA_INCAPACIDADE: "Aposentadoria por Incapacidade Permanente",
  AUXILIO_INCAPACIDADE_TEMPORARIA: "Auxílio por Incapacidade Temporária",
  AUXILIO_ACIDENTE: "Auxílio-Acidente",
  AUXILIO_RECLUSAO: "Auxílio-Reclusão",
  PENSAO_MORTE: "Pensão por Morte",
  SALARIO_MATERNIDADE: "Salário-Maternidade",
  BPC_IDOSO: "BPC - Idoso",
  BPC_DEFICIENCIA: "BPC - Pessoa com Deficiência",
  OUTRO: "Outro",
  NAO_IDENTIFICADO: "Não identificado",
};


export default function UploadArea({
  token,
  onProcessingChange,
  onDocumentProcessed,
  onPetitionGenerated,
}: UploadAreaProps) {
  const [caseSuggestions, setCaseSuggestions] = useState<Record<string, CaseSuggestion>>({});
  const [reviewedFields, setReviewedFields] = useState<Set<string>>(new Set());
  const [caseFields, setCaseFields] = useState<Record<string, string>>({});
  const [caseDetails, setCaseDetails] = useState<Record<string, boolean | null>>({});
  useEffect(() => {
    clauseRequest<ClauseOptions>(token, "/options").then(o => setCaseFields(o.case_fields))
      .catch(() => setError("Não foi possível carregar as particularidades do caso. Recarregue a página."));
  }, [token]);
  const inputRef = useRef<HTMLInputElement>(null);

  const [uploading, setUploading] =
    useState(false);

  const [error, setError] =
    useState("");

  const [document, setDocument] =
    useState<DocumentResponse | null>(null);

  const [clientData, setClientData] =
    useState<ClientData | null>(null);

  const [selectedBenefit, setSelectedBenefit] =
    useState("");

  const [correctingBenefit, setCorrectingBenefit] =
    useState(false);

  const [correctionSuccess, setCorrectionSuccess] =
    useState(false);

  const [generatingPetition, setGeneratingPetition] =
    useState(false);

  const [finalizingPetition, setFinalizingPetition] =
    useState(false);

  const [dataConfirmed, setDataConfirmed] =
    useState(false);

  const [petition, setPetition] =
    useState<PetitionResponse | null>(null);

  const [exportingFormat, setExportingFormat] =
    useState<"pdf" | "docx" | null>(null);

  const [exportMessage, setExportMessage] = useState("");
  const [exportError, setExportError] = useState("");

  useEffect(() => {
    setExportMessage("");
    setExportError("");
  }, [petition]);

  const hasMissingClientData =
    !!clientData &&
    (
      !clientData.nome ||
      !clientData.cpf ||
      !clientData.data_nascimento ||
      !clientData.nit_pis ||
      !clientData.numero_beneficio ||
      !clientData.data_inicio_beneficio ||
      clientData.competencias.length === 0 ||
      !clientData.valor_beneficio
    );

  const hasInvalidCpf =
    !!clientData?.cpf && !isValidCpf(clientData.cpf);

  const hasInvalidName =
    !!clientData?.nome && !isValidName(clientData.nome);

  const hasInvalidBirthDate =
    !!clientData?.data_nascimento &&
    !isValidDate(clientData.data_nascimento);

  const hasFutureBirthDate =
    !!clientData?.data_nascimento &&
    isValidDate(clientData.data_nascimento) &&
    isFutureDate(clientData.data_nascimento);

  const hasInvalidNitPis =
    !!clientData?.nit_pis &&
    !isValidNitPis(clientData.nit_pis);

  const hasInvalidBenefitNumber =
    !!clientData?.numero_beneficio &&
    !isValidBenefitNumber(clientData.numero_beneficio);

  const hasInvalidBenefitStartDate =
    !!clientData?.data_inicio_beneficio &&
    !isValidDate(clientData.data_inicio_beneficio);

  const hasBenefitStartBeforeBirth =
    !!clientData?.data_inicio_beneficio &&
    !!clientData?.data_nascimento &&
    isValidDate(clientData.data_inicio_beneficio) &&
    isValidDate(clientData.data_nascimento) &&
    isDateBefore(
      clientData.data_inicio_beneficio,
      clientData.data_nascimento
    );

  const hasInvalidCompetencias =
    !!clientData &&
    clientData.competencias.length > 0 &&
    !clientData.competencias.every(isValidCompetencia);

  const hasInvalidBenefitValue =
    !!clientData?.valor_beneficio &&
    !isValidBenefitValue(clientData.valor_beneficio);

  const hasInvalidClientData =
    hasInvalidCpf ||
    hasInvalidName ||
    hasInvalidBirthDate ||
    hasFutureBirthDate ||
    hasInvalidNitPis ||
    hasInvalidBenefitNumber ||
    hasInvalidBenefitStartDate ||
    hasBenefitStartBeforeBirth ||
    hasInvalidCompetencias ||
    hasInvalidBenefitValue;

  async function sendFile(file: File) {
    setError("");
    setDocument(null);
    setCaseDetails({});
    setCaseSuggestions({});
    setReviewedFields(new Set());
    setClientData(null);
    setPetition(null);
    setDataConfirmed(false);

    if (file.type !== "application/pdf") {
      setError(
        "Selecione um arquivo PDF."
      );

      return;
    }

    if (file.size > 20 * 1024 * 1024) {
      setError(
        "O arquivo deve possuir no máximo 20 MB."
      );

      return;
    }

    setUploading(true);
    onProcessingChange(true);

    try {
      const result =
        await uploadDocument(
          token,
          file
        );

      setDocument(result);
      const suggestions = result.case_suggestions ?? {};
      setCaseSuggestions(suggestions);
      setCaseDetails(Object.fromEntries(
        Object.entries(suggestions).map(([key, suggestion]) => [key, suggestion.value])
      ));
      setClientData(result.dados_cliente);
      onDocumentProcessed();

    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Não foi possível enviar o arquivo."
      );

    } finally {
      setUploading(false);
      onProcessingChange(false);
    }
  }

  function updateClientData<K extends keyof ClientData>(
    field: K,
    value: ClientData[K]
  ) {
    setClientData((current) =>
      current
        ? {
          ...current,
          [field]: value,
        }
        : current
    );

    setDataConfirmed(false);
    setPetition(null);
  }

  function formatDateInput(value: string) {
    const digits = value
      .replace(/\D/g, "")
      .slice(0, 8);

    if (digits.length <= 2) {
      return digits;
    }

    if (digits.length <= 4) {
      return `${digits.slice(0, 2)}/${digits.slice(2)}`;
    }

    return `${digits.slice(0, 2)}/${digits.slice(2, 4)}/${digits.slice(4)}`;
  }

  function formatMonthYearInput(value: string) {
    const digits = value
      .replace(/\D/g, "")
      .slice(0, 6);

    if (digits.length <= 2) {
      return digits;
    }

    return `${digits.slice(0, 2)}/${digits.slice(2)}`;
  }

  function formatCpfInput(value: string) {
    const digits = value
      .replace(/\D/g, "")
      .slice(0, 11);

    if (digits.length <= 3) {
      return digits;
    }

    if (digits.length <= 6) {
      return `${digits.slice(0, 3)}.${digits.slice(3)}`;
    }

    if (digits.length <= 9) {
      return `${digits.slice(0, 3)}.${digits.slice(3, 6)}.${digits.slice(6)}`;
    }

    return `${digits.slice(0, 3)}.${digits.slice(3, 6)}.${digits.slice(6, 9)}-${digits.slice(9)}`;
  }

  function isValidCpf(value: string) {
    const cpf = value.replace(/\D/g, "");

    if (cpf.length !== 11 || /^(\d)\1{10}$/.test(cpf)) {
      return false;
    }

    const calculateDigit = (length: number) => {
      let sum = 0;

      for (let i = 0; i < length; i++) {
        sum += Number(cpf[i]) * (length + 1 - i);
      }

      const remainder = (sum * 10) % 11;
      return remainder === 10 ? 0 : remainder;
    };

    return (
      calculateDigit(9) === Number(cpf[9]) &&
      calculateDigit(10) === Number(cpf[10])
    );
  }

  function isValidName(value: string) {
    const name = value.trim();

    if (!name || !/^[\p{L}\s'’-]+$/u.test(name)) {
      return false;
    }

    const letters = Array.from(name.toLocaleLowerCase()).filter((char) =>
      /\p{L}/u.test(char)
    );

    if (letters.length === 0) {
      return false;
    }

    if (letters.length >= 3 && new Set(letters).size === 1) {
      return false;
    }

    return true;
  }

  function isValidDate(value: string) {
    const match = value.trim().match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);

    if (!match) {
      return false;
    }

    const day = Number(match[1]);
    const month = Number(match[2]);
    const year = Number(match[3]);

    const date = new Date(year, month - 1, day);

    return (
      date.getFullYear() === year &&
      date.getMonth() === month - 1 &&
      date.getDate() === day
    );
  }

  function parseDate(value: string) {
    const match = value.trim().match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);

    if (!match) {
      return null;
    }

    const day = Number(match[1]);
    const month = Number(match[2]);
    const year = Number(match[3]);

    const date = new Date(year, month - 1, day);

    if (
      date.getFullYear() !== year ||
      date.getMonth() !== month - 1 ||
      date.getDate() !== day
    ) {
      return null;
    }

    return date;
  }

  function isFutureDate(value: string) {
    const date = parseDate(value);

    if (!date) {
      return false;
    }

    const today = new Date();
    today.setHours(0, 0, 0, 0);

    return date > today;
  }

  function isDateBefore(value: string, referenceValue: string) {
    const date = parseDate(value);
    const referenceDate = parseDate(referenceValue);

    if (!date || !referenceDate) {
      return false;
    }

    return date < referenceDate;
  }

  function isValidCompetencia(value: string) {
    const match = value.trim().match(/^(\d{1,2})\/(\d{4})$/);

    if (!match) {
      return false;
    }

    const month = Number(match[1]);
    const year = Number(match[2]);

    return month >= 1 && month <= 12 && year > 0;
  }

  function isValidBenefitValue(value: string) {
    const cleaned = value
      .trim()
      .replace("R$", "")
      .replace(/\./g, "")
      .replace(",", ".")
      .trim();

    if (!cleaned) {
      return false;
    }

    const amount = Number(cleaned);

    return Number.isFinite(amount) && amount > 0;
  }

  function isValidNitPis(value: string) {
    const identifier = value.trim();

    if (!identifier || !/^[\d\s.-]+$/.test(identifier)) {
      return false;
    }

    const digits = identifier.replace(/\D/g, "");

    if (digits.length !== 11 || /^(\d)\1{10}$/.test(digits)) {
      return false;
    }

    const weights = [3, 2, 9, 8, 7, 6, 5, 4, 3, 2];

    const total = weights.reduce(
      (sum, weight, index) =>
        sum + Number(digits[index]) * weight,
      0
    );

    const remainder = total % 11;
    let checkDigit = 11 - remainder;

    if (checkDigit === 10 || checkDigit === 11) {
      checkDigit = 0;
    }

    return checkDigit === Number(digits[10]);
  }

  function isValidBenefitNumber(value: string) {
    const identifier = value.trim();

    if (!identifier || !/^[\d\s.-]+$/.test(identifier)) {
      return false;
    }

    const digits = identifier.replace(/\D/g, "");

    if (digits.length !== 10 || /^(\d)\1{9}$/.test(digits)) {
      return false;
    }

    const weights = [2, 9, 8, 7, 6, 5, 4, 3, 2];

    const total = weights.reduce(
      (sum, weight, index) =>
        sum + Number(digits[index]) * weight,
      0
    );

    const remainder = total % 11;

    const checkDigit =
      remainder === 0 || remainder === 1
        ? 0
        : 11 - remainder;

    return checkDigit === Number(digits[9]);
  }

  async function handleBenefitCorrection() {
    if (!document || !selectedBenefit) {
      return;
    }

    setError("");
    setCorrectionSuccess(false);
    setCorrectingBenefit(true);

    try {
      const result = await correctDocumentBenefit(
        token,
        document.id,
        selectedBenefit
      );

      setDocument({
        ...document,
        benefit_type: result.benefit_type,
        benefit_confidence: result.benefit_confidence,
      });

      setCorrectionSuccess(true);
      setPetition(null);
      setDataConfirmed(false);

    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Não foi possível corrigir o benefício."
      );

    } finally {
      setCorrectingBenefit(false);
    }
  }

  async function handleGeneratePetition() {
    if (!document || !clientData) {
      return;
    }

    setError("");
    setPetition(null);
    setGeneratingPetition(true);

    try {
      const result = await generatePetition(
        token,
        document.id,
        clientData,
        caseDetails
      );

      setPetition(result);
      onPetitionGenerated();

    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Não foi possível gerar a petição."
      );

    } finally {
      setGeneratingPetition(false);
    }
  }


  async function handleExportPetition(
    fileFormat: "pdf" | "docx"
  ) {
    if (!document || !petition || exportingFormat) {
      return;
    }

    setExportMessage("");
    setExportError("");
    setExportingFormat(fileFormat);

    try {
      await exportPetition(
        token,
        document.id,
        fileFormat
      );

      setExportMessage(
        "Documento exportado com sucesso! O download iniciará automaticamente."
      );
    } catch (err) {
      setExportError(
        err instanceof Error
          ? err.message
          : "Não foi possível exportar a petição."
      );
    } finally {
      setExportingFormat(null);
    }
  }


  async function handleFinalizePetition() {
    if (!document || !petition) {
      return;
    }

    setError("");
    setFinalizingPetition(true);

    try {
      const result = await finalizePetition(
        token,
        document.id
      );

      setPetition(result);

    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Não foi possível finalizar a petição."
      );

    } finally {
      setFinalizingPetition(false);
    }
  }

  function handleDrop(
    event: DragEvent<HTMLButtonElement>
  ) {
    event.preventDefault();

    const file =
      event.dataTransfer.files[0];

    if (file) {
      sendFile(file);
    }
  }


  return (
    <>
      <button
        className="dropzone"
        type="button"
        onClick={() =>
          inputRef.current?.click()
        }
        onDragOver={(event) =>
          event.preventDefault()
        }
        onDrop={handleDrop}
        disabled={uploading}
      >
        <div className="dropzone-icon">
          <UploadCloud size={30} />
        </div>

        <strong>
          {uploading
            ? "Enviando documento..."
            : "Arraste o PDF aqui ou clique para selecionar"}
        </strong>

        <span>
          PDF de até 20 MB
        </span>
      </button>

      <input
        ref={inputRef}
        type="file"
        accept="application/pdf,.pdf"
        hidden
        onChange={(event) => {
          const file =
            event.target.files?.[0];

          if (file) {
            sendFile(file);
          }

          event.target.value = "";
        }}
      />

      {error && (
        <div className="error-box upload-message">
          {error}
        </div>
      )}

      {document && (
        <section
          className="document-result"
          aria-live="polite"
        >
          <div className="upload-success">
            <CheckCircle2 size={22} />

            <div>
              <strong>
                Documento processado com sucesso!
              </strong>

              <span>
                Verifique os dados extraídos.
              </span>

              <span>
                {document.original_filename}
              </span>
            </div>
          </div>

          {clientData && (
            <section className="client-data-card">
              <div className="extracted-content-heading">
                <FileText size={20} />
                <div>
                  <h3>Dados extraídos do cliente</h3>
                  <span>Confira as informações identificadas no documento.</span>
                </div>
              </div>

              <div className="client-data-grid">
                <article>
                  <span>Nome completo</span>

                  <input
                    type="text"
                    value={clientData.nome ?? ""}
                    placeholder="Não identificado"
                    onChange={(event) =>
                      updateClientData(
                        "nome",
                        event.target.value || null
                      )
                    }
                  />

                  {hasInvalidName && (
                    <span className="field-error">
                      Nome inválido. Use apenas letras, espaços, hífen ou apóstrofo e não informe apenas a mesma letra repetida.
                    </span>
                  )}
                </article>

                <article>
                  <span>CPF</span>

                  <input
                    type="text"
                    value={clientData.cpf ?? ""}
                    placeholder="Não identificado"
                    onChange={(event) =>
                      updateClientData(
                        "cpf",
                        formatCpfInput(event.target.value) || null
                      )
                    }
                  />

                  {hasInvalidCpf && (
                    <span className="field-error">
                      CPF inválido. Verifique os dígitos informados.
                    </span>
                  )}
                </article>

                <article>
                  <span>Data de nascimento</span>

                  <input
                    type="text"
                    value={clientData.data_nascimento ?? ""}
                    placeholder="DD/MM/AAAA"
                    onChange={(event) =>
                      updateClientData(
                        "data_nascimento",
                        formatDateInput(event.target.value) || null
                      )
                    }
                  />

                  {hasInvalidBirthDate && (
                    <span className="field-error">
                      Data de nascimento inválida. Verifique a data informada.
                    </span>
                  )}

                  {hasFutureBirthDate && (
                    <span className="field-error">
                      Data de nascimento inválida. A data de nascimento não pode estar no futuro.
                    </span>
                  )}
                </article>

                <article>
                  <span>NIT/PIS</span>

                  <input
                    type="text"
                    value={clientData.nit_pis ?? ""}
                    placeholder="Não identificado"
                    onChange={(event) =>
                      updateClientData(
                        "nit_pis",
                        event.target.value || null
                      )
                    }
                  />

                  {hasInvalidNitPis && (
                    <span className="field-error">
                      NIT/PIS inválido. Confira os 11 dígitos e o dígito verificador. Pontos e hífen são opcionais.
                    </span>
                  )}
                </article>

                <article>
                  <span>Número do benefício</span>

                  <input
                    type="text"
                    value={clientData.numero_beneficio ?? ""}
                    placeholder="Não identificado"
                    onChange={(event) =>
                      updateClientData(
                        "numero_beneficio",
                        event.target.value || null
                      )
                    }
                  />

                  {hasInvalidBenefitNumber && (
                    <span className="field-error">
                      Número do benefício inválido. Confira os 10 dígitos e o dígito verificador. Pontos e hífen são opcionais.
                    </span>
                  )}
                </article>

                <article>
                  <span>Data de início do benefício (DIB)</span>

                  <input
                    type="text"
                    value={clientData.data_inicio_beneficio ?? ""}
                    placeholder="DD/MM/AAAA"
                    onChange={(event) =>
                      updateClientData(
                        "data_inicio_beneficio",
                        formatDateInput(event.target.value) || null
                      )
                    }
                  />

                  {hasInvalidBenefitStartDate && (
                    <span className="field-error">
                      Data de início do benefício inválida. Verifique a data informada.
                    </span>
                  )}

                  {hasBenefitStartBeforeBirth && (
                    <span className="field-error">
                      Data de início do benefício inválida. A DIB não pode ser anterior à data de nascimento.
                    </span>
                  )}
                </article>

                <article>
                  <span>Competências</span>

                  <input
                    type="text"
                    value={clientData.competencias.join(", ")}
                    placeholder="MM/AAAA"
                    onChange={(event) =>
                      updateClientData(
                        "competencias",
                        event.target.value
                          .split(",")
                          .map((item) => formatMonthYearInput(item.trim()))
                          .filter(Boolean)
                      )
                    }
                  />

                  {hasInvalidCompetencias && (
                    <span className="field-error">
                      Competência inválida. Use mês e ano válidos.
                    </span>
                  )}
                </article>

                <article>
                  <span>Valor do benefício</span>

                  <input
                    type="text"
                    value={clientData.valor_beneficio ?? ""}
                    placeholder="Não identificado"
                    onChange={(event) =>
                      updateClientData(
                        "valor_beneficio",
                        event.target.value || null
                      )
                    }
                  />

                  {hasInvalidBenefitValue && (
                    <span className="field-error">
                      Valor do benefício inválido. Informe um valor maior que zero.
                    </span>
                  )}
                </article>
              </div>

              {hasMissingClientData && (
                <p className="client-data-note">
                  Alguns campos obrigatórios não foram identificados. Complete-os manualmente antes de prosseguir.
                </p>
              )}
            </section>
          )}

          <div className="document-summary">
            <article className="document-summary-card">
              <CheckCircle2 size={20} />
              <span>Status</span>
              <strong>{document.status}</strong>
            </article>

            <article className="document-summary-card">
              <Files size={20} />
              <span>Páginas</span>
              <strong>{document.page_count ?? 0}</strong>
            </article>

            <article className="document-summary-card">
              <ScanText size={20} />
              <span>Páginas sem texto</span>
              <strong>
                {document.pages_without_text.length > 0
                  ? document.pages_without_text.join(", ")
                  : "Nenhuma"}
              </strong>
            </article>

            <article className="document-summary-card">
              <FileText size={20} />
              <span>Tamanho</span>
              <strong>
                {(document.size_bytes / 1024).toLocaleString(
                  "pt-BR",
                  { maximumFractionDigits: 1 }
                )} KB
              </strong>
            </article>
            <article className="document-summary-card">
              <ScanText size={20} />
              <span>Benefício identificado</span>
              <strong>
                {document.benefit_type
                  ? benefitLabels[document.benefit_type] ?? document.benefit_type
                  : "Não identificado"}
              </strong>
            </article>

            <article className="document-summary-card">
              <ScanText size={20} />
              <span>Corrigir benefício</span>

              <select
                value={selectedBenefit}
                onChange={(event) =>
                  setSelectedBenefit(event.target.value)
                }
                disabled={correctingBenefit}
              >
                <option value="">
                  Selecione...
                </option>

                {Object.entries(benefitLabels).map(
                  ([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  )
                )}
              </select>

              <button
                type="button"
                onClick={handleBenefitCorrection}
                disabled={
                  !selectedBenefit ||
                  correctingBenefit
                }
              >
                {correctingBenefit
                  ? "Salvando..."
                  : "Confirmar correção"}
              </button>

              {correctionSuccess && (
                <small>
                  Benefício corrigido com sucesso.
                </small>
              )}
            </article>
          </div>

          <details className="extracted-content extracted-content-details">
            <summary className="extracted-content-toggle">
              <FileText size={20} />
              <span>Ver texto extraído do documento</span>
            </summary>

            <pre>
              {document.extracted_text?.trim()
                || "Nenhum texto foi encontrado neste documento."}
            </pre>

            {document.pages_without_text.length > 0 && (
              <p className="ocr-warning">
                As páginas indicadas não possuem camada de texto e
                poderão precisar de processamento por OCR.
              </p>
            )}
          </details>

          <section className="petition-generation">
            <div className="extracted-content-heading">
              <FileText size={20} />

              <div>
                <h3>Petição inicial</h3>
                <span>
                  Gere a petição com os dados conferidos acima.
                </span>
              </div>
            </div>

            <fieldset className="case-details">
              <legend>Particularidades do caso</legend>
              <p>
                Confira os trechos e corrija o que for necessário.
              </p>
              {Object.entries(caseFields).map(([key, label]) => (
                <div className="case-suggestion" key={key}>
                  <label>
                    {label}
                    <select
                      value={caseDetails[key] == null ? "" : String(caseDetails[key])}
                      disabled={generatingPetition || finalizingPetition}
                      onChange={(event) => {
                        setCaseDetails({
                          ...caseDetails,
                          [key]: event.target.value === "" ? null : event.target.value === "true",
                        });
                        setReviewedFields((current) => new Set([...current, key]));
                        setPetition(null);
                        setDataConfirmed(false);
                      }}
                    >
                      <option value="">Não informado</option>
                      <option value="true">Sim</option>
                      <option value="false">Não</option>
                    </select>
                  </label>
                </div>
              ))}
            </fieldset>
            <label className="petition-confirmation">
              <input
                type="checkbox"
                checked={dataConfirmed}
                disabled={hasMissingClientData || hasInvalidClientData}
                onChange={(event) =>
                  setDataConfirmed(event.target.checked)
                }
              />

              <span>
                Confirmo que conferi os dados.
              </span>
            </label>

            <button
              className="primary-button petition-generate-button"
              type="button"
              aria-busy={generatingPetition}
              onClick={handleGeneratePetition}
              disabled={
                generatingPetition ||
                !dataConfirmed ||
                !document.dados_cliente ||
                !document.benefit_type ||
                document.benefit_type === "NAO_IDENTIFICADO"
              }
            >
              {generatingPetition
                ? "Gerando petição..."
                : "Gerar petição"}
            </button>

            {petition && (
              <div className="petition-preview">
                <h3>Pré-visualização da petição</h3>
                <PetitionSummary petition={petition} />
                <pre>
                  {petition.content}
                </pre>


                <div className="petition-export-actions">
                  <button
                    className="primary-button"
                    type="button"
                    onClick={() => handleExportPetition("pdf")}
                    disabled={exportingFormat !== null}
                    aria-busy={exportingFormat === "pdf"}
                  >
                    {exportingFormat === "pdf"
                      ? "Exportando PDF..."
                      : "Exportar PDF"}
                  </button>

                  <button
                    className="primary-button"
                    type="button"
                    onClick={() => handleExportPetition("docx")}
                    disabled={exportingFormat !== null}
                    aria-busy={exportingFormat === "docx"}
                  >
                    {exportingFormat === "docx"
                      ? "Exportando Word..."
                      : "Exportar Word"}
                  </button>
                </div>

                {exportMessage && (
                  <p className="petition-export-success" role="status">
                    {exportMessage}
                  </p>
                )}

                {exportError && (
                  <p className="petition-export-error" role="alert">
                    {exportError}
                  </p>
                )}


                {petition.status !== "FINALIZADA" ? (
                  <button
                    className="primary-button petition-finalize-button"
                    type="button"
                    onClick={handleFinalizePetition}
                    disabled={finalizingPetition}
                  >
                    {finalizingPetition
                      ? "Finalizando petição..."
                      : "Finalizar petição"}
                  </button>
                ) : (
                  <p className="petition-finalized-message">
                    Petição finalizada com sucesso.
                  </p>
                )}
              </div>
            )}
          </section>

        </section>
      )}
    </>
  );
}
