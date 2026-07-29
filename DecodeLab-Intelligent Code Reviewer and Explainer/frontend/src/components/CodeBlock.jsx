import { useState } from "react";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";
import { LANGUAGE_MAP } from "../utils/language";
import Icon from "./Icon";

const syntaxTheme = {
  ...vscDarkPlus,
  'pre[class*="language-"]': {
    ...vscDarkPlus['pre[class*="language-"]'],
    background: "transparent",
    margin: 0,
    padding: "1.15rem 1rem 1.25rem",
    fontSize: "12.5px",
    lineHeight: "1.72",
  },
  'code[class*="language-"]': {
    ...vscDarkPlus['code[class*="language-"]'],
    background: "transparent",
    textShadow: "none",
  },
};

export function downloadCode(code, language, filename) {
  const meta = LANGUAGE_MAP[language] || { ext: "txt" };
  const blob = new Blob([code], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  const base = filename?.includes(".") ? filename.split(".").slice(0, -1).join(".") : filename || "reviewed-code";
  anchor.href = url;
  anchor.download = `${base}.fixed.${meta.ext}`;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

export default function CodeBlock({ code, language, filename, showHeader = true, maxHeight = 560 }) {
  const [copied, setCopied] = useState(false);
  const meta = LANGUAGE_MAP[language] || { label: language || "Code", highlightLang: "text", ext: "txt" };
  const outputName = filename?.includes(".")
    ? filename.replace(/\.[^.]+$/, `.fixed.${meta.ext}`)
    : `${filename || "reviewed-code"}.fixed.${meta.ext}`;

  async function copy() {
    await navigator.clipboard.writeText(code);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1600);
  }

  return (
    <section className="analysis-section code-section">
      {showHeader && (
        <div className="section-title-row">
          <div>
            <span className="section-kicker">Corrected output</span>
            <h3>Production-ready code</h3>
          </div>
          <div className="code-actions">
            <button type="button" className="secondary-action" onClick={copy}>
              <Icon name="copy" size={15} /> {copied ? "Copied" : "Copy"}
            </button>
            <button type="button" className="primary-action small" onClick={() => downloadCode(code, language, filename)}>
              <Icon name="download" size={15} /> Download
            </button>
          </div>
        </div>
      )}

      <div className="code-window">
        <div className="code-window-bar">
          <div className="window-dots"><i /><i /><i /></div>
          <span>{outputName}</span>
          <em>{meta.label}</em>
        </div>
        <div className="code-scroll" style={{ maxHeight }}>
          <SyntaxHighlighter
            language={meta.highlightLang}
            style={syntaxTheme}
            showLineNumbers
            wrapLongLines={false}
            lineNumberStyle={{ color: "#4b5770", minWidth: "2.6em", paddingRight: "1.1em" }}
          >
            {code}
          </SyntaxHighlighter>
        </div>
      </div>
    </section>
  );
}
