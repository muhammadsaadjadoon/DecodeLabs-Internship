import { useEffect, useState } from "react";

const DIFF_SAMPLES = [
  {
    lang: "python",
    before: "if user.role = 'admin':",
    after: "if user.role == 'admin':",
    note: "assignment used instead of comparison",
  },
  {
    lang: "javascript",
    before: "for (let i = 0; i <= arr.length; i++)",
    after: "for (let i = 0; i < arr.length; i++)",
    note: "off-by-one array bound",
  },
  {
    lang: "cpp",
    before: "int total = a / b;",
    after: "int total = b != 0 ? a / b : 0;",
    note: "unguarded division by zero",
  },
];

export default function Hero({ onScrollToUpload }) {
  const [sampleIndex, setSampleIndex] = useState(0);
  const [animKey, setAnimKey] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setSampleIndex((i) => (i + 1) % DIFF_SAMPLES.length);
      setAnimKey((k) => k + 1);
    }, 4200);
    return () => clearInterval(interval);
  }, []);

  const sample = DIFF_SAMPLES[sampleIndex];

  return (
    <section className="mx-auto max-w-6xl px-6 pb-10 pt-14 sm:pt-20">
      <div className="grid items-center gap-12 lg:grid-cols-[1.05fr_1fr]">
        <div className="animate-fadeUp">
          <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-edge bg-raised px-3 py-1 font-mono text-[11px] text-brand">
            <span className="h-1.5 w-1.5 rounded-full bg-brand" />
            .py &nbsp;·&nbsp; .js &nbsp;·&nbsp; .ts &nbsp;·&nbsp; .java &nbsp;·&nbsp; .cpp &nbsp;·&nbsp; +more
          </div>

          <h1 className="font-mono text-4xl font-bold leading-[1.1] tracking-tight text-primary sm:text-5xl">
            Review. Fix.
            <br />
            <span className="text-brand">Improve.</span>
          </h1>

          <p className="mt-5 max-w-md text-[15px] leading-relaxed text-muted">
            Drop in any source file — CodeFix AI reads it like a senior reviewer,
            flags every bug with a plain-language explanation, and hands back a
            corrected, compilable version you can download in one click.
          </p>

          <div className="mt-8 flex flex-wrap items-center gap-3">
            <button
              onClick={onScrollToUpload}
              className="focus-ring rounded-lg bg-brand px-5 py-3 font-mono text-sm font-semibold text-ink transition hover:brightness-110 active:scale-[0.98]"
            >
              Review my code →
            </button>
            <span className="font-mono text-xs text-faint">no signup · your code never leaves this session</span>
          </div>
        </div>

        {/* Signature element: live terminal diff */}
        <div className="animate-fadeUp overflow-hidden rounded-xl border border-edge bg-surface shadow-panel" style={{ animationDelay: "120ms" }}>
          <div className="flex items-center gap-2 border-b border-edge bg-raised px-4 py-3">
            <span className="term-dot bg-bug/70" />
            <span className="term-dot bg-warn/70" />
            <span className="term-dot bg-fix/70" />
            <span className="ml-3 font-mono text-[11px] text-faint">codefix — {sample.lang}</span>
          </div>

          <div key={animKey} className="space-y-1 px-5 py-6 font-mono text-[13px] sm:text-sm">
            <div className="flex gap-3 text-bug/90">
              <span className="select-none text-bug/50">-</span>
              <span className="line-through decoration-bug/60">{sample.before}</span>
            </div>

            <div className="flex gap-3 text-fix">
              <span className="select-none text-fix/60">+</span>
              <span
                className="inline-block overflow-hidden whitespace-nowrap border-r-2 border-fix/70 pr-1"
                style={{ animation: "typeIn 1.6s steps(40, end) 0.5s both" }}
              >
                {sample.after}
              </span>
            </div>

            <p className="mt-4 border-t border-edgeSoft pt-4 text-xs text-faint">
              <span className="mr-2 rounded bg-fix/10 px-2 py-0.5 font-semibold text-fix">FIXED</span>
              {sample.note}
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
