# MakerPlot Studio

Guided **prepare-and-send** workflow for the MakerPlot 3D-printable pen plotter. Automates the software steps from the MakerPlot manual:

1. **F-Engrave** — convert text or PNG to G-code (batch mode)
2. **Backlash compensation** — 0.3 mm per axis (configurable)
3. **GRBL cleanup** — remove unsupported commands (`G90.1`, spindle/coolant M-codes)
4. **UGS Classic CLI** — stream G-code to the Arduino over serial

A step-by-step desktop UI walks you through setup, design, prepare, hardware checklist, and send.

## Requirements

- Windows 10/11
- Python 3.9+
- MakerPlot assembled, GRBL flashed, and calibrated per the manual
- MakerPlot kit folder (one-time, to copy bundled apps into the project)

## Quick start

```powershell
git clone https://github.com/wedenj/makerplot-studio.git
cd makerplot-studio
.\scripts\setup.ps1    # copies F-Engrave, Java, UGS into vendor/
.\run.ps1
```

If your MakerPlot kit is not at `d:\Bambu\MakerPlot\GoogleDrive`, pass the path:

```powershell
.\scripts\bundle-apps.ps1 -MakerPlotDir "C:\path\to\GoogleDrive"
```

## Bundled applications

Required tools are copied into `vendor/` (gitignored, ~240 MB total):

| Component | Location |
|-----------|----------|
| F-Engrave 1.78 | `vendor/f-engrave/` |
| Java 17 JRE | `vendor/jre/` |
| UGS Classic | `vendor/ugs-classic/UniversalGcodeSender/UniversalGcodeSender.jar` |

Prepared G-code is written to `output/`. Settings templates live in `settings/`.

## Using the wizard

| Step | What you do |
|------|-------------|
| **1. Setup** | Validate bundled apps; optionally copy from kit via **Copy apps to vendor/** |
| **2. Design** | Choose **Text** or **Image**, enter content or pick a PNG |
| **3. Prepare** | Click **Prepare G-code** — output goes to `output/` |
| **4. Hardware** | Paper, pen, power, jog to corner, touch Z to paper, set zero |
| **5. Send** | COM port is auto-detected; click **Send G-code to plotter** |

### COM port detection

Ports are listed via **pyserial** and **UGS CLI** (`-l`). The app prefers devices whose description contains Arduino, CH340, CP210x, FTDI, etc., and remembers your last port.

## Project layout

```
makerplot-studio/
├── src/makerplot_studio/   # Application code
├── vendor/                 # F-Engrave, JRE, UGS (copied locally, not in git)
├── settings/               # F-Engrave setting templates
├── samples/                # Sample images (e.g. monkey.png)
├── output/                 # Generated G-code (gitignored)
└── scripts/
    ├── setup.ps1           # First-time setup
    └── bundle-apps.ps1     # Copy apps from MakerPlot kit
```

## License

MIT — MakerPlot hardware/firmware and third-party tools (F-Engrave, UGS) remain under their respective licenses.
