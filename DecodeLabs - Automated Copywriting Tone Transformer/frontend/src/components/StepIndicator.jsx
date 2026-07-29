const STEPS = [
  { n: "01", label: "Brief" },
  { n: "02", label: "Generate" },
  { n: "03", label: "Refine" },
];

export default function StepIndicator({ active }) {
  return (
    <div className="flex flex-wrap items-center gap-3 font-mono text-[11px] uppercase tracking-[0.18em]">
      {STEPS.map((step, i) => {
        const isActive = i === active;
        const isDone = i < active;
        return (
          <div key={step.n} className="flex items-center gap-3">
            <span
              className={`flex items-center gap-2 rounded-full border px-3 py-1.5 transition-all ${
                isActive
                  ? "border-lex-cyan/60 bg-lex-cyan/10 text-lex-cyan shadow-glow"
                  : isDone
                  ? "border-lex-teal/40 bg-lex-teal/10 text-lex-teal"
                  : "border-white/10 bg-white/[0.03] text-white/35"
              }`}
            >
              <span className="text-[10px]">{step.n}</span>
              {step.label}
            </span>
            {i < STEPS.length - 1 && (
              <span className="hidden sm:block h-px w-8 bg-gradient-to-r from-white/20 to-transparent" aria-hidden="true" />
            )}
          </div>
        );
      })}
    </div>
  );
}
