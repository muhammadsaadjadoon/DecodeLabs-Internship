import { useEffect, useRef, useState } from "react";
import Icon from "./Icon";
import PremiumSelect from "./PremiumSelect";
import {
  ACCEPTED_EXTENSIONS,
  detectFromFilename,
  detectLanguageFromCode,
  LANGUAGE_MAP,
  LANGUAGE_OPTIONS,
  sameLanguageFamily,
} from "../utils/language";

const MAX_CHARS = 100_000;
const AUTO_DETECT_DELAY_MS = 320;

function filenameWithExtension(currentName, extension) {
  const value = String(currentName || "").trim();
  const fallback = "snippet";
  const separator = Math.max(value.lastIndexOf("/"), value.lastIndexOf("\\"));
  const dot = value.lastIndexOf(".");
  const base = dot > separator ? value.slice(0, dot) : value;
  return `${base || fallback}.${extension}`;
}

function mismatchMessage(fileName, expected, detected) {
  return `The file “${fileName}” is identified as ${detected.label}, but its extension represents ${expected.label}. Rename the file with the correct extension before starting the review.`;
}

export default function ReviewComposer({ onSubmit, loading, resetKey = 0, compact = false }) {
  const [mode, setMode] = useState("paste");
  const [file, setFile] = useState(null);
  const [code, setCode] = useState("");
  const [filename, setFilename] = useState("snippet.py");
  const [language, setLanguage] = useState("py");
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState("");
  const [languageNotice, setLanguageNotice] = useState("");
  const fileRef = useRef(null);
  const textareaRef = useRef(null);

  function resizeTextarea() {
    const textarea = textareaRef.current;
    if (!textarea) return;

    const collapsedHeight = 44;
    const expandedMinHeight = compact ? 96 : 112;
    const expandedMaxHeight = compact ? 170 : 240;

    // Always measure from the compact state so deleting code reliably shrinks the field.
    textarea.style.height = `${collapsedHeight}px`;

    if (!code.trim()) {
      textarea.style.height = `${collapsedHeight}px`;
      textarea.style.overflowY = "hidden";
      return;
    }

    const contentHeight = textarea.scrollHeight;
    const nextHeight = Math.min(
      Math.max(contentHeight, expandedMinHeight),
      expandedMaxHeight,
    );

    textarea.style.height = `${nextHeight}px`;
    textarea.style.overflowY = contentHeight > expandedMaxHeight ? "auto" : "hidden";
  }

  useEffect(() => {
    setFile(null);
    setCode("");
    setFilename("snippet.py");
    setLanguage("py");
    setMode("paste");
    setError("");
    setLanguageNotice("");
  }, [resetKey]);

  useEffect(() => {
    if (!compact) textareaRef.current?.focus({ preventScroll: true });
  }, [compact, resetKey]);

  useEffect(() => {
    resizeTextarea();
  }, [code, compact, mode, resetKey]);

  useEffect(() => {
    if (mode !== "paste" || !code.trim()) {
      setLanguageNotice("");
      setError((current) => (
        current.includes("source language") || current.includes("identified as") ? "" : current
      ));
      return undefined;
    }

    const timer = window.setTimeout(() => {
      const detected = detectLanguageFromCode(code);
      if (!detected) return;

      if (language !== detected.ext) {
        setLanguage(detected.ext);
        setFilename((current) => filenameWithExtension(current, detected.ext));
        setLanguageNotice(`Detected ${detected.label}. The language and file extension were updated automatically.`);
      }
      setError((current) => (
        current.includes("source language") || current.includes("identified as") ? "" : current
      ));
    }, AUTO_DETECT_DELAY_MS);

    return () => window.clearTimeout(timer);
  }, [code, language, mode]);

  async function chooseFile(candidate) {
    if (!candidate) return;
    setError("");
    setLanguageNotice("");

    if (candidate.size > MAX_CHARS * 4) {
      setError("This source file is too large for a reliable review. Please keep it below 100,000 characters.");
      return;
    }

    try {
      const source = await candidate.text();
      if (!source.trim()) throw new Error("The selected source file is empty.");
      if (source.length > MAX_CHARS) {
        throw new Error(`This file contains ${source.length.toLocaleString()} characters. The supported review limit is ${MAX_CHARS.toLocaleString()}.`);
      }

      const extensionMeta = detectFromFilename(candidate.name);
      const detected = detectLanguageFromCode(source);
      if (
        detected
        && extensionMeta.ext !== "txt"
        && !sameLanguageFamily(extensionMeta.ext, detected.ext)
      ) {
        throw new Error(mismatchMessage(candidate.name, extensionMeta, detected));
      }

      const resolvedLanguage = detected?.ext || extensionMeta.ext || "txt";
      setFile(candidate);
      setCode(source);
      setFilename(candidate.name);
      setLanguage(resolvedLanguage);
      setMode("file");
      if (detected && extensionMeta.ext === "txt") {
        setLanguageNotice(`Detected ${detected.label} from the source content.`);
      }
    } catch (err) {
      setFile(null);
      setCode("");
      setError(err.message || "This file could not be read as valid source code.");
    }
  }

  function changeLanguage(nextLanguage) {
    const meta = LANGUAGE_MAP[nextLanguage] || LANGUAGE_MAP.txt;
    setLanguage(nextLanguage);
    setFilename((current) => filenameWithExtension(current, meta.ext));
    setLanguageNotice("");
    setError("");
  }

  async function submit() {
    setError("");
    if (!code.trim()) {
      setError(mode === "file" ? "Attach a source file to begin the review." : "Paste source code to begin the review.");
      return;
    }
    if (code.length > MAX_CHARS) {
      setError(`This review exceeds the ${MAX_CHARS.toLocaleString()}-character limit.`);
      return;
    }

    const detected = detectLanguageFromCode(code);
    const finalLanguage = detected?.ext || language;
    const finalMeta = LANGUAGE_MAP[finalLanguage] || LANGUAGE_MAP.txt;
    const finalFilename = mode === "paste"
      ? filenameWithExtension(filename || "snippet", finalMeta.ext)
      : filename;
    const submission = {
      file: mode === "file" ? file : null,
      code,
      sourceCode: code,
      filename: finalFilename || `snippet.${finalLanguage}`,
      language: finalLanguage,
    };

    if (textareaRef.current) {
      textareaRef.current.style.height = "44px";
      textareaRef.current.style.overflowY = "hidden";
      textareaRef.current.scrollTop = 0;
    }
    setCode("");
    setFile(null);
    setLanguageNotice("");
    setError("");

    await onSubmit(submission);
  }

  const selectedMeta = LANGUAGE_MAP[language] || detectFromFilename(filename);

  return (
    <section className={`review-composer ${compact ? "compact" : ""}`} aria-label="Code review composer">
      <div className="composer-tabs" role="tablist" aria-label="Code input method">
        <button
          type="button"
          className={mode === "paste" ? "active" : ""}
          onClick={() => setMode("paste")}
          role="tab"
          aria-selected={mode === "paste"}
        >
          <Icon name="code" size={16} /> Paste code
        </button>
        <button
          type="button"
          className={mode === "file" ? "active" : ""}
          onClick={() => setMode("file")}
          role="tab"
          aria-selected={mode === "file"}
        >
          <Icon name="upload" size={16} /> Attach file
        </button>
      </div>

      {mode === "file" ? (
        <div
          className={`file-dropzone ${dragging ? "dragging" : ""} ${file ? "has-file" : ""}`}
          onDragOver={(event) => {
            event.preventDefault();
            if (!loading) setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={(event) => {
            event.preventDefault();
            setDragging(false);
            if (!loading) chooseFile(event.dataTransfer.files?.[0]);
          }}
          onClick={() => !loading && fileRef.current?.click()}
        >
          <input
            ref={fileRef}
            type="file"
            hidden
            accept={ACCEPTED_EXTENSIONS}
            onChange={(event) => chooseFile(event.target.files?.[0])}
          />
          <span className="dropzone-icon"><Icon name={file ? "file" : "upload"} size={22} /></span>
          {file ? (
            <div className="selected-file">
              <strong>{file.name}</strong>
              <span>{selectedMeta.label} · {(file.size / 1024).toFixed(1)} KB · ready for analysis</span>
            </div>
          ) : (
            <div>
              <strong>Drop a source file here</strong>
              <span>or click to browse · Python, JavaScript, Java, C++, Go and more</span>
            </div>
          )}
          {file && (
            <button
              type="button"
              className="remove-file-btn"
              onClick={(event) => {
                event.stopPropagation();
                setFile(null);
                setCode("");
                setLanguageNotice("");
              }}
            >
              Remove
            </button>
          )}
        </div>
      ) : (
        <div className="paste-editor">
          <div className="editor-toolbar">
            <label>
              <span>File name</span>
              <input
                value={filename}
                onChange={(event) => setFilename(event.target.value)}
                placeholder="snippet.py"
              />
            </label>
            <label>
              <span>Language</span>
              <PremiumSelect
                value={language}
                options={LANGUAGE_OPTIONS}
                onChange={changeLanguage}
                ariaLabel="Select source language"
                className="language-select"
              />
            </label>
          </div>
          <textarea
            ref={textareaRef}
            value={code}
            onChange={(event) => setCode(event.target.value)}
            placeholder="Paste the code you want CodeFix AI to review…"
            spellCheck={false}
            rows={1}
          />
          <div className="editor-meta">
            <span>{selectedMeta.label}</span>
            <span>{code.split("\n").length} lines · {code.length.toLocaleString()} / {MAX_CHARS.toLocaleString()} characters</span>
          </div>
        </div>
      )}

      {languageNotice && (
        <div className="composer-notice" role="status">
          <Icon name="sparkles" size={16} /> {languageNotice}
        </div>
      )}
      {error && <div className="composer-error"><Icon name="alert" size={16} /> {error}</div>}

      <div className="composer-footer-row">
        <div className="privacy-note">
          <Icon name="shield" size={15} />
          <span>Private analysis session · structured review output</span>
        </div>
        <button type="button" className="analyze-btn" onClick={submit} disabled={loading}>
          {loading ? (
            <><span className="spinner" /> Reviewing code…</>
          ) : (
            <><Icon name="sparkles" size={18} /> Review code</>
          )}
        </button>
      </div>
    </section>
  );
}
