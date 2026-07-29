import { useEffect, useMemo, useRef, useState } from "react";
import { bulkGenerate, bulkTemplateUrl } from "../api.js";

const REQUIRED_COLUMNS = ["product_name", "product_description", "platform", "tone"];

function parseLine(line) {
  const cells = [];
  let current = "";
  let quoted = false;
  for (let i = 0; i < line.length; i += 1) {
    const char = line[i];
    if (char === '"') quoted = !quoted;
    else if (char === "," && !quoted) { cells.push(current.trim()); current = ""; }
    else current += char;
  }
  cells.push(current.trim());
  return cells.map((cell) => cell.replace(/^"|"$/g, ""));
}

function parsePreview(text) {
  const lines = text.split(/\r?\n/).filter((line) => line.trim().length);
  if (!lines.length) return { headers: [], rows: [], errors: ["CSV is empty"], totalRows: 0 };
  const headers = parseLine(lines[0]).map((h) => h.trim());
  const missing = REQUIRED_COLUMNS.filter((col) => !headers.includes(col));
  const rows = lines.slice(1).map((line, index) => {
    const cells = parseLine(line);
    const row = Object.fromEntries(headers.map((h, i) => [h, cells[i]?.trim() || ""]));
    const rowErrors = REQUIRED_COLUMNS.filter((col) => !row[col]).map((col) => `${col} missing`);
    return { index: index + 1, row, rowErrors };
  });
  return { headers, rows, errors: missing.length ? [`Missing columns: ${missing.join(", ")}`] : [], totalRows: rows.length };
}

function bytes(size) {
  if (!size) return "0 KB";
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / 1024 / 1024).toFixed(2)} MB`;
}

function downloadCSV(results) {
  const headers = ["row_id", "product_name", "platform", "tone", "status", "headline", "body", "cta", "error"];
  const rows = results.map((r) => {
    const copy = r.response?.variations?.[0];
    return [r.row_id, r.product_name, r.response?.platform || "", r.response?.tone || "", r.status, copy?.headline || "", copy?.body || "", copy?.call_to_action || "", r.error || ""];
  });
  const csv = [headers, ...rows].map((row) => row.map((cell) => `"${String(cell ?? "").replaceAll('"', '""')}"`).join(",")).join("\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "lexora-bulk-results.csv";
  a.click();
  URL.revokeObjectURL(url);
}

