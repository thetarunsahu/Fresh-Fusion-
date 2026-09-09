import { useState } from "react";
import {
  Bot,
  Database,
  FileSearch,
  History,
  RadioTower,
  Send,
  ShieldCheck,
} from "lucide-react";
import { explainInvestigation } from "../../api";
import { Panel, StatusChip } from "../../shared/Panel";

const suggestions = [
  "Why is this assessment locked?",
  "What evidence is missing?",
  "Explain sensor contribution",
  "What did the reference retrieval find?",
  "What should I capture next?",
];

export default function AICopilot({ session }) {
  const report = session.report;
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const sources = [
    ["Current sample evidence", Boolean(report?.evidence), FileSearch],
    ["Sensor telemetry", Boolean(report?.evidence?.sensors?.latest), RadioTower],
    ["Reference context", Boolean(report?.analysts?.reference), Database],
    ["Human / inspection history", Boolean(report?.human_verifications?.length || report?.timeline?.length), History],
  ];
  const availableCount = sources.filter(([, available]) => available).length;

  async function ask(text = question) {
    const prompt = text.trim();
    if (!prompt || !session.sample?.sample_id || busy) return;
    setQuestion("");
    setBusy(true);
    setError("");
    setMessages((current) => [...current, { type: "user", text: prompt }]);
    try {
      const response = await explainInvestigation(session.sample.sample_id, prompt);
      if (response.status !== "ready" || !response.explanation) {
        throw new Error(
          response.status === "model-not-installed"
            ? "Gemma is not installed in Ollama."
            : "Local Ollama is unavailable. The deterministic verdict remains unaffected.",
        );
      }
      setMessages((current) => [
        ...current,
        {
          type: "assistant",
          text: response.explanation.summary,
          supporting: response.explanation.supporting_evidence || [],
          contradictions: response.explanation.contradictions || [],
          missing: response.explanation.missing_evidence || [],
          next: response.explanation.recommended_next_step,
          snapshotId: response.snapshot_id,
        },
      ]);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="featurePage aiCopilotPage ffCopilotPage">
      <div className="pageIntro ffCopilotIntro">
        <span className="eyebrow">AI COPILOT</span>
        <h1>Ask the evidence — not a generic chatbot.</h1>
        <p>
          Local Gemma answers only from the selected FreshFusion investigation.
          Retrieved evidence remains visible beside every conversation, and the
          deterministic critic/fusion path remains the verdict authority.
        </p>
      </div>

      <section className="ffCopilotStatusBar">
        <div className="chipRow">
          <StatusChip tone="good">Gemma 3</StatusChip>
          <StatusChip>Ollama local</StatusChip>
          <StatusChip tone="good">RAG enabled</StatusChip>
          <StatusChip>Explanation only</StatusChip>
        </div>
        <span>{availableCount} / {sources.length} evidence groups available</span>
      </section>

      <section className="ffCopilotLayout">
        <Panel title="Evidence-grounded local reasoning" eyebrow="AI COPILOT" className="ffChatPanel">
          <div className="ffChatFeed">
            {!messages.length && (
              <div className="ffChatWelcome">
                <span><Bot size={22} /></span>
                <h3>Ask about the selected inspection.</h3>
                <p>Questions are sent with the current evidence snapshot, analyst outputs, critic state and deterministic decision.</p>
              </div>
            )}
            {messages.map((message, index) => (
              <div className={`ffChatMessage ${message.type}`} key={`${message.type}-${index}`}>
                <span className="ffChatRole">{message.type === "user" ? "YOU" : "GEMMA · GROUNDED RESPONSE"}</span>
                <p>{message.text}</p>
                {message.type === "assistant" && (
                  <div className="ffChatEvidence">
                    {!!message.supporting?.length && <div><b>Supporting evidence</b><span>{message.supporting.join(" · ")}</span></div>}
                    {!!message.contradictions?.length && <div><b>Contradictions</b><span>{message.contradictions.join(" · ")}</span></div>}
                    {!!message.missing?.length && <div><b>Missing evidence</b><span>{message.missing.join(" · ")}</span></div>}
                    <div className="next"><b>Recommended next step</b><span>{message.next || "Review the deterministic investigation."}</span></div>
                    {message.snapshotId && <small>Evidence snapshot #{message.snapshotId}</small>}
                  </div>
                )}
              </div>
            ))}
            {busy && <div className="ffChatThinking"><span /><span /><span /> Gemma is reading the retrieved evidence…</div>}
          </div>

          {error && <div className="notice">{error}</div>}

          <div className="ffSuggestedQuestions">
            {suggestions.map((text) => (
              <button key={text} type="button" onClick={() => ask(text)} disabled={!session.sample || busy}>{text}</button>
            ))}
          </div>

          <form className="ffChatComposer" onSubmit={(event) => { event.preventDefault(); ask(); }}>
            <input
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              placeholder={session.sample ? "Ask about this sample, evidence, sensors or missing data…" : "Select an inspection first…"}
              disabled={!session.sample || busy}
              maxLength={600}
              aria-label="Ask FreshFusion AI Copilot"
            />
            <button className="primary" type="submit" disabled={!question.trim() || !session.sample || busy}>
              <Send size={15} /> Ask
            </button>
          </form>
        </Panel>

        <aside className="ffCopilotSide">
          <Panel title="Retrieved context" eyebrow="VISIBLE SOURCE PROOF">
            <div className="ffRetrievedSources">
              {sources.map(([label, available, Icon]) => (
                <div key={label} className={available ? "available" : "waiting"}>
                  <span><Icon size={15} /> {label}</span>
                  <StatusChip tone={available ? "good" : "neutral"}>{available ? "Retrieved" : "Waiting"}</StatusChip>
                </div>
              ))}
            </div>
          </Panel>

          <Panel title="Verdict authority" eyebrow="AI GUARDRAIL" className="ffGuardrailCard">
            <ShieldCheck size={20} />
            <p>Gemma explains and answers questions. It cannot unlock the verdict, invent calibration, or replace deterministic critic/fusion logic.</p>
          </Panel>

          <Panel title="Selected inspection" eyebrow={session.sample?.sample_id || "NO SAMPLE"}>
            <div className="ffSourceMini">
              <span>Critic</span><b>{report?.critic?.status || "Waiting"}</b>
              <span>Decision</span><b>{report?.decision?.status || "Waiting"}</b>
              <span>Fruit</span><b>{session.sample?.fruit_type || "—"}</b>
            </div>
          </Panel>
        </aside>
      </section>
    </div>
  );
}
