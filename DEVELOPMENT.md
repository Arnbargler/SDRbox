# SDRbox roadmap — spectrum-first

## Status (2026-11-11)

S1 spectrum capture was field-tested in v0.6: **real CH1 peak and 2–3 FFT updates per second**. v0.7 rewrites the control interface and removes traditional scanner code; **not field-tested yet**.

## Development sequence

| Milestone | Status | Verification |
| --- | --- | --- |
| S1 wideband IQ/FFT | Measured, previously verified | 462.650 MHz, 2.048 MS/s, visible CH1 peak, 2–3 updates/s |
| S1 interface redesign | Committed | Large FFT display, GMRS zoom and real diagnostics; test 1280×400 |
| S2 signal candidates | **Initial field test passed** | Detect FFT blobs at +10 dB relative to local floor and require 2 of 3 successive frames; validate CH1/CH7 PTT and idle false positives |
| S3 selection | **Field-verified on rackio** | Strongest persistent RF candidate; sticky selection, no stronger-peak preemption, 1.2s release hang |
| S4 demod/audio | **Implemented, hardware test pending** | Selected in-window GMRS NFM channel, rackio-local ALSA PCM, 8–30 dB RF threshold |
| S5 windows/banks | Future | 467 MHz GMRS then AM airband, overlapping spans, measured revisit delays |
| S6 appliance | Future | Config, hit persistence, hardening and optional kiosk |

## Critical design principles

- One SDR worker, persistent USB handle, bounded IQ buffers; FFT and USB work off the FastAPI event loop.
- The displayed 1.70 MHz center crop is **provisional**, not a proven clean passband.
- Relative FFT dB and local noise floor are **uncalibrated**, not dBm.
- An unqualified strongest bin is NOT a transmission or a confirmed hit.
- Keep the UI concise for the verified 1280×400 panel, use Chrome locally or on trusted LAN.
- Old sequential scanner backends were retired as requested; retained in Git history only.
- Avoid coding automatic selection/audio until validating the new UI and measurements.

## Historical results retained in Git history

RTL_fm worked with walkie-talkie audio and squelch; Python/rtl_fm scanner ran ~1 channel/s, persistent frequency retunes ~3/s. Those prototypes were stepping stones rather than the product. An older spectrum view froze because a legacy watchdog was checking for nonexistent rtl_fm; the fix resulted in continuous 2–3 Hz FFT updates. The persistent pyrtlsdr wrapper was pinned to 0.2.91 to match rackio system librtlsdr.

## v0.8 S2 detector — 2026-11-11

Implemented `sdrbox/detector.py` (pure NumPy/SciPy) with coarse contiguous FFT-bin grouping, 10 dB contrast threshold, 3-bin minimum, 45 kHz maximum, provisional center DC and usable-edge guards, and a 2-of-3-frame candidate tracker. Spectrum worker reuses existing FFT and floor arrays; output includes `candidates` plus experimental detection method. Browser overlays candidate locations and lists up to two persistent candidates; no confirmed hits, audio, modulation classification or automatic selection. Added `tests/test_detector.py`, runnable without attached SDR via `python -m unittest discover -s tests`. **Awaiting hardware testing**; thresholds are provisional. No rate claims for S2 until measured. Stable spurs may still appear and require rejection using a longer background model.

## S2 real-radio field test — 2026-11-11

User reported **no false positives observed while idle** in the tested session. Keying a walkie-talkie from approximately 2 feet caused **multiple simultaneous candidates**, but the **highest-ranked candidate matched the correct transmission frequency**. This is strong first-pass confirmation that the spectral detector and candidate ranking work on actual SDR hardware; it is not proof of robustness against weaker signals or broader interference. At very close range, receiver front-end overload may explain extra peaks; test at 10–20 feet or with attenuation before changing thresholds. Suggested next milestone S3: select the strongest qualified candidate with hysteresis/release timing, initially without audio, then proceed to in-window NFM demodulation.

## v0.9 S3 selection candidate — 2026-11-11

Added `sdrbox/selector.py` as a pure-Python state machine. From S2's confirmed-by-persistence FFT candidate list, select highest contrast signal when SEARCHING; lock its *initial* estimated frequency within a +/-8 kHz candidate association window, ignore unrelated stronger new peaks until current candidate disappears; retain selection in HANG across short losses and release after 1.2 seconds without matched stable candidate. Uses worker monotonic clock, resets on capture start, exports `spectrum.selection` including `status`, `frequency_mhz`, `contrast_db`, `width_khz`, `release_remaining_s`, `audio_active=false`. Cyan graph marker and selected-frequency/status readout replace raw strongest-bin diagnostic. Added eight offline tests in `tests/test_selector.py`. **Code committed but S3 has not yet been field tested on rackio**. This is RF-selection policy only: no tuning, FM demodulation, audio, modulation classification or confirmed hit logs.

## v1.0 S4 + sensitivity — 2026-11-11

S3 field-test passed: SEARCHING, SELECTED, HANG and release work as expected on actual rackio. User noticed occasional approximately +12.9 dB locks outside GMRS; **do not treat as identified interference or false traffic without diagnosis**. Introduced user-facing threshold slider 8–30 dB, default +15 dB (higher number = less sensitive). RF candidates are still visible across the entire FFT, but **selection and local NFM audio** are restricted to frequencies within +/-9 kHz of GMRS 1–7 channel centers. This avoids listening to off-bank peaks and prevents arbitrary modulation assumptions.

