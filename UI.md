# SDRbox UI — spectrum-first (v0.7)

The user chose to **retire the classic scanner interface** after proving that wideband IQ spectrum updates live at 2–3 Hz and shows a real GMRS CH1 spike.

## Layout at 1280×400

- Compact header with SDRbox, LAN connection and receiver state.
- Fixed **GMRS 462 active window** selector and clearly disabled future GMRS 467/AIR/CB/CUSTOM labels (not active controls).
- **Dominant live spectrum graph** with real RF power, local noise baseline, channel markers and calibrated frequency axis (the RF values themselves are not calibrated dBm).
- Full-window/GMRS 1–7 *visual* zoom controls.
- Right-hand diagnostic column: running state, last capture time, strongest **unqualified** FFT bin and contrast, sample rate, future signal-selection status.
- Bottom START/STOP CAPTURE button and truthful no-audio label.

Only a single active window. No setting or mode popover, old bank toggles, squelch, HOLD, SKIP, hit logging or simulated state. Optional future layout changes should be driven by real signals and candidate detection.

The original concept art `assets/scanner-mockup-option-2.webp` remains in the repository as **historical visual reference**, not the current running design. Local HTML/CSS/JS source is under `sdrbox/static/`.

## S3 enhancement (v0.9)

One readout now shows **S3 SELECTED SIGNAL** (frequency, SEARCHING/SELECTED/HANG status and release timer) rather than unqualified strongest-bin text. On the plot, **cyan** represents the locked signal while **amber** represents other candidate peaks, including nearby overload artifacts. No new tuning or listening controls, and no audio. The FFT remains dominant at 1280×400.

## S4 controls

The bottom bar now has a compact MIN RF CONTRAST +dB slider, 8–30 dB, default 15. Higher values make RF peak detection **less sensitive**. The third diagnostics row is S4 LOCAL AUDIO (RECEIVING, MUTED, ERROR/STOPPED). The chosen FFT candidate remains cyan, other candidate peaks amber. A signal selected outside GMRS is blocked from audio selection; all FFT measurements remain visible. Local audio on rackio only, with no browser stream. This is not a traditional squelch or RF gain slider.
