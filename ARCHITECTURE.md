# SDRbox architecture — spectrum-first direction

**Decision: 2026-11-11. This describes the NEXT architecture, not current implemented functionality.** Today's receiver implementations scan known GMRS frequencies. We will build wideband FFT detection on the already working persistent-device foundation.

## Guiding model

```text
One NESDR device owner (pyrtlsdr / librtlsdr)
  -> tune a planned spectrum window; capture continuous complex IQ
  -> FFT / averaged power spectrum
  -> per-frequency local noise baseline; exclude DC spur & unusable edges
  -> candidate peak / occupied-bandwidth estimation
  -> persistence + hysteresis + modulation/service constraints
  -> select strongest QUALIFIED candidate (initial policy)
  -> extract subchannel from buffered/continuing wideband IQ
  -> NFM or AM demodulation -> rackio-local audio
  -> end-of-activity + hang timer -> return to search
  -> state/hit events -> FastAPI/WebSocket -> all browsers
```

A strong FFT peak is **not automatically speech**: exclude tuner/DC artifacts, constant interferers, adjacent-channel bleed and momentary impulses; validate candidates before recording a hit. Preserve signal metadata (center frequency estimate, width, relative SNR/contrast, modulation, window, timestamps). Do not label uncalibrated values dBm or assume exact tuned carrier frequency.

## Important design choice: work within a wide IQ window

At 462 MHz, GMRS/FRS channels 1–7 extend 462.5625–462.7125 MHz: just **150 kHz between end channel centers**. A single wideband capture can see all seven simultaneously. This is **not** seven tuner retunes.

Start with a fixed 462 MHz window. Compute a short-time spectrum and identify *all* simultaneously active candidates. Initially select the **strongest qualified signal above its local noise floor**, not simply the highest absolute FFT bin. Later add first-seen, round-robin or manual priorities to avoid repeatedly favoring a nearby strong transmitter.

Retain IQ availability for the currently captured window while listening when feasible: separate detection/monitor and demod/audio pipelines so receiving one channel need not blind the engine to other candidates *inside that same window*. Don't overpromise continuous monitoring of other windows with one tuner.

## Window planning

- **Nominal** RTL-SDR sample rates ~2.048–2.4 MS/s may yield a **smaller** clean usable bandwidth; test actual stable IQ and aliasing/rolloff.
- Use **overlapping windows** with explicit guard bands, suppress center DC/LO leakage, and avoid edge-attenuated candidate bins.
- Begin at 462 MHz for GMRS 1–7. Expand to 467 MHz only after one-window detection/audio/hold/resume works.
- Alternating 462/467 windows introduces unavoidable revisit gaps; multiple disjoint services/banks add more. Measure dwell, tune/settle time and missed-transmission probability rather than guessing.
- Airband 118–137 MHz later: AM modulation, channel/spacing rules and overlapping ~2 MHz window plan based on measurements, not a fixed assumed count.
- Treat CB 27 MHz and local AMB/FIRE services as future, research-dependent; some services are digital/trunked/encrypted and outside NFM/AM scope. RTL tuner/antenna limitations apply.

## Engine boundaries (target, not current directories)

1. **Receiver / IQ source:** single-owner open/configure/tune/read/close; later interchangeable RSP1A; one worker holds USB access.
2. **Spectrum engine:** window-plan scheduler, FFT average and local noise estimation, peak grouping and channel bandwidth limits.
3. **Detector:** qualification, dwell/persistence, start/stop thresholds, cooldown, false-positive controls and candidate ranking.
4. **Selector / state machine:** SCANNING_WINDOW -> CANDIDATE -> RECEIVING -> RESUME_DELAY; manual HOLD/SKIP and STOP/ERROR.
5. **Demod / audio:** IQ subchannel extraction, NFM first, AM later; keep 24 kHz rackio-local audio independent of browsers.
6. **Web / persistence:** existing FastAPI, REST commands, WebSocket shared snapshots and real-only activity history.

The Python SDR/FFT worker must not block the FastAPI event loop. Use bounded buffers and thread-safe event/command handoff. Avoid recording a hit until candidate confirmation; differentiate **tuned window center**, **detected signal frequency**, and **demodulated selected frequency** in API/UI.

## Today's code (keep until replacement proven)

- `sdrbox/main.py` — FastAPI and command/state wiring.
- `sdrbox/persistent.py` — **single-open receiver** but still **sequential channel tuning**, ~3 channels/s observed; primitive contrast detection and NFM DSP.
- `sdrbox/scanner.py` — Python-owned sequential per-channel `rtl_fm`, field-tested ~1 channel/s.
- `sdrbox/receiver.py` — native `rtl_fm` scanning or fixed CH1.
- `sdrbox/static/` — responsive dark control UI, not a wideband spectrum display yet.

Do **not** delete the known-good receiver modes while designing or validating the spectrum engine.

## Explicit non-goals for this milestone

No multi-SDR concurrent band coverage, transmission, encrypted/digital trunking decode, remote browser audio, generalized waterfall laboratory, new frontend framework, compulsory kiosk, or speculative performance promises.

## Engineering acceptance for first spectrum window

Demonstrate simultaneous visibility of GMRS 1–7 within one IQ capture; stable local baseline; correctly identify one/two actual walkie-talkie transmissions by frequency; select and demodulate a qualifying NFM signal; release after hang; distinguish RF candidates from real confirmed hits; suppress spurs, idle false positives and repeated duplicates. Retain tested fallback and characterize CPU, missed signals, end-to-end latency and refresh rates.
