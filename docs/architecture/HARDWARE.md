# Hardware and Capture Architecture

## Prototype hardware

FreshFusion currently combines a physical fruit chamber, an ESP32 sensing node and a phone camera.

### ESP32 sensor node

Current prototype inputs:

- DHT11 temperature
- DHT11 humidity
- MQ135 analog raw reading
- device metadata such as RSSI / uptime where available

The ESP32 sends measurements over Wi-Fi/HTTP to the FastAPI backend.

### Phone camera

The phone is used as a multi-view RGB camera. It captures labelled viewpoints such as:

- Front
- Left
- Right
- Back
- Top

The phone upload path is evidence collection, not a standalone classifier.

## Hardware data flow

```text
Physical Fruit
   |
   +--> Chamber environment --> DHT11 / MQ135 --> ESP32
   |                                         |
   |                                         v
   |                                   FastAPI sensors API
   |
   +--> Phone camera --> labelled frames --> FastAPI image API
                                             |
                                             v
                                        Sample database
                                             |
                                             v
                                      Investigation engine
```

## Sensor contract

Current prototype packets require finite values for:

- temperature: 0-50 C input bounds;
- humidity: 0-100 %RH input bounds;
- MQ135 raw: 0-4095 for the configured 12-bit ADC path.

These are input/electrical bounds, not accuracy or calibration claims.

## MQ135 scientific boundary

Do not present `mq135_raw` as calibrated gas concentration.

Current safe language:

> MQ135 provides a relative gas-response signal used as experimental supporting evidence. Calibration against controlled gas concentrations and fruit-specific chamber experiments is still required.

Do not claim ethylene specificity from the current hardware.

## Pairing model

The prototype has one explicit active chamber inspection.

```text
Create inspection
     |
     v
Set active capture target
     |
     +--> phone QR includes sample_id
     |
     +--> ESP32 may use explicit sample_id or active target
```

Important rules:

1. A phone remains paired to the selected inspection.
2. If the target changes, phone capture should stop and request re-pairing.
3. Historical browsing must not redirect the ESP32.
4. Stale uploads to the wrong sample should be rejected rather than silently accepted.
5. Multi-chamber/device identity is future work.

## Evidence timing

Current operational evidence windows are prototype freshness/connection rules, not fruit shelf-life science.

- Recent hardware telemetry is required for a multimodal verdict.
- Old frames should not indefinitely unlock a current assessment.
- A new empty scene must invalidate older positive visual evidence where appropriate.
- Camera connection status should be based on recent activity, not historical data.

See `../INVESTIGATION_FOUNDATION.md` for the exact current operational windows used by the implementation.

## Physical-fruit capture protocol

For a meaningful SIH demo:

1. Start a new inspection.
2. Place one physical fruit in the chamber.
3. Confirm ESP32 data is current.
4. Capture Front.
5. Physically move around/rotate capture position.
6. Capture Left or Right.
7. Capture Back or Top.
8. Confirm appearance change rather than only relabelling the same image.
9. Wait for critic/physical verification state.
10. Release final assessment only when required evidence passes.

## Failure states to demonstrate

The system should handle these without crashing:

- ESP32 disconnected;
- phone disconnected;
- no fruit;
- only one viewpoint;
- same picture relabelled as multiple views;
- fruit image shown on a screen;
- simulator sensor data;
- stale sensor data;
- reference index unavailable;
- Ollama unavailable.

## Future hardware direction

Possible production improvements:

- higher-quality temperature/humidity sensing;
- controlled illumination;
- calibrated gas sensing / dedicated VOC channels;
- depth/stereo camera;
- NIR/spectral sensing where justified;
- fixed multi-camera or motorized capture rig;
- explicit device identity and multi-chamber pairing;
- industrial enclosure and power architecture.

These are roadmap items, not current deployed capabilities.