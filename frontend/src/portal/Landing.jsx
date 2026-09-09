import {
  ArrowRight,
  Bot,
  Camera,
  Database,
  Microscope,
  ShieldCheck,
  Sparkles,
  Waves,
} from "lucide-react";

export default function Landing({ user, navigate }) {
  const goWorkspace = () => navigate(user ? "overview" : "login");

  return (
    <div className="portalPage landingPage">
      <header className="landingNav">
        <button className="portalBrand" onClick={() => navigate("home")}>
          <span className="portalLogo ffPortalTextLogo">FF</span>
          <span>
            <b>FreshFusion</b>
            <small>Fruit Quality Intelligence</small>
          </span>
        </button>
        <nav aria-label="Landing navigation">
          <a href="#capabilities">Capabilities</a>
          <a href="#architecture">Architecture</a>
          <a href="#evidence">Evidence</a>
        </nav>
        <div className="landingNavActions">
          {user && <span className="signedInAs">{user.full_name}</span>}
          <button className="portalGhost" onClick={() => navigate("login")}>Sign in</button>
          <button className="portalPrimary" onClick={goWorkspace}>
            {user ? "Open workspace" : "Enter FreshFusion"} <ArrowRight size={16} />
          </button>
        </div>
      </header>

      <main>
        <section className="landingHero">
          <div className="landingHeroCopy">
            <div className="portalKicker"><Sparkles size={15} /> SIH 2026 · Team OrchardX</div>
            <h1>Inspect the fruit.<br /><span>Challenge the evidence.</span></h1>
            <p>
              A multimodal fruit-quality investigation system combining phone vision,
              ESP32 sensor evidence, public references, deterministic critique and a
              local evidence-aware AI explanation layer.
            </p>
            <div className="landingHeroActions">
              <button className="portalPrimary portalPrimaryLarge" onClick={goWorkspace}>
                Start investigating <ArrowRight size={18} />
              </button>
              <button className="portalSecondary" onClick={() => navigate("login")}>Secure access</button>
            </div>
            <div className="landingTrust">
              <span><ShieldCheck size={15} /> Deterministic gating</span>
              <span><Database size={15} /> Evidence history</span>
              <span><Bot size={15} /> Gemma + RAG explanation</span>
            </div>
          </div>

          <div className="landingHeroVisual" aria-label="FreshFusion investigation concept">
            <div className="ffLandingVisualHeader">
              <div><span>SYSTEM READINESS</span><b>FreshFusion online</b></div>
              <small>LOCAL AI</small>
            </div>
            <div className="heroFruitOrb">
              <div className="heroFruitCore"><b>FF</b><small>INVESTIGATION</small></div>
              <span className="heroOrbitLabel labelVision">Vision</span>
              <span className="heroOrbitLabel labelSensor">Sensors</span>
              <span className="heroOrbitLabel labelReference">Reference</span>
              <span className="heroOrbitLabel labelCritic">Critic</span>
            </div>
            <div className="heroOutcomeCard">
              <span>EXPERIMENTAL ASSESSMENT</span>
              <strong>Evidence before conclusions</strong>
              <small>Fresh · Ripe · Overripe · Spoiled · Inconclusive</small>
            </div>
          </div>
        </section>

        <section className="landingMetrics" aria-label="Prototype highlights">
          <div><strong>4</strong><span>independent analyst layers</span></div>
          <div><strong>3</strong><span>physical evidence modalities</span></div>
          <div><strong>Local</strong><span>Gemma via Ollama</span></div>
          <div><strong>Human</strong><span>ground-truth verification</span></div>
        </section>

        <section className="landingSection" id="capabilities">
          <div className="landingSectionHead">
            <span>CAPABILITIES</span>
            <h2>One workspace. Multiple independent signals.</h2>
            <p>Each layer contributes evidence without pretending every source is an equivalent vote.</p>
          </div>
          <div className="landingCapabilityGrid">
            {[
              [Camera, "Visual intelligence", "Multi-view phone capture, colour, texture and visible-defect evidence."],
              [Waves, "Sensor intelligence", "DHT11 environmental context plus raw relative MQ135 response."],
              [Database, "Reference retrieval", "Published visual references provide context and retrieved evidence."],
              [Microscope, "Evidence critic", "Missing, stale, contradictory or suspicious evidence is challenged before release."],
              [Bot, "AI Copilot", "Gemma explains retrieved sample evidence through a local Ollama runtime."],
              [ShieldCheck, "Human verification", "Operators can accept, challenge or add independent ground truth."],
            ].map(([Icon, title, text]) => (
              <article key={title}>
                <span><Icon size={20} /></span>
                <h3>{title}</h3>
                <p>{text}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="landingArchitecture" id="architecture">
          <div>
            <span>INVESTIGATION PIPELINE</span>
            <h2>Designed to know when evidence is insufficient.</h2>
          </div>
          <div className="architectureRail">
            {["Physical sample", "Camera + ESP32", "Analyst layers", "Evidence critic", "Deterministic fusion", "Human review"].map((item, index) => (
              <div key={item}><b>{String(index + 1).padStart(2, "0")}</b><span>{item}</span></div>
            ))}
          </div>
        </section>

        <section className="landingEvidence" id="evidence">
          <div className="landingEvidenceCopy">
            <span>GROUNDED AI</span>
            <h2>Show the judge exactly what the LLM retrieved.</h2>
            <p>
              FreshFusion AI Copilot exposes its current-sample evidence, sensor telemetry,
              visual analysis, reference context and human records alongside every explanation.
              Gemma explains the investigation; it does not replace the deterministic verdict.
            </p>
            <button className="portalPrimary" onClick={goWorkspace}>Explore the workspace <ArrowRight size={16} /></button>
          </div>
          <div className="ragProofCard">
            <div className="ragProofHeader"><span><Bot size={18} /> AI Copilot</span><b>RAG ENABLED</b></div>
            <div className="ragProofBadges"><span>Gemma 3</span><span>Ollama local</span><span>Evidence retrieval</span></div>
            <div className="ragProofAnswer"><small>WHY IS THIS SAMPLE BLOCKED?</small><p>Camera evidence is available, but the latest physical ESP32 reading is stale. The critic therefore keeps the assessment locked.</p></div>
            <div className="ragProofSources"><span>Vision analysis</span><span>Sensor log</span><span>Reference index</span><span>Inspection history</span></div>
          </div>
        </section>
      </main>

      <footer className="landingFooter">
        <span>FreshFusion · Team OrchardX</span>
        <span>Experimental SIH prototype · Calibration and real-world validation required</span>
      </footer>
    </div>
  );
}
