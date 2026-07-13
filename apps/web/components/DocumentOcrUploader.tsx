"use client";

import { useState, useRef, useCallback } from "react";
import { createWorker } from "tesseract.js";
import { submitDocumentOcr, DocumentOcrResponse } from "../lib/api";

const DOCUMENT_TYPES = [
  { value: "passport", label: "Passport" },
  { value: "cv", label: "CV / Resume" },
  { value: "degree", label: "Degree / Certificate" },
  { value: "language_certificate", label: "Language certificate" },
  { value: "other", label: "Other" },
];

export function DocumentOcrUploader({
  leadId,
  onExtracted,
}: {
  leadId: string;
  onExtracted?: (result: DocumentOcrResponse) => void;
}) {
  const [file, setFile] = useState<File | null>(null);
  const [documentType, setDocumentType] = useState("passport");
  const [progress, setProgress] = useState<string | null>(null);
  const [extractedText, setExtractedText] = useState<string | null>(null);
  const [result, setResult] = useState<DocumentOcrResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback((selected: File | null) => {
    if (!selected) return;
    if (!selected.type.startsWith("image/")) {
      setError("Please upload an image file (PNG, JPG, WEBP). PDFs are not supported by browser OCR.");
      return;
    }
    setFile(selected);
    setError(null);
    setExtractedText(null);
    setResult(null);
  }, []);

  const runOcr = async () => {
    if (!file) return;
    setProgress("Reading document...");
    setError(null);

    try {
      const worker = await createWorker("eng");
      const ret = await worker.recognize(file);
      await worker.terminate();

      const text = ret.data.text;
      setExtractedText(text);
      setProgress("Saving extraction...");

      const response = await submitDocumentOcr({
        lead_id: leadId,
        document_type: documentType,
        filename: file.name,
        extracted_text: text,
        language: "eng",
        confidence: ret.data.confidence,
      });

      setResult(response);
      setProgress(null);
      onExtracted?.(response);
    } catch (err) {
      setProgress(null);
      setError(err instanceof Error ? err.message : "OCR failed");
    }
  };

  return (
    <div className="document-ocr-uploader">
      <label className="ocr-dropzone">
        <input
          ref={inputRef}
          type="file"
          accept="image/png,image/jpeg,image/jpg,image/webp"
          onChange={(e) => handleFile(e.target.files?.[0] || null)}
        />
        {file ? (
          <span>{file.name}</span>
        ) : (
          <span>Drop or click to upload an image (passport, CV, certificate)</span>
        )}
      </label>

      <div className="ocr-controls">
        <select value={documentType} onChange={(e) => setDocumentType(e.target.value)}>
          {DOCUMENT_TYPES.map((t) => (
            <option key={t.value} value={t.value}>
              {t.label}
            </option>
          ))}
        </select>
        <button className="button primary" type="button" onClick={runOcr} disabled={!file || !!progress}>
          {progress ? progress : "Extract text"}
        </button>
      </div>

      {error && <div className="inline-notice error">{error}</div>}

      {result && (
        <div className="ocr-result panel">
          <h3>Extracted from {result.document_type}</h3>
          {Object.keys(result.parsed_fields).length > 0 && (
            <div className="ocr-parsed-fields">
              <strong>Parsed fields</strong>
              <pre>{JSON.stringify(result.parsed_fields, null, 2)}</pre>
            </div>
          )}
          <details>
            <summary>Raw extracted text</summary>
            <pre className="ocr-raw">{extractedText}</pre>
          </details>
        </div>
      )}
    </div>
  );
}
