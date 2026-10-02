import {
  DragEvent,
  useRef,
  useState,
} from "react";

import {
  CheckCircle2,
  FileText,
  Files,
  ScanText,
  UploadCloud,
} from "lucide-react";

import {
  correctDocumentBenefit,
  finalizePetition,
  generatePetition,
  uploadDocument,
  type ClientData,
  type DocumentResponse,
  type PetitionResponse,
} from "../api";


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

  async function sendFile(file: File) {
    setError("");
    setDocument(null);
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
      clientData
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
                Documento processado
              </strong>

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
                </article>
              </div>

              {hasMissingClientData && (
                <p className="client-data-note">
                  Campos não identificados devem ser conferidos e preenchidos manualmente antes de prosseguir.
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

          <label className="petition-confirmation">
            <input
              type="checkbox"
              checked={dataConfirmed}
              disabled={hasMissingClientData || hasInvalidCpf}
              onChange={(event) =>
                setDataConfirmed(event.target.checked)
              }
            />

            <span>
              Confirmo que conferi os dados acima.
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

                <pre>
                  {petition.content}
                </pre>

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

          <div className="extracted-content">
            <div className="extracted-content-heading">
              <FileText size={20} />
              <h3>Conteúdo extraído</h3>
            </div>

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
          </div>
        </section>
      )}
    </>
  );
}
