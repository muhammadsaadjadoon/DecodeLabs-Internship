import BugReport from "./BugReport";
import CodeBlock from "./CodeBlock";

export default function ResultsPanel({ result, onReset }) {
  if (!result) return null;

  return (
    <section className="mx-auto max-w-6xl px-6 pb-20 pt-2 animate-fadeUp">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2 font-mono text-xs text-faint">
          <span className="rounded border border-edge bg-raised px-2 py-1 text-muted">{result.filename}</span>
          <span className="rounded border border-edge bg-raised px-2 py-1 text-brand">{result.language}</span>
          <span className="rounded border border-edge bg-raised px-2 py-1 text-muted">{result.model_used}</span>
        </div>
        <button
          onClick={onReset}
          className="focus-ring rounded-md border border-edge px-3 py-1.5 font-mono text-xs text-muted hover:border-faint hover:text-primary"
        >
          ← Review another file
        </button>
      </div>

      <div className="grid gap-6 rounded-xl border border-edge bg-surface p-6 shadow-panel lg:grid-cols-2">
        <BugReport markdown={result.bug_report} hasIssues={result.has_issues} />
        <CodeBlock code={result.refactored_code} language={result.language} filename={result.filename} />
      </div>
    </section>
  );
}
