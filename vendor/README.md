# Bundled applications

MakerPlot Studio keeps its required tools under `vendor/`. These are **not committed to git** (too large); copy them once from your MakerPlot kit:

```powershell
.\scripts\bundle-apps.ps1
```

Or use **Setup → Copy apps to vendor/** in the app UI.

## What gets copied

| Path | Source | Size (approx.) |
|------|--------|----------------|
| `vendor/f-engrave/` | `F-Engrave-1.78_win/` from MakerPlot kit | ~76 MB |
| `vendor/jre/` | JRE from `win64-ugs-platform-app-*/ugsplatform-win/jdk/` | ~124 MB |
| `vendor/ugs-classic/UniversalGcodeSender/UniversalGcodeSender.jar` | Downloaded or extracted from zip | ~42 MB |

Also copied into the project:

- `settings/text_settings.txt` — F-Engrave text defaults from the kit
- `samples/monkey.png` — sample image for testing

## Fallback

If bundled apps are missing, the app falls back to tools in your MakerPlot kit folder (if configured) or downloads UGS Classic automatically.
