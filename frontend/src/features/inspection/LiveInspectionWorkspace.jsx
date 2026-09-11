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
            <span>DETAILED EVIDENCE & ANALYSIS</span>
            <h2>Full technical inspection workspace</h2>
            <p>
              Product decisions stay at the top. The original FreshFusion evidence tools remain
              available below for QR pairing, sensor trends, reference data, image analysis,
              colour, texture and observations.
            </p>
          </div>
          <span className="ffRestoredBadge">RESTORED</span>
        </div>

        <details open className="ffRestoredDetails">
          <summary>Show detailed technical modules</summary>
          <div className="ffLegacyEvidenceOnly">
            <LiveInspection session={session} />
          </div>
        </details>
      </section>
    </>
  );
}
