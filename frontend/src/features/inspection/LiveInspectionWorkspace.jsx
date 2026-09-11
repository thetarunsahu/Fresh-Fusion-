import ProductLiveInspection from "./ProductLiveInspection";
import LiveInspection from "./LiveInspection";
import "./live-inspection-workspace.css";

export default function LiveInspectionWorkspace({ session }) {
  return (
    <>
      <ProductLiveInspection session={session} />

      <section className="ffRestoredEvidence">
        <div className="ffRestoredEvidenceHeader">
          <div>
            <span>DETAILED ANALYSIS</span>
            <h2>Inspection evidence and measurements</h2>
            <p>
              Open the detailed analysis when you want to review sensor trends, phone pairing,
              reference data, image analysis, colour, texture and observation details.
            </p>
          </div>
        </div>

        <details className="ffRestoredDetails">
          <summary>Open detailed analysis</summary>
          <div className="ffLegacyEvidenceOnly">
            <LiveInspection session={session} />
          </div>
        </details>
      </section>
    </>
  );
}
