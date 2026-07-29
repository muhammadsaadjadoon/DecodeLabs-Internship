import { useMemo, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";
import BugReport from "./BugReport";
import CodeBlock, { downloadCode } from "./CodeBlock";
import AnalysisLoading from "./AnalysisLoading";
import Icon from "./Icon";
import { LANGUAGE_MAP } from "../utils/language";

const codePreviewTheme = {
  ...vscDarkPlus,
  'pre[class*="language-"]': {
    ...vscDarkPlus['pre[class*="language-"]'],
    background: "transparent",
    margin: 0,
    padding: "1rem",
    fontSize: "12px",
    lineHeight: "1.65",
  },
  'code[class*="language-"]': {
    ...vscDarkPlus['code[class*="language-"]'],
    background: "transparent",
  },
};

function EmptyWorkspace({ theme }) {
  return (
    <section className="empty-workspace">
      <div className="hero-logo"><img src={theme === "light" ? "/codefix-logo-light.png" : "/codefix-logo.png"} alt="CodeFix AI" /></div>
      <span className="eyebrow">AI-powered code intelligence</span>
      <h1>Review code with senior-level precision.</h1>
      <p>
        Attach a source file or paste code to receive a structured defect report,
        corrected implementation, and an optional line-by-line explanation.
      </p>
    </section>
  );
}

function UserSubmission({ session, profile }) {
  const meta = LANGUAGE_MAP[session.language] || { label: session.language || "Code", highlightLang: "text" };
  const displayName = profile?.name || "You";
  const initials = displayName
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase() || "YO";

  return (
    <article className="user-chat-message">
      <div className="user-message">
        <div className="user-message-identity">
          <div>
            <strong>{displayName}</strong>
            <span>Submitted code for review</span>
          </div>
          <span>{session.sourceCode?.split("\n").length || 0} lines</span>
        </div>
        <div className="user-message-header">
          <div>
            <span className="file-badge"><Icon name="file" size={15} /> {session.filename}</span>
            <span className="language-badge">{meta.label}</span>
          </div>
        </div>
        <div className="submitted-code-preview">
          <SyntaxHighlighter language={meta.highlightLang} style={codePreviewTheme} showLineNumbers>
            {session.sourceCode || ""}
          </SyntaxHighlighter>
        </div>
      </div>
      {profile?.avatarUrl ? (
        <img className="user-chat-avatar user-chat-avatar-image" src={profile.avatarUrl} alt={displayName} />
      ) : (
        <div className="user-chat-avatar" aria-label={displayName}>{initials}</div>
      )}
    </article>
  );
}

function ExplanationPanel({ explanation }) {
  return (
    <section className="analysis-section explanation-panel">
      <div className="section-title-row">
        <div><span className="section-kicker">Code walkthrough</span><h3>Line-by-line explanation</h3></div>
        <span className="status-pill neutral"><Icon name="layers" size={14} /> Guided walkthrough</span>
      </div>
      <div className="explanation-prose">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            h2: ({ children }) => <h4>{children}</h4>,
            h3: ({ children }) => <h5>{children}</h5>,
            ul: ({ children }) => <ul>{children}</ul>,
            ol: ({ children }) => <ol>{children}</ol>,
            li: ({ children }) => <li>{children}</li>,
            code: ({ inline, children }) => inline
              ? <code className="inline-code">{children}</code>
              : <code>{children}</code>,
          }}
        >
          {explanation}
        </ReactMarkdown>
      </div>
    </section>
  );
}

export default function ReviewWorkspace({ session, loading, pendingInput, onExplain, explaining, theme, profile }) {
  const [tab, setTab] = useState("overview");
  const result = session?.result;
  const issueCount = useMemo(() => {
    if (!result?.bug_report) return 0;
    return (result.bug_report.match(/^\s*-\s+/gm) || []).length;
  }, [result]);

  if (!session && !loading) return <EmptyWorkspace theme={theme} />;

  const current = session || pendingInput;

  return (
    <section className="conversation-stream">
      {current && <UserSubmission session={current} profile={profile} />}
      {loading ? (
        <AnalysisLoading theme={theme} />
      ) : result ? (
        <article className="assistant-message">
          <div className="assistant-avatar"><img src={theme === "light" ? "/codefix-logo-light.png" : "/codefix-logo.png"} alt="" /></div>
          <div className="assistant-card review-result-card">
            <div className="review-summary-header">
              <div>
                <span className="assistant-name">CodeFix AI</span>
                <h2>{result.has_issues ? "Review completed with recommended fixes" : "Review completed — code verified"}</h2>
                <p>
                  {result.has_issues
                    ? "The analysis identified concrete issues and produced a corrected implementation."
                    : "No functional, security, or performance defects were detected. The verified code is preserved below."}
                </p>
              </div>
              <span className={`review-score ${result.has_issues ? "attention" : "verified"}`}>
                <Icon name={result.has_issues ? "alert" : "shield"} size={18} />
                <strong>{result.has_issues ? `${issueCount || "Review"} finding${issueCount === 1 ? "" : "s"}` : "Verified"}</strong>
              </span>
            </div>

            <div className="result-metadata">
              <span><Icon name="file" size={14} /> {result.filename}</span>
              <span><Icon name="code" size={14} /> {result.language}</span>
              <span><Icon name="sparkles" size={14} /> AI quality review</span>
            </div>

            <div className="result-tabs" role="tablist">
              {[
                ["overview", "Overview"],
                ["issues", "Findings"],
                ["code", "Corrected code"],
                ["explain", "Line by line"],
              ].map(([key, label]) => (
                <button key={key} type="button" className={tab === key ? "active" : ""} onClick={() => setTab(key)}>
                  {label}
                </button>
              ))}
            </div>

            {tab === "overview" && (
              <div className="overview-grid">
                <BugReport markdown={result.bug_report} hasIssues={result.has_issues} />
                <CodeBlock code={result.refactored_code} language={result.language} filename={result.filename} />
              </div>
            )}
            {tab === "issues" && <BugReport markdown={result.bug_report} hasIssues={result.has_issues} />}
            {tab === "code" && <CodeBlock code={result.refactored_code} language={result.language} filename={result.filename} maxHeight={720} />}
            {tab === "explain" && (
              session.explanation ? (
                <ExplanationPanel explanation={session.explanation} />
              ) : (
                <div className="explain-empty">
                  <div className="explain-icon"><Icon name="layers" size={25} /></div>
                  <h3>Understand the corrected code in depth</h3>
                  <p>Generate a structured walkthrough covering purpose, execution flow, and each meaningful line or block.</p>
                  <button type="button" className="primary-action" onClick={onExplain} disabled={explaining}>
                    {explaining ? <><span className="spinner" /> Building explanation…</> : <><Icon name="sparkles" size={17} /> Explain line by line</>}
                  </button>
                </div>
              )
            )}

            <div className="assistant-actions">
              <button type="button" className="secondary-action" onClick={() => navigator.clipboard.writeText(result.refactored_code)}>
                <Icon name="copy" size={15} /> Copy corrected code
              </button>
              <button type="button" className="secondary-action" onClick={() => downloadCode(result.refactored_code, result.language, result.filename)}>
                <Icon name="download" size={15} /> Download file
              </button>
              <button type="button" className="secondary-action" onClick={() => { setTab("explain"); if (!session.explanation) onExplain(); }} disabled={explaining}>
                <Icon name="layers" size={15} /> {session.explanation ? "View explanation" : "Explain code"}
              </button>
            </div>
          </div>
        </article>
      ) : null}
    </section>
  );
}
