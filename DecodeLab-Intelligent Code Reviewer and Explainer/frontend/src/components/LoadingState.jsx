import { useEffect, useState } from "react";

const STEPS = [
  "Ingesting source payload",
  "Parsing syntax & structure",
  "Running Gemini analysis",
  "Validating structured output",
];

export default function LoadingState() {
  const [activeStep, setActiveStep] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setActiveStep((s) => (s < STEPS.length - 1 ? s + 1 : s));
    }, 900);
    return () => clearInterval(interval);
  }, []);

  return (
    <section className="mx-auto max-w-6xl px-6 py-6">
      <div className="rounded-xl border border-edge bg-surface p-8 shadow-panel">
        <div className="space-y-4">
          {STEPS.map((step, i) => (
            <div key={step} className="flex items-center gap-3 font-mono text-sm">
              <span
                className={`flex h-5 w-5 items-center justify-center rounded-full border text-[11px] ${
                  i < activeStep
                    ? "border-fix bg-fix/10 text-fix"
                    : i === activeStep
                    ? "border-brand text-brand animate-pulseDot"
                    : "border-edge text-faint"
                }`}
              >
                {i < activeStep ? "✓" : i + 1}
              </span>
              <span className={i <= activeStep ? "text-primary" : "text-faint"}>{step}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
