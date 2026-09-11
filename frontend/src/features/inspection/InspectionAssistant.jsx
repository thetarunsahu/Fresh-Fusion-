import { useEffect, useMemo, useState } from "react";
import { AlertTriangle, Bot, CheckCircle2, Loader2, MessageCircle, Send, ShieldAlert, Sparkles } from "lucide-react";
import { askInspectionAssistant } from "../../api";
import "./inspection-assistant.css";

const nice = (value) => String(value || "info").replaceAll("_", " ").replaceAll("-", " ").replace(/\b\w/g, (c) => c.toUpperCase());

export default function InspectionAssistant({ session, proactive }) {
  const [question, setQuestion] = useState("");
  const [asking, setAsking] = useState(false);
  const [answer, setAnswer] = useState(null);
  const [error, setError] = useState("");
  const sampleId = session.sample?.sample_id;
  const recentEvents = session.report?.product?.events || [];
  const latestImportant = useMemo(
    () => recentEvents.find((event) => ["warning", "critical"].includes(event.severity)),
    [recentEvents],
  );

  useEffect(() => {
    setAnswer(null);
    setQuestion("");
    setError("");
  }, [sampleId]);

  const ask = async (event) => {
    event?.preventDefault();
    const clean = question.trim();
    if (!sampleId || clean.length < 2 || asking) return;
    setAsking(true);
    setError("");
    try {
      const result = await askInspectionAssistant(sampleId, clean);
      setAnswer({ ...result.response, mode: result.mode });
      setQuestion("");
      await session.refresh();
    } catch (err) {
      setError(err.message || "Assistant request failed.");
    } finally {
      setAsking(false);
    }
  };

  const severity = proactive?.severity || latestImportant?.severity || "info";

  return (
    <aside className={`ffAssistant ffPanel iaRoot ia-${severity}`}>
      <div className="ffAssistantTitle">
        <div className="ffAssistantIcon"><Sparkles size={18} /></div>
        <div>
          <span className="ffEyebrow">LIVE GUIDANCE · {nice(severity)}</span>
          <h2>FreshFusion Assistant</h2>
        </div>
      </div>

      {latestImportant && (
        <div className={`iaAlert ${latestImportant.severity}`}>
          {latestImportant.severity === "critical" ? <AlertTriangle size={15}/> : <ShieldAlert size={15}/>} 
          <span>{latestImportant.message}</span>
        </div>
      )}

      <div className="ffAssistantMessage">
        <div><b>What changed?</b><p>{proactive?.changed || "Inspection evidence is being monitored."}</p></div>
        <div><b>What does it mean?</b><p>{proactive?.meaning || "FreshFusion will hold the result if evidence is incomplete or inconsistent."}</p></div>
        <div className="ffNextAction"><b>What should you do?</b><p>{proactive?.action || "Continue the guided inspection workflow."}</p></div>
      </div>

      {answer && (
        <div className="iaAnswer">
          <div className="iaAnswerHead">
            <Bot size={15}/>
            <b>Answer</b>
            <span>{answer.mode === "gemma" ? "Gemma · evidence grounded" : "Local evidence fallback"}</span>
          </div>
          <p>{answer.answer}</p>
          {answer.evidence_used?.length > 0 && (
            <div className="iaEvidenceUsed">
              <small>Evidence used</small>
              <div>{answer.evidence_used.map((item) => <span key={item}><CheckCircle2 size={11}/>{item}</span>)}</div>
            </div>
          )}
          {answer.uncertainty && <small className="iaUncertainty">Limit: {answer.uncertainty}</small>}
          {answer.next_action && <div className="iaNext"><b>Next action</b><span>{answer.next_action}</span></div>}
        </div>
      )}

      <form className="ffAskBox iaAsk" onSubmit={ask}>
        <MessageCircle size={15}/>
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask: Why this result? What should I do?"
          maxLength={500}
          disabled={!sampleId || asking}
        />
        <button type="submit" disabled={!sampleId || question.trim().length < 2 || asking} aria-label="Ask FreshFusion Assistant">
          {asking ? <Loader2 className="iaSpin" size={16}/> : <Send size={16}/>} 
        </button>
      </form>
      {error && <small className="iaError">{error}</small>}
      <div className="ffAssistantFacts">
        <span><ShieldAlert size={14} /> Answers use current inspection evidence and previous verified context.</span>
        <span><ShieldAlert size={14} /> Assistant explanations never override the deterministic freshness decision.</span>
      </div>
    </aside>
  );
}
