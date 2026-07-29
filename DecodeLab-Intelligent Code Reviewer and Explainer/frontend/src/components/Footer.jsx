export default function Footer() {
  return (
    <footer className="border-t border-edge/70 py-8">
      <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-2 px-6 text-center font-mono text-[11px] text-faint sm:flex-row sm:text-left">
        <p>CodeFix AI — Intelligent Code Review &amp; Correction</p>
        <p>Built with FastAPI · Gemini · React</p>
      </div>
    </footer>
  );
}
