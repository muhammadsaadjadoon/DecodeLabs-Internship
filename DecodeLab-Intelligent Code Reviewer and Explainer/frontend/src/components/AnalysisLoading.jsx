import { useEffect, useState } from "react";
import Icon from "./Icon";

const STEPS = [
  "Reading source structure",
  "Tracing logic and control flow",
  "Evaluating defects and risks",
  "Validating corrected output",
];

export default function AnalysisLoading({ theme }) {
  const [active, setActive] = useState(0);

  useEffect(() => {
    const timer = window.setInterval(() => {
      setActive((value) => Math.min(value + 1, STEPS.length - 1));
    }, 900);
    return () => window.clearInterval(timer);
  }, []);

  return (
    <article className="assistant-message loading-message">
      <div className="assistant-avatar"><img src={theme === "light" ? "/codefix-logo-light.png" : "/codefix-logo.png"} alt="" /></div>
      <div className="assistant-card">
        <div className="assistant-heading">
          <div><span>CodeFix AI</span><strong>Review in progress</strong></div>
          <span className="live-indicator"><i /> Analysis active</span>
        </div>
        <div className="analysis-progress">
          {STEPS.map((step, index) => (
            <div className={`progress-step ${index < active ? "done" : index === active ? "active" : ""}`} key={step}>
              <span>{index < active ? <Icon name="check" size={13} /> : index + 1}</span>
              <p>{step}</p>
            </div>
          ))}
        </div>
      </div>
    </article>
  );
}
