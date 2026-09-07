import { Panel, Facts, StatusChip } from "../../shared/Panel";
import { dateTime, titleCase } from "../../shared/format";

export default function History({ samples, onOpen }) {
  return (
    <div className="featurePage">
      <div className="pageIntro">
        <span className="eyebrow">HISTORY</span>
        <h1>Every inspection keeps its evidence.</h1>
        <p>
          Open a previous sample without changing the chamber's active capture
          target. Historical states describe the last recorded assessment;
          opening an investigation rechecks evidence age.
        </p>
      </div>
      <div className="historyGrid">
        {samples.map((sample) => (
          <Panel
            key={sample.sample_id}
            title={sample.fruit_type}
            eyebrow={sample.sample_id}
          >
            <p>{dateTime(sample.created_at)}</p>
            <StatusChip>{titleCase(sample.status)}</StatusChip>
            <Facts
              items={[
                ["Stored camera frames", sample.camera_frames],
                ["Sensor readings", sample.sensor_readings],
                ["Last physical check", titleCase(sample.verification_state)],
                [
                  "Last recorded verdict",
                  sample.last_recorded_verdict_ready
                    ? "Released (historical)"
                    : "Locked / not assessed",
                ],
                ["Last assessed", dateTime(sample.last_assessed_at)],
              ]}
            />
            <div className="buttonRow">
              <button
                className="primary"
                onClick={() => onOpen(sample, "investigation")}
              >
                Open investigation
              </button>
              <button
                className="secondary"
                onClick={() => onOpen(sample, "evidence")}
              >
                View evidence
              </button>
            </div>
          </Panel>
        ))}
      </div>
      {!samples.length && (
        <Panel title="No inspections loaded">
          <p>
            Connect the backend and start an inspection. History shows persisted
            records, not demonstration samples.
          </p>
        </Panel>
      )}
    </div>
  );
}
