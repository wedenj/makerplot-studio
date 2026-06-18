"""MakerPlot Studio — guided prepare-and-send UI."""

from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from makerplot_studio.com_ports import guess_best_port, list_serial_ports
from makerplot_studio.config import AppConfig, load_config, save_config
from makerplot_studio.paths import (
    FENGRAVE_EXE,
    JRE_JAVA,
    PROJECT_ROOT,
    UGS_JAR,
    bundled_apps_present,
    ensure_ugs_jar,
    find_fengrave,
    find_java,
)
from makerplot_studio.pipeline import PrepareResult, prepare_job
from makerplot_studio.ugs_cli import list_ports_via_ugs, send_gcode


STEPS = [
    ("1. Setup", "setup"),
    ("2. Design", "design"),
    ("3. Prepare", "prepare"),
    ("4. Hardware", "hardware"),
    ("5. Send", "send"),
]

HARDWARE_ITEMS = [
    "Place paper on the work area",
    "Insert pen in the holder (moves freely up/down)",
    "Position plotter on the paper so it won't slide",
    "Connect USB and turn on the 5V motor power supply",
    "Jog pen to the start corner and lower Z until it touches paper",
    "In UGS (or here after sending), ensure work zero is set",
]


class MakerPlotApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("MakerPlot Studio")
        self.geometry("920x680")
        self.minsize(820, 620)

        self.cfg = load_config(PROJECT_ROOT)
        self.current_step = 0
        self.prepare_result: PrepareResult | None = None
        self.java_path: Path | None = None
        self.ugs_jar: Path | None = None
        self.mode_var = tk.StringVar(value="text")
        self.port_var = tk.StringVar(value=self.cfg.last_com_port)
        self.status_var = tk.StringVar(value="Welcome — start with Setup.")

        self._build_layout()
        self._show_step(0)
        self.after(200, self._bootstrap_tools)

    def _build_layout(self) -> None:
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        sidebar = ttk.Frame(self, padding=12)
        sidebar.grid(row=0, column=0, sticky="ns")
        ttk.Label(sidebar, text="MakerPlot Studio", font=("Segoe UI", 14, "bold")).pack(
            anchor="w", pady=(0, 12)
        )
        self.step_labels: list[ttk.Label] = []
        for title, _ in STEPS:
            lbl = ttk.Label(sidebar, text=title, font=("Segoe UI", 10))
            lbl.pack(anchor="w", pady=4)
            self.step_labels.append(lbl)

        main = ttk.Frame(self, padding=12)
        main.grid(row=0, column=1, sticky="nsew")
        main.columnconfigure(0, weight=1)
        main.rowconfigure(0, weight=1)

        self.content = ttk.Frame(main)
        self.content.grid(row=0, column=0, sticky="nsew")
        self.content.columnconfigure(0, weight=1)

        log_frame = ttk.LabelFrame(main, text="Log", padding=8)
        log_frame.grid(row=1, column=0, sticky="ew", pady=(12, 0))
        log_frame.columnconfigure(0, weight=1)
        self.log = tk.Text(log_frame, height=8, wrap="word", state="disabled")
        self.log.grid(row=0, column=0, sticky="ew")
        scroll = ttk.Scrollbar(log_frame, command=self.log.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        self.log.configure(yscrollcommand=scroll.set)

        nav = ttk.Frame(main)
        nav.grid(row=2, column=0, sticky="ew", pady=(12, 0))
        nav.columnconfigure(1, weight=1)
        self.back_btn = ttk.Button(nav, text="← Back", command=self._prev_step)
        self.back_btn.grid(row=0, column=0, padx=(0, 8))
        ttk.Label(nav, textvariable=self.status_var).grid(row=0, column=1, sticky="w")
        self.next_btn = ttk.Button(nav, text="Next →", command=self._next_step)
        self.next_btn.grid(row=0, column=2, padx=(8, 0))

        self.frames: dict[str, ttk.Frame] = {}
        self._build_setup_frame()
        self._build_design_frame()
        self._build_prepare_frame()
        self._build_hardware_frame()
        self._build_send_frame()

    def _build_setup_frame(self) -> None:
        frame = ttk.Frame(self.content, padding=4)
        self.frames["setup"] = frame
        ttk.Label(frame, text="Paths & tools", font=("Segoe UI", 12, "bold")).grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 12)
        )

        ttk.Label(frame, text="MakerPlot kit folder (optional)").grid(row=1, column=0, sticky="w")
        self.makerplot_var = tk.StringVar(value=self.cfg.makerplot_dir or "")
        ttk.Entry(frame, textvariable=self.makerplot_var, width=60).grid(
            row=1, column=1, sticky="ew", padx=8
        )
        ttk.Button(frame, text="Browse…", command=self._browse_makerplot).grid(row=1, column=2)
        ttk.Label(
            frame,
            text="Apps live in vendor/. Kit folder is only needed for first-time bundling or extra samples.",
            wraplength=640,
            foreground="#555",
        ).grid(row=2, column=0, columnspan=3, sticky="w", pady=(4, 0))

        ttk.Label(frame, text="Text settings file").grid(row=3, column=0, sticky="w", pady=(8, 0))
        self.text_settings_var = tk.StringVar(value=str(self.cfg.resolved_text_settings()))
        ttk.Entry(frame, textvariable=self.text_settings_var, width=60).grid(
            row=3, column=1, sticky="ew", padx=8, pady=(8, 0)
        )
        ttk.Button(frame, text="Browse…", command=self._browse_text_settings).grid(
            row=3, column=2, pady=(8, 0)
        )

        ttk.Label(frame, text="Image settings file").grid(row=4, column=0, sticky="w", pady=(8, 0))
        self.image_settings_var = tk.StringVar(value=str(self.cfg.resolved_image_settings()))
        ttk.Entry(frame, textvariable=self.image_settings_var, width=60).grid(
            row=4, column=1, sticky="ew", padx=8, pady=(8, 0)
        )
        ttk.Button(frame, text="Browse…", command=self._browse_image_settings).grid(
            row=4, column=2, pady=(8, 0)
        )

        bl = ttk.LabelFrame(frame, text="Backlash compensation (mm)", padding=8)
        bl.grid(row=5, column=0, columnspan=3, sticky="ew", pady=(16, 0))
        self.backlash_x = tk.StringVar(value=str(self.cfg.backlash_x))
        self.backlash_y = tk.StringVar(value=str(self.cfg.backlash_y))
        self.backlash_z = tk.StringVar(value=str(self.cfg.backlash_z))
        for i, (label, var) in enumerate(
            [("X", self.backlash_x), ("Y", self.backlash_y), ("Z", self.backlash_z)]
        ):
            ttk.Label(bl, text=f"{label}:").grid(row=0, column=i * 2, padx=(0, 4))
            ttk.Entry(bl, textvariable=var, width=8).grid(row=0, column=i * 2 + 1, padx=(0, 12))

        self.tools_status = ttk.Label(frame, text="Checking tools…", wraplength=640)
        self.tools_status.grid(row=6, column=0, columnspan=3, sticky="w", pady=(16, 0))

        btn_row = ttk.Frame(frame)
        btn_row.grid(row=7, column=0, columnspan=3, sticky="w", pady=(12, 0))
        ttk.Button(btn_row, text="Save & validate", command=self._save_setup).pack(side="left")
        ttk.Button(btn_row, text="Copy apps to vendor/", command=self._run_bundle).pack(
            side="left", padx=(8, 0)
        )
        frame.columnconfigure(1, weight=1)

    def _build_design_frame(self) -> None:
        frame = ttk.Frame(self.content, padding=4)
        self.frames["design"] = frame
        ttk.Label(frame, text="What do you want to plot?", font=("Segoe UI", 12, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 12)
        )

        mode_row = ttk.Frame(frame)
        mode_row.grid(row=1, column=0, columnspan=2, sticky="w")
        ttk.Radiobutton(
            mode_row, text="Text", value="text", variable=self.mode_var, command=self._toggle_design_mode
        ).pack(side="left", padx=(0, 16))
        ttk.Radiobutton(
            mode_row, text="Image (PNG)", value="image", variable=self.mode_var, command=self._toggle_design_mode
        ).pack(side="left")

        self.text_panel = ttk.LabelFrame(frame, text="Text to plot", padding=8)
        self.text_panel.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=(12, 0))
        self.text_input = tk.Text(self.text_panel, height=6, width=70)
        self.text_input.pack(fill="both", expand=True)
        self.text_input.insert("1.0", "HELLO")

        self.image_panel = ttk.LabelFrame(frame, text="Image file", padding=8)
        self.image_panel.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        default_image = self.cfg.default_sample_image()
        self.image_var = tk.StringVar(
            value=str(default_image) if default_image else ""
        )
        ttk.Entry(self.image_panel, textvariable=self.image_var, width=60).pack(
            side="left", fill="x", expand=True, padx=(0, 8)
        )
        ttk.Button(self.image_panel, text="Browse…", command=self._browse_image).pack(side="left")

        ttk.Label(frame, text="Job name (optional)").grid(row=4, column=0, sticky="w", pady=(12, 0))
        self.job_name_var = tk.StringVar(value="")
        ttk.Entry(frame, textvariable=self.job_name_var, width=30).grid(
            row=4, column=1, sticky="w", pady=(12, 0)
        )
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(2, weight=1)
        self._toggle_design_mode()

    def _build_prepare_frame(self) -> None:
        frame = ttk.Frame(self.content, padding=4)
        self.frames["prepare"] = frame
        ttk.Label(frame, text="Prepare G-code", font=("Segoe UI", 12, "bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 8)
        )
        ttk.Label(
            frame,
            text="Runs F-Engrave (batch), applies backlash compensation, and cleans the file for GRBL. Output is saved to the project output/ folder.",
            wraplength=640,
        ).grid(row=1, column=0, sticky="w")

        self.prepare_btn = ttk.Button(frame, text="Prepare G-code", command=self._run_prepare)
        self.prepare_btn.grid(row=2, column=0, sticky="w", pady=(12, 0))

        self.prepare_info = ttk.Label(frame, text="No job prepared yet.", wraplength=640)
        self.prepare_info.grid(row=3, column=0, sticky="w", pady=(12, 0))

        preview_frame = ttk.LabelFrame(frame, text="Preview", padding=8)
        preview_frame.grid(row=4, column=0, sticky="nsew", pady=(12, 0))
        self.preview_text = tk.Text(preview_frame, height=14, width=80, state="disabled")
        self.preview_text.pack(fill="both", expand=True)
        frame.rowconfigure(4, weight=1)

    def _build_hardware_frame(self) -> None:
        frame = ttk.Frame(self.content, padding=4)
        self.frames["hardware"] = frame
        ttk.Label(frame, text="Prepare the plotter", font=("Segoe UI", 12, "bold")).pack(
            anchor="w", pady=(0, 8)
        )
        ttk.Label(
            frame,
            text="Complete each step before sending. Zero the machine at your desired start corner.",
            wraplength=640,
        ).pack(anchor="w", pady=(0, 12))

        self.hw_checks: list[tk.BooleanVar] = []
        for item in HARDWARE_ITEMS:
            var = tk.BooleanVar(value=False)
            self.hw_checks.append(var)
            ttk.Checkbutton(frame, text=item, variable=var).pack(anchor="w", pady=3)

    def _build_send_frame(self) -> None:
        frame = ttk.Frame(self.content, padding=4)
        self.frames["send"] = frame
        ttk.Label(frame, text="Send to MakerPlot", font=("Segoe UI", 12, "bold")).grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 8)
        )

        ttk.Label(frame, text="COM port").grid(row=1, column=0, sticky="w")
        self.port_combo = ttk.Combobox(frame, textvariable=self.port_var, width=36, state="readonly")
        self.port_combo.grid(row=1, column=1, sticky="w", padx=8)
        ttk.Button(frame, text="Refresh ports", command=self._refresh_ports).grid(row=1, column=2)

        ttk.Label(frame, text="Baud rate").grid(row=2, column=0, sticky="w", pady=(8, 0))
        self.baud_var = tk.StringVar(value=str(self.cfg.baud_rate))
        ttk.Entry(frame, textvariable=self.baud_var, width=12).grid(
            row=2, column=1, sticky="w", padx=8, pady=(8, 0)
        )

        self.send_btn = ttk.Button(frame, text="Send G-code to plotter", command=self._run_send)
        self.send_btn.grid(row=3, column=0, columnspan=3, sticky="w", pady=(16, 0))

        self.send_info = ttk.Label(frame, text="", wraplength=640)
        self.send_info.grid(row=4, column=0, columnspan=3, sticky="w", pady=(12, 0))

    def _toggle_design_mode(self) -> None:
        is_text = self.mode_var.get() == "text"
        if is_text:
            self.text_panel.grid()
            self.image_panel.grid_remove()
        else:
            self.text_panel.grid_remove()
            self.image_panel.grid()

    def _show_step(self, index: int) -> None:
        self.current_step = index
        for frame in self.frames.values():
            frame.grid_remove()
        key = STEPS[index][1]
        self.frames[key].grid(row=0, column=0, sticky="nsew")
        self.content.rowconfigure(0, weight=1)

        for i, lbl in enumerate(self.step_labels):
            font = ("Segoe UI", 10, "bold") if i == index else ("Segoe UI", 10)
            lbl.configure(font=font)

        self.back_btn.configure(state="normal" if index > 0 else "disabled")
        self.next_btn.configure(
            text="Finish" if index == len(STEPS) - 1 else "Next →",
            state="normal",
        )
        self.status_var.set(f"Step {index + 1} of {len(STEPS)}: {STEPS[index][0]}")

        if key == "send":
            self._refresh_ports()

    def _prev_step(self) -> None:
        if self.current_step > 0:
            self._show_step(self.current_step - 1)

    def _next_step(self) -> None:
        if not self._validate_current_step():
            return
        if self.current_step < len(STEPS) - 1:
            self._show_step(self.current_step + 1)

    def _validate_current_step(self) -> bool:
        key = STEPS[self.current_step][1]
        if key == "setup":
            return self._save_setup(silent=False)
        if key == "design":
            if self.mode_var.get() == "text":
                if not self.text_input.get("1.0", "end").strip():
                    messagebox.showwarning("Design", "Enter text to plot.")
                    return False
            else:
                if not Path(self.image_var.get()).is_file():
                    messagebox.showwarning("Design", "Choose a valid image file.")
                    return False
        if key == "prepare":
            if not self.prepare_result:
                messagebox.showwarning("Prepare", "Click 'Prepare G-code' first.")
                return False
        if key == "hardware":
            if not all(v.get() for v in self.hw_checks):
                if not messagebox.askyesno(
                    "Hardware checklist",
                    "Not all hardware steps are checked. Continue anyway?",
                ):
                    return False
        return True

    def _append_log(self, message: str) -> None:
        self.log.configure(state="normal")
        self.log.insert("end", message + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _browse_makerplot(self) -> None:
        path = filedialog.askdirectory(initialdir=self.makerplot_var.get())
        if path:
            self.makerplot_var.set(path)

    def _browse_text_settings(self) -> None:
        path = filedialog.askopenfilename(
            initialdir=self.makerplot_var.get(),
            filetypes=[("F-Engrave settings", "*.txt"), ("All files", "*.*")],
        )
        if path:
            self.text_settings_var.set(path)

    def _browse_image_settings(self) -> None:
        path = filedialog.askopenfilename(
            initialdir=str(PROJECT_ROOT / "settings"),
            filetypes=[("F-Engrave settings", "*.txt"), ("All files", "*.*")],
        )
        if path:
            self.image_settings_var.set(path)

    def _browse_image(self) -> None:
        path = filedialog.askopenfilename(
            initialdir=self.makerplot_var.get(),
            filetypes=[("Images", "*.png;*.bmp;*.jpg;*.jpeg"), ("All files", "*.*")],
        )
        if path:
            self.image_var.set(path)

    def _save_setup(self, silent: bool = True) -> bool:
        try:
            self.cfg.makerplot_dir = self.makerplot_var.get()
            self.cfg.text_settings = self.text_settings_var.get()
            self.cfg.image_settings = self.image_settings_var.get()
            self.cfg.backlash_x = float(self.backlash_x.get())
            self.cfg.backlash_y = float(self.backlash_y.get())
            self.cfg.backlash_z = float(self.backlash_z.get())
        except ValueError:
            messagebox.showerror("Setup", "Backlash values must be numbers.")
            return False

        save_config(self.cfg, PROJECT_ROOT)
        ok, msg = self._validate_tools()
        self.tools_status.configure(text=msg)
        if not silent and not ok:
            messagebox.showwarning("Setup", msg)
        elif not silent:
            messagebox.showinfo("Setup", "Settings saved and tools validated.")
        return ok

    def _validate_tools(self) -> tuple[bool, str]:
        makerplot = self.cfg.resolved_makerplot()
        lines = []
        ok = True

        if bundled_apps_present():
            lines.append("✓ Bundled apps in vendor/ (self-contained)")
        else:
            lines.append("○ Bundled apps not complete — run “Copy apps to vendor/”")

        try:
            fengrave = find_fengrave(makerplot)
            src = "bundled" if fengrave == FENGRAVE_EXE else "kit"
            lines.append(f"✓ F-Engrave ({src}): {fengrave}")
        except FileNotFoundError as exc:
            lines.append(f"✗ F-Engrave: {exc}")
            ok = False

        self.java_path = find_java(self.cfg.java_path, makerplot)
        if self.java_path:
            src = "bundled" if self.java_path == JRE_JAVA else "system/kit"
            lines.append(f"✓ Java ({src}): {self.java_path}")
        else:
            lines.append("✗ Java not found — run bundle script or install JRE 17+")
            ok = False

        try:
            self.ugs_jar = ensure_ugs_jar(self.cfg.ugs_jar_path)
            src = "bundled" if self.ugs_jar == UGS_JAR else "downloaded"
            lines.append(f"✓ UGS Classic ({src}): {self.ugs_jar}")
        except Exception as exc:  # noqa: BLE001
            lines.append(f"✗ UGS Classic: {exc}")
            ok = False

        return ok, "\n".join(lines)

    def _run_bundle(self) -> None:
        script = PROJECT_ROOT / "scripts" / "bundle-apps.ps1"
        kit = self.makerplot_var.get().strip() or r"d:\Bambu\MakerPlot\GoogleDrive"
        if not Path(kit).is_dir():
            messagebox.showerror(
                "Bundle apps",
                f"MakerPlot kit folder not found:\n{kit}\n\nBrowse to your kit folder first.",
            )
            return
        self._append_log(f"Bundling apps from {kit}…")
        self.status_var.set("Copying applications…")

        def work() -> None:
            import subprocess

            try:
                proc = subprocess.run(
                    [
                        "powershell",
                        "-ExecutionPolicy",
                        "Bypass",
                        "-File",
                        str(script),
                        "-MakerPlotDir",
                        kit,
                    ],
                    capture_output=True,
                    text=True,
                    cwd=str(PROJECT_ROOT),
                )
                output = (proc.stdout or "") + (proc.stderr or "")

                def done() -> None:
                    for line in output.splitlines():
                        if line.strip():
                            self._append_log(line)
                    ok, msg = self._validate_tools()
                    self.tools_status.configure(text=msg)
                    self.status_var.set("Bundle finished.")
                    if proc.returncode == 0:
                        messagebox.showinfo("Bundle apps", "Applications copied to vendor/.")
                    else:
                        messagebox.showerror("Bundle apps", output[-500:] or "Bundle failed.")

                self.after(0, done)
            except Exception as exc:  # noqa: BLE001
                self.after(
                    0,
                    lambda: messagebox.showerror("Bundle apps", str(exc)),
                )

        threading.Thread(target=work, daemon=True).start()

    def _bootstrap_tools(self) -> None:
        def work() -> None:
            self._append_log("Checking tools…")
            ok, msg = self._validate_tools()
            self.after(0, lambda: self.tools_status.configure(text=msg))
            self.after(0, lambda: self._append_log(msg.replace("\n", "\n")))
            if ok:
                self.after(0, lambda: self._refresh_ports())

        threading.Thread(target=work, daemon=True).start()

    def _refresh_ports(self) -> None:
        def work() -> None:
            ports = list_serial_ports()
            ugs_ports: list[str] = []
            if self.java_path and self.ugs_jar:
                try:
                    ugs_ports = list_ports_via_ugs(self.java_path, self.ugs_jar)
                except Exception as exc:  # noqa: BLE001
                    self.after(0, lambda: self._append_log(f"UGS port list: {exc}"))

            labels = [p.label for p in ports]
            best = guess_best_port(ports, ugs_ports, self.cfg.last_com_port)

            def update() -> None:
                self.port_combo["values"] = labels or ugs_ports
                if best:
                    for p in ports:
                        if p.device == best:
                            self.port_var.set(p.label)
                            break
                    else:
                        self.port_var.set(best)
                self._append_log(
                    f"Ports: {', '.join(p.device for p in ports) or 'none detected'}"
                )

            self.after(0, update)

        threading.Thread(target=work, daemon=True).start()

    def _selected_port_device(self) -> str:
        value = self.port_var.get().strip()
        if "—" in value:
            return value.split("—", 1)[0].strip()
        return value

    def _run_prepare(self) -> None:
        if not self._save_setup(silent=True):
            messagebox.showerror("Prepare", "Fix setup issues before preparing.")
            return

        self.prepare_btn.configure(state="disabled")
        self._append_log("Preparing G-code…")

        mode = self.mode_var.get()
        text = self.text_input.get("1.0", "end").strip()
        image = Path(self.image_var.get()) if mode == "image" else None
        job_name = self.job_name_var.get().strip()

        def work() -> None:
            try:
                result = prepare_job(
                    self.cfg,
                    mode=mode,
                    text=text,
                    image_path=image,
                    job_name=job_name,
                )

                def done() -> None:
                    self.prepare_result = result
                    self.prepare_btn.configure(state="normal")
                    info = (
                        f"Ready file: {result.ready_path}\n"
                        f"{result.line_count} lines of G-code"
                    )
                    self.prepare_info.configure(text=info)
                    self.preview_text.configure(state="normal")
                    self.preview_text.delete("1.0", "end")
                    self.preview_text.insert("1.0", result.preview)
                    self.preview_text.configure(state="disabled")
                    self._append_log(f"Prepared: {result.ready_path}")
                    messagebox.showinfo("Prepare", "G-code is ready to send.")

                self.after(0, done)
            except Exception as exc:  # noqa: BLE001
                def fail() -> None:
                    self.prepare_btn.configure(state="normal")
                    self._append_log(f"Prepare failed: {exc}")
                    messagebox.showerror("Prepare", str(exc))

                self.after(0, fail)

        threading.Thread(target=work, daemon=True).start()

    def _run_send(self) -> None:
        if not self.prepare_result:
            messagebox.showwarning("Send", "Prepare G-code first (step 3).")
            return

        port = self._selected_port_device()
        if not port:
            messagebox.showwarning("Send", "Select a COM port.")
            return

        if not self.java_path or not self.ugs_jar:
            messagebox.showerror("Send", "Java or UGS Classic is not configured.")
            return

        try:
            baud = int(self.baud_var.get())
        except ValueError:
            messagebox.showerror("Send", "Baud rate must be an integer.")
            return

        if not messagebox.askyesno(
            "Send G-code",
            f"Send {self.prepare_result.ready_path.name} to {port}?\n\n"
            "Ensure the plotter is zeroed and the pen touches the paper.",
        ):
            return

        self.send_btn.configure(state="disabled")
        self.send_info.configure(text="Sending…")
        self._append_log(f"Sending to {port} @ {baud}…")

        gcode_file = self.prepare_result.ready_path

        def work() -> None:
            try:
                send_gcode(
                    self.java_path,
                    self.ugs_jar,
                    port=port,
                    baud=baud,
                    gcode_file=gcode_file,
                    on_output=lambda line: self.after(0, lambda l=line: self._append_log(l)),
                )

                def done() -> None:
                    self.send_btn.configure(state="normal")
                    self.send_info.configure(text="Plot finished.")
                    self.cfg.last_com_port = port
                    self.cfg.baud_rate = baud
                    save_config(self.cfg, PROJECT_ROOT)
                    messagebox.showinfo("Send", "G-code sent successfully.")

                self.after(0, done)
            except Exception as exc:  # noqa: BLE001
                def fail() -> None:
                    self.send_btn.configure(state="normal")
                    self.send_info.configure(text="Send failed.")
                    self._append_log(f"Send failed: {exc}")
                    messagebox.showerror("Send", str(exc))

                self.after(0, fail)

        threading.Thread(target=work, daemon=True).start()


def main() -> None:
    app = MakerPlotApp()
    app.mainloop()


if __name__ == "__main__":
    main()
