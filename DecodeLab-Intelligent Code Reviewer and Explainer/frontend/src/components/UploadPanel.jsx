import { useRef, useState } from "react";
import { ACCEPTED_EXTENSIONS, detectFromFilename, LANGUAGE_MAP } from "../utils/language";

const MAX_CHARS = 100_000;

export default function UploadPanel({ onSubmit, loading, disabled }) {
  const [mode, setMode] = useState("upload"); // "upload" | "paste"
  const [file, setFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [pastedCode, setPastedCode] = useState("");
  const [pastedFilename, setPastedFilename] = useState("snippet.py");
  const [pastedLanguage, setPastedLanguage] = useState("py");
  const [localError, setLocalError] = useState("");
  const inputRef = useRef(null);

  function pickFile(f) {
    if (!f) return;
    if (f.size > MAX_CHARS * 2) {
      setLocalError("That file looks too large for this demo tool (keep it under ~60k characters).");
      return;
    }
    setLocalError("");
    setFile(f);
  }

  function handleDrop(e) {
    e.preventDefault();
    setDragActive(false);
    if (disabled) return;
    const f = e.dataTransfer.files?.[0];
    pickFile(f);
  }

  function handleSubmit() {
    setLocalError("");
    if (mode === "upload") {
      if (!file) {
        setLocalError("Choose or drop a source file first.");
        return;
      }
      onSubmit({ file });
    } else {
      if (!pastedCode.trim()) {
        setLocalError("Paste some code first.");
        return;
      }
      if (pastedCode.length > MAX_CHARS) {
        setLocalError(`That's ${pastedCode.length.toLocaleString()} characters — keep it under ${MAX_CHARS.toLocaleString()}.`);
        return;
      }
      onSubmit({
        code: pastedCode,
        language: pastedLanguage,
        filename: pastedFilename || `snippet.${pastedLanguage}`,
      });
    }
  }

  const detected = file ? detectFromFilename(file.name) : null;

  return (
    <section id="upload" className="mx-auto max-w-6xl px-6 py-6">
      <div className="rounded-xl border border-edge bg-surface shadow-panel">
        {/* Tabs */}
        <div className="flex border-b border-edge">
          {[
            { key: "upload", label: "Upload file" },
            { key: "paste", label: "Paste code" },
          ].map((tab) => (
            <button
              key={tab.key}
              onClick={() => setMode(tab.key)}
              className={`focus-ring px-5 py-3.5 font-mono text-xs font-medium transition ${
                mode === tab.key
                  ? "border-b-2 border-brand text-primary"
                  : "text-faint hover:text-muted"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <div className="p-6">
          {mode === "upload" ? (
            <div
              onDragOver={(e) => {
                e.preventDefault();
                if (!disabled) setDragActive(true);
              }}
              onDragLeave={() => setDragActive(false)}
              onDrop={handleDrop}
              onClick={() => !disabled && inputRef.current?.click()}
              className={`flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed px-6 py-14 text-center transition ${
                dragActive ? "border-brand bg-brand/5" : "border-edge hover:border-faint"
              } ${disabled ? "pointer-events-none opacity-60" : ""}`}
            >
              <input
                ref={inputRef}
                type="file"
                accept={ACCEPTED_EXTENSIONS}
                className="hidden"
                onChange={(e) => pickFile(e.target.files?.[0])}
              />
              <div className="mb-3 font-mono text-3xl text-faint">⌥</div>
              {file ? (
                <>
                  <p className="font-mono text-sm text-primary">{file.name}</p>
                  <p className="mt-1 text-xs text-faint">
                    Detected as <span className="text-brand">{detected.label}</span> · {(file.size / 1024).toFixed(1)} KB
                  </p>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setFile(null);
                    }}
                    className="focus-ring mt-3 rounded-full border border-edge px-3 py-1 text-xs text-muted hover:text-bug"
                  >
                    Remove file
                  </button>
                </>
              ) : (
                <>
                  <p className="text-sm text-muted">
                    Drag &amp; drop a source file here, or{" "}
                    <span className="text-brand underline underline-offset-2">browse</span>
                  </p>
                  <p className="mt-1.5 font-mono text-[11px] text-faint">.py .js .ts .java .cpp .go .rb .php .cs .rs …</p>
                </>
              )}
            </div>
          ) : (
            <div className="space-y-3">
              <div className="flex flex-wrap gap-3">
                <input
                  value={pastedFilename}
                  onChange={(e) => setPastedFilename(e.target.value)}
                  placeholder="filename.py"
                  className="focus-ring w-48 rounded-md border border-edge bg-raised px-3 py-2 font-mono text-xs text-primary placeholder:text-faint"
                />
                <select
                  value={pastedLanguage}
                  onChange={(e) => setPastedLanguage(e.target.value)}
                  className="focus-ring rounded-md border border-edge bg-raised px-3 py-2 font-mono text-xs text-primary"
                >
                  {Object.entries(LANGUAGE_MAP)
                    .filter(([ext]) => ext !== "txt")
                    .map(([ext, meta]) => (
                      <option key={ext} value={ext}>
                        {meta.label}
                      </option>
                    ))}
                </select>
              </div>
              <textarea
                value={pastedCode}
                onChange={(e) => setPastedCode(e.target.value)}
                placeholder="Paste your code here…"
                rows={12}
                spellCheck={false}
                className="focus-ring w-full resize-y rounded-lg border border-edge bg-raised p-4 font-mono text-[13px] leading-relaxed text-primary placeholder:text-faint"
              />
              <p className="text-right font-mono text-[11px] text-faint">
                {pastedCode.length.toLocaleString()} / {MAX_CHARS.toLocaleString()} chars
              </p>
            </div>
          )}

          {localError && (
            <p className="mt-3 rounded-md border border-bug/30 bg-bug/10 px-3 py-2 text-xs text-bug">{localError}</p>
          )}

          <div className="mt-5 flex items-center justify-between">
            <p className="font-mono text-[11px] text-faint">
              Analysis runs through Gemini · code is not stored after the response returns
            </p>
            <button
              onClick={handleSubmit}
              disabled={loading || disabled}
              className="focus-ring rounded-lg bg-brand px-6 py-2.5 font-mono text-sm font-semibold text-ink transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loading ? "Analyzing…" : "Analyze code"}
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}
