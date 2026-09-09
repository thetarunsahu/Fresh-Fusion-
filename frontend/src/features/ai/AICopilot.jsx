import { Bot, Database, FileSearch, History, RadioTower } from "lucide-react";
import GemmaExplanation from "../investigation/GemmaExplanation";
import { Panel, StatusChip } from "../../shared/Panel";

export default function AICopilot({ session }) {
  const report = session.report;
  const sources = [
    ["Current sample evidence", Boolean(report?.evidence), FileSearch],
    ["Sensor telemetry", Boolean(report?.evidence?.sensors?.latest), RadioTower],
    ["Reference context", Boolean(report?.analysts?.reference), Database],
    ["Inspection history", Boolean(report?.human_verifications?.length), History],
  ];

  return (
    <div className="featurePage aiCopilotPage">
      <div className="pageIntro">
        <span className="eyebrow">AI COPILOT</span>
        <h1>Ask the evidence, not a generic chatbot.</h1>
        <p>
          FreshFusion uses local Gemma through Ollama to explain the selected
          inspection. The response is grounded in retrieved sample evidence and
          never replaces the deterministic assessment gate.
        </p>
      </div>
      <div className="twoPanels">
        <Panel title="LLM + RAG state" eyebrow="LOCAL · EVIDENCE-GROUNDED">
          <div className="chipRow">
            <StatusChip tone="good">Gemma 3</StatusChip>
            <StatusChip>Ollama local</StatusChip>
            <StatusChip tone="good">RAG enabled</StatusChip>
            <StatusChip>Explanation only</StatusChip>
          </div>
          <p>
            The copilot retrieves the current investigation snapshot, analyst
            outputs, critic state and stored records before generating an answer.
          </p>
        </Panel>
        <Panel title="Retrieved context" eyebrow="VISIBLE SOURCE PROOF">
          <div className="connectionList">
            {sources.map(([label, available, Icon]) => (
              <div key={label}>
                <span><Icon size={15} /> {label}</span>
                <StatusChip tone={available ? "good" : "neutral"}>
                  {available ? "Available" : "Waiting"}
                </StatusChip>
              </div>
            ))}
          </div>
        </Panel>
      </div>
      <Panel title="Suggested questions" eyebrow="GROUND YOUR QUESTIONS IN THE CURRENT SAMPLE">
        <div className="chipRow aiPromptChips">
          {[
            "Why is this assessment locked?",
            "What evidence is missing?",
            "Explain sensor contribution",
            "What did the reference retrieval find?",
            "What should I capture next?",
          ].map((text) => <span key={text}><Bot size={13} /> {text}</span>)}
        </div>
      </Panel>
      <GemmaExplanation sampleId={session.sample?.sample_id} />
    </div>
  );
}
