# SDRbox — spectrum-first receiver

SDRbox is a **receive-only wideband spectrum monitor**, not a conventional channel-hopping scanner. Our long-term goal is to capture overlapping ~2 MHz usable RF windows, discover multiple signals above their local noise floor, select the strongest qualified candidate, and demodulate it.

## Current code: v0.8 (S2 candidate detection awaiting rackio field test)

- One live window centered on **462.650 MHz** at **2.048 MS/s**.
- Measured averaged FFT spectrum plus estimated local noise floor, refreshed ~2–3 times/second in the previous S1 interface.
- Full-window and GMRS channels 1–7 display zoom; single START/STOP capture button.
- A spectrum-centric 1280×400 Chrome UI, shared over the home LAN.
- **Experimental S2 spectral candidates**: RF power blobs above a local noise estimate, approximate peak frequencies, and two-frame persistence. No verified voice detection, audio, hit logging, or multi-window tuning yet.
- Old scanner profiles and modules removed from the current branch; Git history preserves them.

## Hardware

rackio.local: Dell OptiPlex 5060 Micro, 8 GB, Linux Mint, NooElec NESDR Smart RTL2832U/R820T. One verified HDMI-2 1280×400 touchscreen at +0+0. FastAPI browser control on http://rackio.local:8080. No compulsory kiosk.

## Where to go

Read [HANDOFF.md](HANDOFF.md) for concise state, [RUNNING.md](RUNNING.md) for commands, [ARCHITECTURE.md](ARCHITECTURE.md) for spectrum design and [DEVELOPMENT.md](DEVELOPMENT.md) for milestones.

Do not confuse the strongest displayed FFT bin with an identified radio transmission. That requires the next-stage candidate detector.

Keep the service on trusted home LAN only; there is no authentication.