Added `sdrbox/audio.py` to digitally shift the locked channel out of the same 2.048 MS/s IQ window, decimate by 32 to 64 kHz complex, FM-discriminate, bandpass-filter, resample to 24 kHz, and feed local `aplay` 16-bit mono PCM. The radio **does not retune**. One ALSA playback process is started by the spectrum worker, fed silence when not receiving, and terminated during STOP/shutdown. HANG is muted; changing selected channel resets demod state. The WebSocket reports local audio status and selected audio frequency separately from estimated FFT frequency. A local ALSA error is reported but should not kill the spectrum graph. Capture threshold changes reset temporal detector and selector; slider applies during capture without reopening USB.

New offline `tests/test_audio.py` covers synthetic wideband FM tone, PCM sample counts and threshold rejection. The synthetic DSP math recovered a 1 kHz tone at 1 kHz with a 24 kHz output in an isolated check. **On-hardware S4 audio/CPU/latency are not yet confirmed**; hardware tests are mandatory before calling it working. Watch for underruns, CPU overload, very close PTT front-end saturation, and channel 4 proximity to RTL DC spur (current tuner center 462.650 MHz). No real hit logging or multi-window scan yet.

## S4 dropout follow-up, 2026-11-11
User verified correct S4 frequency lock and NFM demodulation with normal FFT rate, but found periodic ~1 s audio / ~1 s silence during continuous PTT. Hypothesis: S3 briefly entered HANG during modulation-dependent FFT fluctuations and S4 immediately muted/reset audio during HANG. Fix committed: normalize selection to nominal GMRS channels, use threshold-5 dB/provisional evidence only for maintaining an existing lock, and keep audio demod open throughout the 1.2 s HANG. Initial acquisition still requires stable candidate above configured threshold. UI now displays Gate OPEN/CLOSED. Added tests. Awaiting field retest. Some hiss after genuine PTT release is a possible side effect.


## S4 follow-up: gate stayed OPEN during silence — 2026-11-11

User confirms audio still periodically cuts in/out while S3 shows SELECTED and S4 shows Gate OPEN throughout; this excludes S3 selection/HANG gating as immediate cause. Changes committed: `sdrbox/playback.py` owns a single local aplay process and a bounded 64-block PCM queue; 10-block startup prebuffer, 400ms ALSA buffer and 80ms period, non-blocking PCM offers from SDR loop. Audio writes no longer stall SDR capture. `sdrbox/spectrum.py` reports `spectrum.audio_diagnostics` with max IQ-read interval, max demod compute time, queued milliseconds, dropped blocks, writer write stalls/gaps/errors; on-screen display shows Gate/IQ/Q/drop. Synthetic tests added for queue behavior. **Awaiting rackio retest**, not a confirmed solution. If audio still pulses with Gate OPEN, inspect stats to distinguish PCM starvation (IQ max >>16ms), queue overload (drop increasing), and downstream ALSA glitches (both normal). Do not change FFT selection/sensitivity just to hide PCM problems.

## Follow-up: gate OPEN, IQ68.9ms / Q16ms / drops0

User reports audio still cycling while selected and gate OPEN, with maximum IQ interval 68.9ms, PCM queue 16ms, zero dropped PCM chunks. Peak interval alone does not prove sustained starvation; prior FFT/percentile analysis did run inside the same IQ/PCM worker, sometimes exceeding 16ms of audio per IQ block. The new code moves all FFT analysis, candidate detection, selection and snapshot dispatch to a separate worker. The IQ worker nonblockingly offers at most one most recent IQ block for visualization, but continuously reads samples, demodulates and produces PCM. Audio queue remains separate. Added `pcm_supply_ratio` = cumulative IQ samples / sample rate divided by elapsed seconds (approximately 1.00 is real time); displayed in S4 panel as `rate`. Work awaiting real rackio test. If continued dropout with rate >= ~1, investigate ALSA XRUN/USB buffering; if rate <1 sustained, optimize DSP/capture further. Keep audio/gate/selection semantics unchanged.

## S4 periodic audio starvation: 0.74x supply, Nov 11 2026
User confirmed PCM supply ratio stayed ~0.74x, **even at idle**, and repeated audio dropouts with Gate OPEN/SELECTED. This implies insufficient input/PCM sample throughput rather than squelch or NFM classification. The previous 32768-IQ read corresponds to only 16ms at 2.048MS/s; repeated synchronous read calls plus interpreter/DSP overhead could cost >16ms. Experimental throughput change increases IQ read blocks to 131072 (64ms); FFT remains separate, PCM buffer startup reduced from 10 to 4 blocks (now 4x64ms), PCM queue cap 16 blocks; queued_ms derived from actual audio bytes. Audio/DSP math now tests the 64ms conversion. Added diagnostics: avg_iq_read_ms (actual synchronous read duration), avg_processing_ms (remaining Python work), iq_block_ms (expected 64ms), pcm_supply_ratio (effective real-time throughput). This is a **candidate fix**, not field-verified. If rate still <1 after pull, compare read vs processing to determine whether SDR/USB read is slow or Python processing is slow; do not keep increasing buffering blindly.
