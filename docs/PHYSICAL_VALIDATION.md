# FreshFusion physical-fruit verification

FreshFusion must not treat a picture of a fruit on a laptop/phone/print as equivalent to a physical fruit in the chamber.

## Prototype gate

The browser-camera pipeline now separates **visual identity** from **physical verification**:

1. Detect a centered fruit-like region.
2. Estimate Apple/Banana visual identity.
3. Measure obvious presentation artifacts (large display-like quadrilaterals, strong axis-aligned lines and periodic display patterns).
4. Store a compact perceptual fingerprint of the segmented fruit crop.
5. Require at least three labelled viewpoints and at least four usable live frames.
6. Compare inter-view fruit fingerprints; near-identical views are treated as possible flat-reference evidence.
7. Require recent ESP32 telemetry before the final multimodal freshness verdict is released.

A screen/photo can still receive a **visual identity** and a public-dataset similarity because those are image-level operations. It cannot unlock the final FreshFusion freshness score unless the physical evidence gate passes.

## Output states

- `no_fruit`: no reliable centered fruit-like region.
- `collecting_physical_evidence`: more changed viewpoints are required.
- `suspected_2d_display`: display/screen artifacts are strong enough to block the verdict.
- `suspected_flat_reference`: multiple labelled views look too similar, consistent with repeatedly showing the same flat image.
- `physical_fruit_likely`: multi-view evidence is consistent with a physical 3D fruit.

`physical_fruit_likely` is deliberately probabilistic wording.

## Scientific limitation

A single RGB phone camera cannot guarantee physical liveness or depth. Sophisticated replay/print attacks can defeat monocular heuristics. A production system that needs strong anti-spoof guarantees should add one or more of:

- stereo/depth camera,
- structured light / ToF,
- NIR or multispectral sensing,
- controlled turntable/mechanical multi-view capture,
- challenge-response illumination,
- a trained presentation-attack detector built from real chamber photos, printed images and screen replays.

The current gate is appropriate for preventing obvious photo/screen misuse in the SIH/Eureka prototype while keeping the limitation explicit.
