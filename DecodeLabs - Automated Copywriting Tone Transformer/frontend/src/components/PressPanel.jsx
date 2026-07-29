import { useEffect, useMemo, useState } from "react";
import CompilingTicker from "./CompilingTicker.jsx";

function CharMeter({ count, max, compliant }) {
  const pct = Math.min(100, (count / Math.max(1, max)) * 100);
  return (
    <div>
      <div className="mb-2 flex justify-between font-mono text-[11px] text-ink/45">
        <span>{count} / {max} characters</span>
        <span className={compliant ? "text-emerald-700" : "text-red-600"}>
          {compliant ? "within budget" : "over budget"}
        </span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-paperLine">
        <div
          className={`h-full rounded-full ${compliant ? "bg-gradient-to-r from-emerald-500 to-cyan-500" : "bg-red-500"}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

function buildText(variation) {
  if (!variation) return "";
  return `${variation.headline}\n\n${variation.body}\n\n${variation.call_to_action}${
    variation.hashtags?.length ? "\n\n" + variation.hashtags.map((tag) => (tag.startsWith("#") ? tag : `#${tag}`)).join(" ") : ""
  }`;
}

function countWords(text) {
  return text.trim() ? text.trim().split(/\s+/).length : 0;
}

export default function PressPanel({ loading, error, result, onRegenerate, onFavourite, onSaveOutput, onClear }) {
  const [activeIndex, setActiveIndex] = useState(0);
  const [editedMap, setEditedMap] = useState({});
  const [copied, setCopied] = useState(false);
  const variations = result?.variations || (result?.copy ? [result.copy] : []);
  const edited = editedMap[activeIndex] || null;
  const active = edited || variations[activeIndex] || null;

  useEffect(() => {
    setActiveIndex(0);
    setEditedMap({});
  }, [result]);

  const text = useMemo(() => buildText(active), [active]);
  const charCount = text.length;
  const wordCount = countWords(text);

  const handleCopy = async () => {
    if (!active) return;
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  const downloadTxt = () => {
    if (!active) return;
    const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `lexora-${active.style || "output"}.txt`.toLowerCase().replaceAll(" ", "-");
    a.click();
    URL.revokeObjectURL(url);
  };

  const updateEdited = (key, value) => {
    const base = editedMap[activeIndex] || active;
    const next = { ...base, [key]: value, char_count: buildText({ ...base, [key]: value }).length };
    setEditedMap((prev) => ({ ...prev, [activeIndex]: next }));
  };

  const regenerateSelected = () => {
    setEditedMap((prev) => { const next = { ...prev }; delete next[activeIndex]; return next; });
    onRegenerate?.();
  };

  return (
    <div className="relative h-full">
      <div className="absolute -inset-1 rounded-[2.2rem] bg-gradient-to-br from-lex-cyan/24 via-transparent to-lex-teal/18 blur-xl" />
      <div className="relative flex min-h-[620px] flex-col rounded-[2rem] border border-white/70 bg-paper p-5 text-ink shadow-paper sm:p-7">
        <div className="mb-6 flex flex-wrap items-center justify-between gap-3 border-b border-paperLine pb-4">
          <div>
            <span className="font-mono text-[11px] uppercase tracking-[0.24em] text-ink/42">Lexora Output</span>
            <h3 className="mt-2 font-display text-xl font-bold text-ink">Safe · Creative · Bold</h3>
          </div>
          {result && (
            <span className="rounded-full border border-ink/10 bg-white/70 px-3 py-1.5 font-mono text-[11px] uppercase tracking-wider text-ink/60">
              {result.platform}
            </span>
          )}
        </div>

        {error && (
          <div className="flex flex-1 items-center justify-center text-center">
            <div className="max-w-sm rounded-2xl border border-red-200 bg-red-50 px-5 py-6">
              <p className="mb-1 font-display font-bold text-red-700">Generation failed</p>
              <p className="text-sm text-ink/60">{error}</p>
            </div>
          </div>
        )}

        {!error && loading && (
          <div className="flex flex-1 items-center justify-center">
            <div className="w-full max-w-md rounded-2xl bg-midnight p-1 shadow-premium">
              <CompilingTicker />
            </div>
          </div>
        )}

        {!error && !loading && !result && (
          <div className="flex flex-1 items-center justify-center text-center">
            <div className="max-w-sm">
              <div className="mx-auto mb-5 flex h-16 w-16 items-center justify-center rounded-2xl border border-lex-cyan/25 bg-cyan-50 text-2xl">✦</div>
              <p className="mb-2 font-display text-xl font-bold text-ink/75">Nothing generated yet</p>
              <p className="text-sm leading-relaxed text-ink/45">Fill the brief and Lexora will create multiple controlled variations here.</p>
            </div>
          </div>
        )}

        {!error && !loading && result && active && (
          <div className="rise-in flex flex-1 flex-col gap-5">
            <div className="flex flex-wrap gap-2">
              {variations.map((item, index) => (
                <button
                  key={`${item.style}-${index}`}
                  onClick={() => setActiveIndex(index)}
                  className={`rounded-full border px-3 py-2 text-xs font-bold transition ${
                    activeIndex === index
                      ? "border-cyan-500 bg-cyan-50 text-cyan-700"
                      : "border-ink/10 bg-white/60 text-ink/55 hover:border-cyan-300 hover:text-cyan-700"
                  }`}
                >
                  {item.style || `Version ${index + 1}`}
                </button>
              ))}
              {edited && <span className="rounded-full border border-amber-300 bg-amber-50 px-3 py-2 text-xs font-bold text-amber-700">Unsaved changes</span>}
            </div>

            <div className="thin-scroll max-h-[520px] overflow-y-auto rounded-3xl border border-paperLine bg-white/60 p-4">
              <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                <p className="font-mono text-[11px] uppercase tracking-[0.18em] text-ink/40">Output editor</p>
                <div className="flex flex-wrap gap-2 text-[11px] font-mono text-ink/45">
                  <span>{wordCount} words</span>
                  <span>{charCount} chars</span>
                </div>
              </div>

              <input
                value={active.headline}
                onChange={(e) => updateEdited("headline", e.target.value)}
                className="w-full rounded-2xl border border-paperLine bg-white px-4 py-3 font-serif text-2xl font-semibold leading-tight text-ink outline-none focus:border-cyan-400"
              />
              <textarea
                value={active.body}
                onChange={(e) => updateEdited("body", e.target.value)}
                rows={7}
                className="thin-scroll mt-3 w-full resize-y rounded-2xl border border-paperLine bg-white px-4 py-3 font-serif text-[16px] leading-relaxed text-ink/82 outline-none focus:border-cyan-400"
              />
              <input
                value={active.call_to_action}
                onChange={(e) => updateEdited("call_to_action", e.target.value)}
                className="mt-3 w-full rounded-2xl border border-paperLine bg-white px-4 py-3 font-serif text-[16px] font-semibold italic text-ink outline-none focus:border-cyan-400"
              />
            </div>

            {active.hashtags?.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {active.hashtags.map((tag, index) => (
                  <span key={`${tag}-${index}`} className="rounded-full border border-cyan-300/70 bg-cyan-50 px-3 py-1.5 font-mono text-[11px] text-cyan-800">
                    {tag.startsWith("#") ? tag : `#${tag}`}
                  </span>
                ))}
              </div>
            )}

            <div className="mt-auto space-y-4 border-t border-paperLine pt-5">
              <CharMeter count={active.char_count || charCount} max={active.max_chars || result.max_chars} compliant={active.compliant ?? charCount <= result.max_chars} />
              <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-6">
                <button onClick={handleCopy} className="rounded-xl border border-ink/15 px-3 py-2 text-xs font-bold text-ink/70 transition hover:border-ink/45 hover:text-ink">{copied ? "Copied" : "Copy"}</button>
                <button onClick={() => onSaveOutput?.(active)} className="rounded-xl border border-ink/15 px-3 py-2 text-xs font-bold text-ink/70 transition hover:border-ink/45 hover:text-ink">Save</button>
                <button onClick={regenerateSelected} className="rounded-xl border border-ink/15 px-3 py-2 text-xs font-bold text-ink/70 transition hover:border-ink/45 hover:text-ink">Regenerate</button>
                <button onClick={() => onFavourite?.(active)} className="rounded-xl border border-ink/15 px-3 py-2 text-xs font-bold text-ink/70 transition hover:border-ink/45 hover:text-ink">Favourite</button>
                <button onClick={downloadTxt} className="rounded-xl border border-ink/15 px-3 py-2 text-xs font-bold text-ink/70 transition hover:border-ink/45 hover:text-ink">Download</button>
                <button onClick={onClear} className="rounded-xl border border-red-300/40 px-3 py-2 text-xs font-bold text-red-700 transition hover:bg-red-50">Clear</button>
              </div>
              <div className="flex flex-wrap items-center justify-between gap-2 font-mono text-[11px] text-ink/40">
                <span>temp {result.temperature?.toFixed?.(2)} · top_p {result.top_p?.toFixed?.(2)} · tone {result.tone}</span>
                <span>edit directly, then copy or download</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
