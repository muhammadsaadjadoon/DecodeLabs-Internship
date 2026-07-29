import { useEffect, useState } from "react";

const STAGES = [
  "reading product facts",
  "mapping audience intent",
  "selecting tone rules",
  "optimizing platform length",
  "generating Lexora draft",
  "validating final copy",
];

export default function CompilingTicker() {
  const [index, setIndex] = useState(0);

  useEffect(() => {
    const id = setInterval(() => {
      setIndex((prev) => (prev + 1 < STAGES.length ? prev + 1 : prev));
    }, 650);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="rounded-2xl border border-white/10 bg-midnight/80 p-5 font-mono text-xs text-white/70">
      <div className="mb-4 flex items-center gap-2 text-white/45">
        <span className="h-2 w-2 rounded-full bg-lex-cyan animate-pulse" />
        lexora_engine.run()
      </div>
      <ul className="space-y-2">
        {STAGES.map((stage, i) => (
          <li
            key={stage}
            className={`transition-opacity duration-300 ${
              i <= index ? "opacity-100" : "opacity-25"
            }`}
          >
            <span className="text-lex-cyan">{i < index ? "✓" : i === index ? ">" : "·"}</span>{" "}
            {stage}
            {i === index && <span className="ticker-cursor">▍</span>}
          </li>
        ))}
      </ul>
    </div>
  );
}
