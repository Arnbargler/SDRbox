# SDRbox — spectrum-first receiver

SDRbox is a **receive-only wideband spectrum monitor**, not a conventional channel-hopping scanner. Our long-term goal is to capture overlapping ~2 MHz usable RF windows, discover multiple signals above their local noise floor, select the strongest qualified candidate, and demodulate it.

## Current code: v1.0 (S4 in-window NFM audio; hardware test pending)

- One live window centered on **462.650 MHz** at **2.048 MS/s**.
- Measured averaged FFT spectrum plus estimated local noise floor, refreshed ~2–3 times/second in the previous S1 interface.
- Full-window and GMRS channels 1–7 display zoom; single START/STOP capture button.
- A spectrum-centric 1280×400 Chrome UI, shared over the home LAN.
- **Field-tested S2 spectral candidates:** idle test had no observed false positives; a nearby walkie-talkie produced multiple RF peaks but the correct frequency ranked strongest.
- **New S3 experimental selection:** locks the strongest persistent RF candidate, maintains the lock against competing peaks, and releases after 1.2 seconds absent. Cyan indicates selected; amber indicates other peaks. S4 adds **experimental rackio-local NFM audio** for the selected GMRS channel and a live +8 to +30 dB contrast threshold. Audio quality, stability and throughput await field testing; no verified voice classification, persistent hit logging or multi-window tuning.
- Old scanner profiles and modules removed from the current branch; Git history preserves them.

## Hardware

rackio.local: Dell OptiPlex 5060 Micro, 8 GB, Linux Mint, NooElec NESDR Smart RTL2832U/R820T. One verified HDMI-2 1280×400 touchscreen at +0+0. FastAPI browser control on http://rackio.local:8080. No compulsory kiosk.

## Where to go

Read [HANDOFF.md](HANDOFF.md) for concise state, [RUNNING.md](RUNNING.md) for commands, [ARCHITECTURE.md](ARCHITECTURE.md) for spectrum design and [DEVELOPMENT.md](DEVELOPMENT.md) for milestones.

Do not confuse the strongest displayed FFT bin with an identified radio transmission. That requires the next-stage candidate detector.

Keep the service on trusted home LAN only; there is no authentication.

## Latest S4 throughput experiment (2026-11-11)

User field measurements: 64ms blocks at 2.048 MS/s average RTL read **66.6ms**, overall IQ supply around **0.86×** and ongoing periodic audio silence, even with stable S3 SELECTED / Gate OPEN. This indicates unsustainable source-to-audio throughput; the old DSP work ran on the same thread as synchronous USB reads.

Current experimental version: capture at **1.536 MS/s**, keeping central **1.3 MHz** visible (462.000–463.300 MHz) and still covering GMRS channels 1–7. One worker owns RTL reads, one processes sequential IQ into 24kHz NFM PCM, one handles live FFT/selection, and a fourth writes PCM to ALSA. Audio worker queue overload is explicitly counted as **IQ lost**. This is a deliberate narrower-spectrum tradeoff, not yet tested on rackio. 
