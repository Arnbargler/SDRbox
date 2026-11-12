# SDRbox development status

## Milestones (as of 2026-11-11)

| Step | Status | Evidence / remaining caveat |
| --- | --- | --- |
| S1 wideband FFT | **Field verified** | Real CH1 spike, live spectrum refresh |
| S2 local-noise signal candidates | **Initial field verified** | Correct GMRS frequency strongest; no idle false positives seen in short test |
| S3 candidate selection and hang | **Field verified** | SEARCHING / SELECTED / HANG / release observed |
| S4 local NFM audio | **Field verified** | Two-minute PTT, continuous intelligible audio, no raw-IQ queue loss |
| S5 additional RF windows | **Future** | 467 MHz GMRS; measure retune/revisit gaps |
| S6 AM airband | **Future** | AM demodulation and channel/window plans |
| S7 persistence/appliance | **Future** | Genuine activity records, settings, error recovery, optional kiosk |

## Why the current pipeline looks like this

Early sequential `rtl_fm`/persistent frequency-hopping prototypes worked but were removed when the user chose spectrum-first scanning. A later single-threaded FFT + NFM audio loop created rhythmic speech/silence. Audio stayed SELECTED/Gate OPEN even during silent periods: it was **not** caused by squelch. At 2.048 MS/s, capture supply measured 0.74–0.86× and average USB reads around 66.6 ms for 64 ms of IQ. A separate PCM writer and then FFT worker alone did not resolve it.

The working change uses **1.536 MS/s** and separate USB, FFT, DSP and ALSA workers. In the successful test the supply ratio reached **0.973×**, USB reads averaged **87.6 ms** for 85.33 ms per block, no IQ audio queue drops and no audible pauses over a two-minute PTT. DSP `P` is cumulative average and increases while receiving voice compared with generating silence; ~7 ms mean was observed at end.

## Guardrails

- Preserve independent USB/audio/FFT/ALSA paths and fixed tuner while S4 works; avoid premature performance rewrites.
- A strong FFT candidate is not confirmed voice; relative dB is uncalibrated.
- Selection currently only includes GMRS 1–7; fixed 1.3 MHz crop cannot cover separate 467 MHz window.
- Single SDR will need retuning to cover separate bands, with unavoidable revisit gaps.
- Tests are synthetic/offline; verify on actual rackio before declaring any new milestone complete.
- The `assets/scanner-mockup-option-2.webp` file is design history only; the live browser UI is implemented separately.
