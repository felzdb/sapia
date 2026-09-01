import {
  DragEvent,
  useRef,
  useState,
} from "react";

import {
  CheckCircle2,
  FileText,
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
        <div className="upload-success">

          <CheckCircle2 size={22} />

          <div>
            <strong>
              Documento enviado
            </strong>

            <span>
              {document.original_filename}
            </span>
          </div>

        </div>
      )}
    </>
  );
}