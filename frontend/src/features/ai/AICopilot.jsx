import { useEffect, useState } from "react";
import {
  Bot,
  Database,
  FileSearch,
  History,
  RadioTower,
  Send,
  ShieldCheck,
} from "lucide-react";
import { explainInvestigation, ollamaHealth } from "../../api";
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
  const [ollama, setOllama] = useState(null);

  const cameraRecent = report?.evidence?.camera?.recent === true;
  const physicalSensorRecent = report?.evidence?.sensors?.physical_present === true;
  const hasLiveEvidence = cameraRecent || physicalSensorRecent;
  const ollamaReady = ollama?.available === true && ollama?.model_installed !== false;
  const canAsk = Boolean(
    session.sample?.sample_id &&
      report &&
      hasLiveEvidence &&
      ollamaReady &&
      !busy,
  );

  useEffect(() => {
    setQuestion("");
    setMessages([]);
    setError("");
  }, [session.sample?.sample_id]);

  useEffect(() => {
    let disposed = false;
    let timer;

    const check = async () => {
      if (!session.online) {
        if (!disposed) setOllama({ available: false, model_installed: false });
      } else {
        try {
          const value = await ollamaHealth();
          if (!disposed) setOllama(value);
        } catch (healthError) {
          if (!disposed) {
            setOllama({
              available: false,
              model_installed: false,
              error: healthError.message,
            });
          }
        }
      }
      if (!disposed) timer = setTimeout(check, 5000);
    };

    check();
    return () => {
      disposed = true;
      clearTimeout(timer);
    };
  }, [session.online]);

  const sources = [
    ["Current sample evidence", Boolean(report?.evidence), FileSearch],
    ["Recent phone camera", cameraRecent, FileSearch],
    ["Recent hardware telemetry", physicalSensorRecent, RadioTower],
    ["Reference context", Boolean(report?.analysts?.reference), Database],
    ["Human / inspection history", Boolean(report?.human_verifications?.length || report?.timeline?.length), History],
  ];
  const availableCount = sources.filter(([, available]) => available).length;

  async function ask(text = question) {
    const prompt = text.trim();
    if (!prompt || !canAsk) return;
    setQuestion("");
    setBusy(true);
    setError("");
    setMessages((current) => [...current, { type: "user", text: prompt }]);
    try {
      const response = await explainInvestigation(session.sample.sample_id, prompt);
      if (response.status !== "ready" || !response.explanation) {
        throw new Error(
          response.status === "model-not-installed"
            ? "Gemma 3 is not installed in Ollama. Run setup_ollama.ps1 once."
            : "Local Ollama is unavailable. Start Ollama and retry. The deterministic verdict remains unaffected.",
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
      try {
        setOllama(await ollamaHealth());
      } catch {
        setOllama({ available: false, model_installed: false });
      }
    } finally {
      setBusy(false);
    }
  }

  const welcomeTitle = !hasLiveEvidence
    ? "Collect live evidence first."
    : !ollamaReady
      ? "Local AI runtime is not ready."
      : "Ask about the selected inspection.";

  const welcomeCopy = !hasLiveEvidence
    ? "The Copilot stays locked until a recent phone-camera frame or physical ESP32 reading exists for the selected inspection. This prevents old or empty samples from looking like live AI analysis."
    : !ollamaReady
      ? "FreshFusion evidence is available, but Gemma cannot answer until Ollama is online with gemma3:4b installed. The deterministic investigation continues to work without the LLM."
      : "Questions are sent with the current evidence snapshot, analyst outputs, critic state and deterministic decision.";

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
          <StatusChip tone={ollamaReady ? "good" : "warning"}>
            {ollamaReady ? "Gemma 3 ready" : ollama === null ? "Checking Gemma" : "Gemma unavailable"}
          </StatusChip>
          <StatusChip tone={ollama?.available ? "good" : "neutral"}>
            {ollama?.available ? "Ollama online" : "Ollama offline"}
          </StatusChip>
          <StatusChip tone={hasLiveEvidence ? "good" : "warning"}>
            {hasLiveEvidence ? "Live evidence ready" : "Live evidence required"}
          </StatusChip>
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
                <h3>{welcomeTitle}</h3>
                <p>{welcomeCopy}</p>
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

          {!hasLiveEvidence && (
            <div className="notice">
              AI Copilot is waiting for live evidence. Start a new inspection and capture a phone frame or send a physical ESP32 reading first.
            </div>
          )}
          {hasLiveEvidence && ollama !== null && !ollamaReady && (
            <div className="notice">
              Live evidence is ready, but Ollama/Gemma is offline. The verdict engine still works; start Ollama to enable grounded explanations.
            </div>
          )}
          {error && <div className="notice">{error}</div>}

          <div className="ffSuggestedQuestions">
            {suggestions.map((text) => (
              <button key={text} type="button" onClick={() => ask(text)} disabled={!canAsk}>{text}</button>
            ))}
          </div>

          <form className="ffChatComposer" onSubmit={(event) => { event.preventDefault(); ask(); }}>
            <input
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              placeholder={
                !session.sample
                  ? "Select an inspection first…"
                  : !hasLiveEvidence
                    ? "Capture live evidence before asking AI…"
                    : !ollamaReady
                      ? "Start Ollama / Gemma to ask the Copilot…"
                      : "Ask about this sample, evidence, sensors or missing data…"
              }
              disabled={!canAsk}
              maxLength={600}
              aria-label="Ask FreshFusion AI Copilot"
            />
            <button className="primary" type="submit" disabled={!question.trim() || !canAsk}>
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
              <span>Camera</span><b>{cameraRecent ? "Recent" : "Waiting / stale"}</b>
              <span>ESP32</span><b>{physicalSensorRecent ? "Recent hardware" : "Waiting / stale"}</b>
              <span>Ollama</span><b>{ollama?.available ? "Online" : ollama === null ? "Checking" : "Offline"}</b>
              <span>Gemma</span><b>{ollamaReady ? "Ready" : "Unavailable"}</b>
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