export default function BulkPanel({ meta }) {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const inputRef = useRef(null);
  const abortRef = useRef(null);

  useEffect(() => {
    if (!file) { setPreview(null); return; }
    const reader = new FileReader();
    reader.onload = () => setPreview(parsePreview(String(reader.result || "")));
    reader.onerror = () => setPreview({ headers: [], rows: [], errors: ["Could not read this CSV file"], totalRows: 0 });
    reader.readAsText(file);
  }, [file]);

  useEffect(() => {
    if (!loading) return;
    setProgress(12);
    const id = setInterval(() => setProgress((p) => Math.min(92, p + Math.random() * 11)), 420);
    return () => clearInterval(id);
  }, [loading]);

  const onDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const dropped = e.dataTransfer.files?.[0];
    if (dropped) setFile(dropped);
  };

  const runBatch = async () => {
    if (!file || loading) return;
    abortRef.current = new AbortController();
    setLoading(true);
    setError(null);
    setResults(null);
    try {
      const data = await bulkGenerate(file, abortRef.current.signal);
      setResults(data);
      setProgress(100);
    } catch (err) {
      setError(err.message);
      setProgress(0);
    } finally {
      setLoading(false);
    }
  };

  const clearAll = () => {
    setFile(null); setPreview(null); setResults(null); setError(null); setProgress(0);
    if (inputRef.current) inputRef.current.value = "";
  };

  const cancelBatch = () => abortRef.current?.abort();
  const successCount = results?.filter((r) => r.status === "success").length ?? 0;
  const errorCount = results?.filter((r) => r.status === "error").length ?? 0;
  const pendingCount = results ? Math.max(0, (preview?.totalRows || 0) - results.length) : 0;
  const hasPreviewErrors = preview?.errors?.length || preview?.rows?.some((r) => r.rowErrors.length);
  const invalidRows = useMemo(() => preview?.rows?.filter((r) => r.rowErrors.length).length || 0, [preview]);

  return (
    <div className="grid gap-6 xl:grid-cols-[0.33fr_0.67fr]">
      <div className="lex-card relative flex h-[clamp(650px,76vh,850px)] flex-col overflow-hidden rounded-[2rem] border border-white/10 bg-lex-panel p-5 shadow-premium sm:p-7">
        <div className="absolute -right-24 -top-24 h-64 w-64 rounded-full bg-lex-cyan/10 blur-3xl" />
        <div className="relative flex min-h-0 flex-1 flex-col gap-5">
          <div className="shrink-0">
            <p className="font-mono text-[11px] uppercase tracking-[0.26em] text-lex-cyan/75">Bulk CSV system</p>
            <h2 className="mt-2 font-display text-2xl font-extrabold text-white">Upload, preview, validate, export.</h2>
            <p className="mt-2 text-sm leading-relaxed text-white/52">Max {meta?.bulk_max_rows || 200} rows. Required: product_name, product_description, platform, tone. Optional: audience, objective, language, length, keywords, brand_voice and more.</p>
          </div>

          <div className="grid shrink-0 gap-3 sm:grid-cols-3 xl:grid-cols-1 2xl:grid-cols-3">
            {[
              ["CSV Preview", preview ? `${preview.totalRows} rows` : "Ready"],
              ["Row Validation", invalidRows ? `${invalidRows} invalid` : "Ready"],
              ["Results CSV", results ? `${successCount}/${results.length}` : "Ready"],
            ].map(([title, value]) => (
              <div key={title} className="rounded-3xl border border-white/10 bg-midnight/55 p-4">
                <p className="font-mono text-[10px] uppercase tracking-[0.2em] text-lex-cyan/75">{value}</p>
                <p className="mt-2 text-sm font-bold text-white">{title}</p>
              </div>
            ))}
          </div>

          <a href={bulkTemplateUrl()} className="inline-flex w-full shrink-0 items-center justify-center gap-2 rounded-2xl border border-lex-cyan/30 bg-lex-cyan/10 px-4 py-3 font-display text-sm font-extrabold text-lex-cyan shadow-glow transition hover:bg-lex-cyan/16 focus:bg-lex-cyan/16">↓ Download extended CSV template</a>

          <div onDragOver={(e) => { e.preventDefault(); setDragOver(true); }} onDragLeave={() => setDragOver(false)} onDrop={onDrop} onClick={() => inputRef.current?.click()} className={`shrink-0 cursor-pointer rounded-3xl border-2 border-dashed p-5 text-center transition-colors ${dragOver ? "border-lex-cyan bg-lex-cyan/10" : "border-white/12 bg-midnight/45 hover:border-lex-cyan/45"}`}>
            <input ref={inputRef} type="file" accept=".csv" className="hidden" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
            <p className="font-display text-lg font-bold text-white">{file ? file.name : "Drop CSV here"}</p>
            <p className="mt-2 text-xs text-white/42">Click to browse · UTF-8 CSV · 2 MB limit</p>
            {file && <p className="mt-2 font-mono text-[11px] text-lex-cyan/80">{bytes(file.size)} · {preview?.totalRows || 0} rows detected</p>}
          </div>

          <div className="grid shrink-0 gap-3 sm:grid-cols-[1fr_auto]">
            <button onClick={runBatch} disabled={!file || loading || preview?.errors?.length} className="rounded-2xl bg-lex-button px-5 py-4 font-display text-sm font-extrabold text-midnight shadow-glow transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-40">{loading ? "Running batch…" : "Run Batch"}</button>
            <button onClick={loading ? cancelBatch : clearAll} disabled={!loading && !file && !results} className="rounded-2xl border border-white/10 px-5 py-4 text-sm font-bold text-white/60 hover:border-red-400/30 hover:text-red-300 disabled:opacity-35">{loading ? "Cancel" : "Remove"}</button>
          </div>

          {loading && <div className="shrink-0"><div className="mb-2 flex justify-between font-mono text-[11px] text-white/40"><span>Processing</span><span>{Math.round(progress)}%</span></div><div className="h-2 overflow-hidden rounded-full bg-white/10"><div className="h-full rounded-full bg-gradient-to-r from-lex-cyan to-lex-teal" style={{ width: `${progress}%` }} /></div></div>}
          {error && <p className="shrink-0 rounded-2xl border border-red-400/25 bg-red-500/10 px-4 py-3 text-sm text-red-200">{error}</p>}

          <div className="thin-scroll min-h-0 flex-1 overflow-y-auto rounded-3xl border border-white/10 bg-midnight/40">
            {!preview && <div className="grid h-full min-h-[180px] place-items-center p-6 text-center text-sm text-white/36">CSV preview stays here without expanding the page.</div>}
            {preview && <div className="p-4 text-sm">
              <div className="sticky -top-4 z-10 -mx-4 mb-3 flex flex-wrap justify-between gap-2 border-b border-white/10 bg-midnight/95 px-4 py-3">
                <p className="font-bold text-white">Preview: {preview.totalRows} rows</p><p className="font-mono text-xs text-white/45">{invalidRows} invalid</p>
              </div>
              {preview.errors.map((item) => <p key={item} className="mb-2 rounded-xl border border-red-400/25 bg-red-500/10 px-3 py-2 text-red-200">{item}</p>)}
              {!hasPreviewErrors && <p className="mb-3 rounded-xl border border-lex-cyan/25 bg-lex-cyan/8 px-3 py-2 text-lex-cyan/85">CSV header looks valid. Full validation runs during processing.</p>}
              <div className="grid gap-2">
                {preview.rows.map((r) => <div key={r.index} className={`rounded-2xl border p-3 ${r.rowErrors.length ? "border-red-400/30 bg-red-500/10" : "border-white/10 bg-white/[0.03]"}`}><div className="flex justify-between gap-3"><p className="font-bold text-white">#{r.index} {r.row.product_name || "Untitled"}</p><p className={`font-mono text-[11px] ${r.rowErrors.length ? "text-red-200" : "text-lex-cyan"}`}>{r.rowErrors.length ? "invalid" : "valid"}</p></div><p className="mt-1 line-clamp-2 text-xs text-white/42">{r.rowErrors.join(", ") || r.row.product_description || "Ready"}</p></div>)}
              </div>
            </div>}
          </div>
        </div>
      </div>

      <div className="flex h-[clamp(650px,76vh,850px)] flex-col overflow-hidden rounded-[2rem] border border-white/10 bg-paper p-2 text-ink shadow-paper">
        <div className="sticky top-0 z-10 flex flex-wrap items-center justify-between gap-3 rounded-t-[1.5rem] border-b border-paperLine bg-paper px-4 py-3">
          <div><p className="font-mono text-[11px] uppercase tracking-wider text-ink/58">Results panel</p><p className="text-sm text-ink/70">Success {successCount} · Failed {errorCount} · Pending {pendingCount}</p></div>
          <div className="flex flex-wrap gap-2"><button disabled={!results} onClick={() => downloadCSV(results || [])} className="rounded-xl border border-ink/10 px-3 py-2 text-xs font-bold text-ink/82 hover:border-cyan-400 disabled:opacity-60">Download results CSV</button><button disabled={!errorCount} onClick={runBatch} className="rounded-xl border border-ink/10 px-3 py-2 text-xs font-bold text-ink/82 hover:border-cyan-400 disabled:opacity-60">Retry failed</button><button disabled={!results && !preview} onClick={clearAll} className="rounded-xl border border-red-200 px-3 py-2 text-xs font-bold text-red-800 hover:bg-red-50 disabled:opacity-60">Clear</button></div>
        </div>
        <div className="thin-scroll min-h-0 flex-1 overflow-auto rounded-b-[1.5rem] bg-paper">
          <table className="w-full min-w-[760px] text-sm">
            <thead><tr className="sticky top-0 z-10 border-b border-paperLine bg-paper text-left font-mono text-[11px] uppercase tracking-wider text-ink/58"><th className="px-4 py-3">#</th><th className="px-4 py-3">Product</th><th className="px-4 py-3">Platform</th><th className="px-4 py-3">Tone</th><th className="px-4 py-3">Status</th><th className="px-4 py-3">Headline / Error</th></tr></thead>
            <tbody>
              {!results && !preview && <tr><td colSpan={6} className="py-28 text-center font-serif text-ink/68">CSV preview and batch results will appear here.</td></tr>}
              {!results && preview?.rows?.map((r) => <tr key={r.index} className={`border-b border-paperLine/70 ${r.rowErrors.length ? "bg-red-50" : ""}`}><td className="px-4 py-3 font-mono text-xs text-ink/58">{r.index}</td><td className="px-4 py-3 font-medium">{r.row.product_name || "—"}</td><td className="px-4 py-3 font-mono text-xs">{r.row.platform || "—"}</td><td className="px-4 py-3 font-mono text-xs">{r.row.tone || "—"}</td><td className="px-4 py-3"><span className={`rounded-full border px-2 py-1 font-mono text-[11px] ${r.rowErrors.length ? "border-red-400 text-red-600" : "border-emerald-500 text-emerald-700"}`}>{r.rowErrors.length ? "failed" : "pending"}</span></td><td className="max-w-xs truncate px-4 py-3 text-ink/75" title={r.rowErrors.join(", ") || r.row.product_description || "Ready"}>{r.rowErrors.join(", ") || r.row.product_description || "Ready"}</td></tr>)}
              {results?.map((r) => <tr key={r.row_id} className="border-b border-paperLine/70 last:border-0"><td className="px-4 py-3 font-mono text-xs text-ink/58">{r.row_id}</td><td className="px-4 py-3 font-medium">{r.product_name}</td><td className="px-4 py-3 font-mono text-xs capitalize">{r.response?.platform ?? "—"}</td><td className="px-4 py-3 font-mono text-xs capitalize">{r.response?.tone ?? "—"}</td><td className="px-4 py-3"><span className={`rounded-full border px-2 py-1 font-mono text-[11px] ${r.status === "success" ? "border-emerald-600 text-emerald-700" : "border-red-500 text-red-600"}`}>{r.status === "success" ? "success" : "failed"}</span></td><td className="max-w-xs truncate px-4 py-3 font-serif text-ink/88" title={r.status === "success" ? r.response?.variations?.[0]?.headline : r.error}>{r.status === "success" ? r.response?.variations?.[0]?.headline : r.error}</td></tr>)}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
