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
  uploadDocument,
  type DocumentResponse,
} from "../api";


type UploadAreaProps = {
  token: string;
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
}: UploadAreaProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  const [uploading, setUploading] =
    useState(false);

  const [error, setError] =
    useState("");

  const [document, setDocument] =
    useState<DocumentResponse | null>(null);

      const [selectedBenefit, setSelectedBenefit] =
    useState("");

  const [correctingBenefit, setCorrectingBenefit] =
    useState(false);

  const [correctionSuccess, setCorrectionSuccess] =
    useState(false);


  async function sendFile(file: File) {
    setError("");
    setDocument(null);

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

    try {
      const result =
        await uploadDocument(
          token,
          file
        );

      setDocument(result);

    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Não foi possível enviar o arquivo."
      );

    } finally {
      setUploading(false);
    }
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
            </article>
          </div>

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
