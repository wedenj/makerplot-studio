# MakerPlot Studio

Guided **prepare-and-send** workflow for the [MakerPlot](https://makerplot) 3D-printable pen plotter. Automates the software steps from the MakerPlot manual:

1. **F-Engrave** — convert text or PNG to G-code (batch mode)
2. **Backlash compensation** — 0.3 mm per axis (configurable)
3. **GRBL cleanup** — remove unsupported commands (`G90.1`, spindle/coolant M-codes)
4. **UGS Classic CLI** — stream G-code to the Arduino over serial

A step-by-step desktop UI walks you through setup, design, prepare, hardware checklist, and send.

## Requirements

- Windows 10/11 (developed on Windows; core pipeline is cross-platform)
- Python 3.9+
- MakerPlot folder from the kit (F-Engrave, GRBL firmware, etc.)
- Java 17+ — auto-detected from the bundled UGS Platform JDK if present
- MakerPlot assembled, GRBL flashed, and calibrated per the manual

## Quick start

```powershell
git clone https://github.com/wedenj/makerplot-studio.git
cd makerplot-studio
pip install -e .
.\run.ps1
```

On first launch the app downloads **UGS Classic** (~40 MB) into `vendor/` if the JAR is not present.

## Using the wizard

| Step | What you do |
|------|-------------|
| **1. Setup** | Point to your MakerPlot Google Drive folder; confirm F-Engrave, Java, and UGS are found |
| **2. Design** | Choose **Text** or **Image**, enter content or pick a PNG |
| **3. Prepare** | Click **Prepare G-code** — output goes to `Backlash Compensated G-Code/` |
| **4. Hardware** | Paper, pen, power, jog to corner, touch Z to paper, set zero |
| **5. Send** | COM port is auto-detected; click **Send G-code to plotter** |

### COM port detection

Ports are listed via **pyserial** and **UGS CLI** (`-l`). The app prefers devices whose description contains Arduino, CH340, CP210x, FTDI, etc., and remembers your last port.

### Image settings

Default image parameters live in `settings/image_settings.txt`. For best results, open F-Engrave once, tune size/optimization for your image, use **File → Save Setting to File**, and point the UI at that file.

## Project layout

```
makerplot-studio/
├── src/makerplot_studio/
│   ├── app.py           # Tkinter wizard UI
│   ├── pipeline.py      # F-Engrave → backlash → cleanup
│   ├── ugs_cli.py       # UGS Classic TerminalClient wrapper
│   ├── backlash.py      # Directional backlash compensation
│   └── ...
├── settings/
│   └── image_settings.txt
├── scripts/
│   └── setup.ps1
└── vendor/              # UGS Classic JAR (downloaded on setup)
```

## Manual workflow replaced

| Manual step | MakerPlot Studio |
|-------------|------------------|
| F-Engrave GUI → Save G-code | `f-engrave_c.exe -b` in batch |
| G-Code Ripper → backlash → save | Built-in backlash + cleanup |
| UGS → open file → delete bad line → Send | UGS CLI `--file` with cleanup already applied |
| Jog / zero | Still manual (step 4 checklist) |

## Configuration

Settings persist in `.makerplot-studio.json` in the project root (gitignored). Defaults assume:

```
d:\Bambu\MakerPlot\GoogleDrive
```

## License

MIT — MakerPlot hardware/firmware and third-party tools (F-Engrave, G-Code Ripper, UGS) remain under their respective licenses.
