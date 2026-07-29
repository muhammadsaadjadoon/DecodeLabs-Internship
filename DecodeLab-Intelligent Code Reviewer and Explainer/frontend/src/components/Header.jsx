export default function Header() {
  return (
    <header className="sticky top-0 z-20 border-b border-edge/70 bg-ink/80 backdrop-blur-md">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-edge bg-raised font-mono text-brand shadow-glowBrand">
            &gt;_
          </div>
          <div className="leading-tight">
            <p className="font-mono text-[15px] font-semibold tracking-tight text-primary">
              CodeFix<span className="text-brand">AI</span>
            </p>
            <p className="text-[11px] text-faint">Intelligent Code Review &amp; Correction</p>
          </div>
        </div>

        <div className="hidden items-center gap-2 rounded-full border border-edge bg-raised px-3 py-1.5 text-xs text-muted sm:flex">
          <span className="h-1.5 w-1.5 rounded-full bg-fix animate-pulseDot" />
          Gemini-powered analysis engine
        </div>
      </div>
    </header>
  );
}
