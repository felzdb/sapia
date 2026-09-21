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
  uploadDocument,
  type DocumentResponse,
} from "../api";


type UploadAreaProps = {
  token: string;
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

          {document.dados_cliente && (
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
                  <strong>{document.dados_cliente.nome ?? "Não identificado"}</strong>
                </article>

                <article>
                  <span>CPF</span>
                  <strong>{document.dados_cliente.cpf ?? "Não identificado"}</strong>
                </article>

                <article>
                  <span>Data de nascimento</span>
                  <strong>{document.dados_cliente.data_nascimento ?? "Não identificado"}</strong>
                </article>

                <article>
                  <span>NIT/PIS</span>
                  <strong>{document.dados_cliente.nit_pis ?? "Não identificado"}</strong>
                </article>

                <article>
                  <span>Número do benefício</span>
                  <strong>{document.dados_cliente.numero_beneficio ?? "Não identificado"}</strong>
                </article>

                <article>
                  <span>Data de início do benefício (DIB)</span>
                  <strong>{document.dados_cliente.data_inicio_beneficio ?? "Não identificado"}</strong>
                </article>

                <article>
                  <span>Competências</span>
                  <strong>
                    {document.dados_cliente.competencias.length > 0
                      ? document.dados_cliente.competencias.join(", ")
                      : "Não identificadas"}
                  </strong>
                </article>

                <article>
                  <span>Valor do benefício</span>
                  <strong>{document.dados_cliente.valor_beneficio ?? "Não identificado"}</strong>
                </article>
              </div>

              <p className="client-data-note">
                Campos não identificados devem ser conferidos e preenchidos manualmente antes de prosseguir.
              </p>
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
