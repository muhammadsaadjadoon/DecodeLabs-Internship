import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import Icon from "./Icon";

function getSeverity(children) {
  const text = Array.isArray(children)
    ? children.map((child) => (typeof child === "string" ? child : child?.props?.children)).join(" ")
    : String(children);
  const lower = text.toLowerCase();
  if (lower.includes("critical")) return "critical";
  if (lower.includes("warning")) return "warning";
  return "info";
}

function ListItem({ children }) {
  const severity = getSeverity(children);
  return (
    <li className={`issue-row ${severity}`}>
      <span className="issue-marker"><Icon name={severity === "info" ? "check" : "alert"} size={13} /></span>
      <div>{children}</div>
    </li>
  );
}

export default function BugReport({ markdown, hasIssues, showHeader = true }) {
  return (
    <section className="analysis-section">
      {showHeader && (
        <div className="section-title-row">
          <div>
            <span className="section-kicker">Review findings</span>
            <h3>{hasIssues ? "Issues requiring attention" : "No issues detected"}</h3>
          </div>
          <span className={`status-pill ${hasIssues ? "warning" : "success"}`}>
            <Icon name={hasIssues ? "bug" : "check"} size={14} />
            {hasIssues ? "Action recommended" : "Code verified"}
          </span>
        </div>
      )}
      <div className="bug-report-prose">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            li: ListItem,
            ul: ({ children }) => <ul>{children}</ul>,
            p: ({ children }) => <p>{children}</p>,
            code: ({ children }) => <code className="inline-code">{children}</code>,
            strong: ({ children }) => <strong>{children}</strong>,
          }}
        >
          {markdown}
        </ReactMarkdown>
      </div>
    </section>
  );
}
