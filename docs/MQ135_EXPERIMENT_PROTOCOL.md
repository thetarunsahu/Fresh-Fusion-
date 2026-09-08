# MQ135 Relative-Response Experiment Protocol

FreshFusion currently uses the MQ135 as an **uncalibrated relative electrical sensor**. This protocol is designed to make that use repeatable without pretending the raw ADC value is ppm, VOC concentration, ethylene concentration or a food-safety measurement.

## Objective

Measure whether the prototype's raw MQ135 response changes repeatably between an empty chamber baseline and fruit inspections under controlled conditions.

## What to record

For every reading series retain:

- timestamp
- device ID
- raw ADC value (`mq135_raw`)
- temperature
- humidity
- chamber state: empty / fruit present
- fruit sample ID when present
- fruit type
- human freshness stage
- notes about fan, lid, lighting and unusual conditions

## 1. Stabilization

Power the same ESP32 + MQ135 setup in the same chamber configuration. Do not use an arbitrary fixed warm-up time as proof of stability.

Instead, observe a rolling window of raw readings and begin a recorded trial only after the signal has stopped showing a strong drift for the current setup. Record how long this took. Use the same procedure across trials.

## 2. Empty-chamber baseline

With no fruit in the chamber:

1. keep fan/lid configuration fixed;
2. collect a continuous sequence of raw readings;
3. record temperature and humidity at the same time;
4. calculate the baseline median or mean and the variability of the window;
5. save the raw readings, not only the aggregate.

The baseline is local to the device/chamber/session. It is not a universal clean-air calibration constant.

## 3. Fruit trial

Place exactly one known fruit sample in the chamber and start/continue the inspection.

Collect a comparable sequence under the same chamber configuration. Record the physical sample ID and human stage.

Useful relative quantities include:

```text
raw_fraction = mq135_raw / 4095
baseline_delta = fruit_raw - empty_baseline_raw
normalized_delta = (fruit_raw - empty_baseline_raw) / max(empty_baseline_raw, small_epsilon)
```

These are engineering features only. They are not gas concentration units.

## 4. Repetition

Repeat empty baseline + fruit trials across multiple physical fruits and stages. Do not treat multiple readings from the same fruit as independent fruit samples when evaluating classification performance.

Useful study questions:

- Is the direction of change consistent for repeated trials?
- How much does temperature/humidity move with the MQ135 signal?
- Does the empty baseline drift during the session?
- Are differences between fruit stages larger than baseline variability?
- Does opening the chamber or changing fan state dominate the signal?

## 5. Recommended analysis

For each physical sample report:

- baseline median/mean;
- fruit-window median/mean;
- baseline variability;
- raw/4095 fraction;
- baseline delta;
- normalized delta;
- temperature and humidity;
- human ground truth.

Plotting raw response over time is more informative than displaying one isolated number.

## 6. What FreshFusion may claim after this experiment

Allowed wording before calibration:

> "FreshFusion uses the MQ135 as a relative gas-response signal and evaluates its behaviour against an empty-chamber baseline under controlled prototype conditions."

Do **not** claim:

- calibrated ppm;
- ethylene concentration;
- universal spoilage thresholds;
- sensor accuracy for freshness classification;
- food-safety certification.

Those claims require an appropriate calibrated sensor methodology, controlled reference gas/calibration procedure and independent validation.

## 7. Fusion policy

The existing fusion contribution must remain explicitly experimental until the team has enough physical ground-truth samples to estimate whether the direction and weight of the MQ135 term are justified.

If the experiment shows that raw response is unstable or dominated by chamber/environment effects, reduce or remove its decision weight rather than forcing it to support the desired result.
