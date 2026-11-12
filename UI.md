# SDRbox browser interface (1280×400)

The live UI is served from `sdrbox/static/`, not from the historical image `assets/scanner-mockup-option-2.webp`.

- Header: connection and capture status; only GMRS 462 is active (467/AIR/CB/CUSTOM are disabled future options).
- Main live FFT: green relative RF power, amber local noise floor, dashed channel centers, amber candidate peaks and cyan **selected** channel.
- FULL WINDOW and GMRS 1–7 buttons change only the plotted range; they never retune the SDR.
- Diagnostics: receiver state and update time, S3 SELECTED / SEARCHING / HANG with nominal GMRS frequency, S4 local audio status and compact throughput diagnostics, plus strongest two persistent candidates.
- Footer: START/STOP CAPTURE, **MIN RF CONTRAST** slider (+8 through +30 dB, default +15; raising it makes detection less sensitive), and status messages.

Audio is played on rackio through ALSA, not through the browser. The 1.536 MS/s IQ stream produces a plotted span of 462.000–463.300 MHz. The status line includes capture supply ratio, average USB read time R, cumulative average audio DSP time P, and discarded IQ blocks. None of these numbers is calibrated RF power.

No sequential scanner channels or profiles, HOLD/SKIP controls, hit log, fake meter, or second display.
