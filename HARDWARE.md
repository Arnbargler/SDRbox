# Hardware and verified environment

_Last reviewed: 2026-11-07._

## Current installation (observed or explicitly supplied)

| Item | Current state |
| --- | --- |
| Operating system | **Linux Mint** — user corrected an earlier mistaken Xubuntu assumption |
| Computer | **Dell OptiPlex**, installed at the bottom of a small **tec MOJO-style rack**; exact model/CPU/RAM not yet verified |
| Upper display | **1U monitor — 1424 × 280 pixels** (user-confirmed native resolution); proposed persistent status strip |
| Middle display | **2U monitor — 1280 × 400 pixels** (user-confirmed native resolution); touch works accurately after mapping to HDMI-2; see [TOUCHSCREEN.md](TOUCHSCREEN.md) |
| SDR | **NooElec NESDR Smart**, older unit (user bought around 2018); RTL-SDR family |
| Current app | **GQRX**, operational on Linux Mint; **no custom FastAPI server/scanner/kiosk yet** |
| Antenna | Temporary telescopic antenna used during proof of concept, to be relocated eventually |
| Future hardware | SDRplay **RSP1A** for a later revision; external antenna/coax, physical rotary knob, dedicated speaker |

**Verification:** On 2026-11-07 the user reported results receiving the **118.800 MHz** Ottawa aviation frequency in GQRX. Earlier, changing GQRX's input from a generic RTL device to the **Realtek** device corrected an apparent frequency offset. Reception near GMRS/FRS channel 1 with a walkie-talkie was tested in an earlier session; reducing latency improved it significantly. These tests do **not** demonstrate an operational automatic scanner.

**Do not assume:** Exact OptiPlex model, current system RAM, installed Mint release, touch controller/coordinate mapping, desktop scaling and actual XRandR output identifiers, USB port topology, NESDR revision, antenna type/connector, or sampled-band performance. Measure on the actual box.

## Capture a reproducible baseline

Run these read-only probes on the Dell and document outputs before implementation:

```bash
cat /etc/os-release
uname -a
lscpu | head -30
free -h
lsusb
xrandr --query
which gqrx rtl_test rtl_fm rtl_power
```

Then (after closing GQRX and other SDR clients, which otherwise lock the dongle):

```bash
rtl_test -t
```

Record actual capture stability, usable sample rates, gain behavior, center-frequency/DC spur, input device identification, display placement, desktop scaling and touchscreen coordinate mapping (the pixel resolutions are already known).

## Layout / I/O

Upper display = **1424×280 always-visible status** (aspect ratio ~5.09:1, HDMI-1, touch disabled); lower display = **1280×400 touch controls** (aspect ratio 3.20:1, HDMI-2, touch mapped correctly). Both are driven by the same Dell; **two local Chromium windows are planned**, displaying pages from the **same FastAPI web server on rackio** (upper `/status`, lower `/control`). Other LAN browsers access the same server at `/`. **These web services and kiosk windows are not implemented yet.** **Touch mapping has been verified interactively** using USB paths; **reboot/autostart persistence has not yet been confirmed**. See [TOUCHSCREEN.md](TOUCHSCREEN.md). The mockup is the agreed design target, not a photo of implemented software.

## RF constraints

- RTL-SDR nominal complex sample rate often discussed as **2.4 MS/s (~2.4 MHz span)**; actual clean/useful passband can be smaller. Verify on hardware, avoid edges and leave overlap.
- A single receiver cannot listen to disjoint bands at once. Alternating CB, AIR, FIRE, etc. means retuning; the selected bank combination affects revisit time.
- CB (~27 MHz) may be supported by the dongle but **antenna suitability and reception sensitivity** must be tested. An antenna that receives airband will not automatically perform well at CB, GMRS and fire/EMS bands.
- Many modern police/fire/EMS services use trunking, digital voice and/or encryption. v1 targets **clear analogue AM / narrow FM only**, and should never imply all agencies are receivable.
- RSP1A's different API, sample rates and tuning ranges are a **future adapter**, not justification to delay the RTL-SDR prototype.

## Planned physical upgrades (not installed yet)

1. Move the antenna away from the screens; use a suitable remote antenna/feedline.
2. Add a USB rotary encoder for volume/tuning.
3. Add a dedicated communications speaker.

All three upgrades are approved in principle, **not** v1 blockers.
