#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# recall-windows.py — Sauvegarde et restauration de layout de fenêtres
# Usage : python3 recall-windows.py -read   (sauvegarder)
#         python3 recall-windows.py -run    (restaurer)
#         python3 recall-windows.py -ui     (interface graphique)
# License: GPLv3

import subprocess
import os
import sys
import time
import locale

WFILE   = os.path.expanduser("~/.windowlist")
TIMEOUT = 15

# ── i18n ─────────────────────────────────────────────────────────────────────
_lang = locale.getlocale()[0] or ""

if _lang.startswith("fr"):
    T = {
        "title":         "Recall Windows",
        "save":          "💾  Sauvegarder",
        "restore":       "▶  Restaurer",
        "autostart":     "🚀  Démarrage auto",
        "autostart_on":  "✓  Démarrage auto activé",
        "saving":        "Sauvegarde en cours…",
        "saved":         "{n} fenêtre(s) sauvegardée(s) ✓",
        "restoring":     "Restauration de {n} fenêtre(s)…",
        "restored":      "Layout restauré ✓",
        "nothing":       "Rien de sélectionné.",
        "no_layout":     "Aucun layout sauvegardé.",
        "ws_names":      {0:"Bureau 1", 1:"Bureau 2", 2:"Bureau 3", 3:"Bureau 4"},
        "autostart_msg": "Recall Windows sera lancé au démarrage de la session.",
        "autostart_err": "Erreur lors de la création du raccourci de démarrage.",
    }
elif _lang.startswith("de"):
    T = {
        "title":         "Recall Windows",
        "save":          "💾  Speichern",
        "restore":       "▶  Wiederherstellen",
        "autostart":     "🚀  Autostart",
        "autostart_on":  "✓  Autostart aktiviert",
        "saving":        "Wird gespeichert…",
        "saved":         "{n} Fenster gespeichert ✓",
        "restoring":     "{n} Fenster werden wiederhergestellt…",
        "restored":      "Layout wiederhergestellt ✓",
        "nothing":       "Nichts ausgewählt.",
        "no_layout":     "Kein gespeichertes Layout.",
        "ws_names":      {0:"Desktop 1", 1:"Desktop 2", 2:"Desktop 3", 3:"Desktop 4"},
        "autostart_msg": "Recall Windows wird beim Sitzungsstart gestartet.",
        "autostart_err": "Fehler beim Erstellen des Autostarts.",
    }
else:
    T = {
        "title":         "Recall Windows",
        "save":          "💾  Save",
        "restore":       "▶  Restore",
        "autostart":     "🚀  Autostart",
        "autostart_on":  "✓  Autostart enabled",
        "saving":        "Saving…",
        "saved":         "{n} window(s) saved ✓",
        "restoring":     "Restoring {n} window(s)…",
        "restored":      "Layout restored ✓",
        "nothing":       "Nothing selected.",
        "no_layout":     "No saved layout.",
        "ws_names":      {0:"Desktop 1", 1:"Desktop 2", 2:"Desktop 3", 3:"Desktop 4"},
        "autostart_msg": "Recall Windows will start at session startup.",
        "autostart_err": "Error creating autostart entry.",
    }

WS_NAMES = T["ws_names"]

# ── Core functions ────────────────────────────────────────────────────────────

def run(cmd):
    return subprocess.check_output(
        cmd, shell=True, stderr=subprocess.DEVNULL).decode()

def get_cmdline(pid):
    try:
        with open(f"/proc/{pid}/cmdline") as f:
            parts = f.read().split("\x00")
        return " ".join(p for p in parts if p)
    except Exception:
        return ""

def is_normal_window(wid):
    try:
        return "_NET_WM_WINDOW_TYPE_NORMAL" in run(f"xprop -id {wid}")
    except Exception:
        return False

def app_label(cmd):
    base = os.path.basename(cmd.split()[0])
    labels = {
        "brave": "Brave", "chrome": "Chrome", "firefox": "Firefox",
        "gnome-terminal-server": "Terminal", "nautilus": "Nautilus",
        "gedit": "Gedit", "code": "VS Code", "thunderbird": "Thunderbird",
    }
    for key, label in labels.items():
        if key in base:
            return label
    return base.capitalize()

def read_windows(ws_filter=None):
    windows = []
    for line in run("wmctrl -lpG").splitlines():
        parts = line.split(None, 8)
        if len(parts) < 7:
            continue
        wid = parts[0]
        ws  = int(parts[1])
        pid = parts[2]
        x, y, w, h = int(parts[3]), int(parts[4]), int(parts[5]), int(parts[6])
        if ws == -1:
            continue
        if ws_filter is not None and ws not in ws_filter:
            continue
        if not is_normal_window(wid):
            continue
        cmd = get_cmdline(pid)
        if not cmd:
            continue
        if "recall-windows" in cmd:
            continue
        windows.append((cmd, ws, x, y, w, h))

    existing = []
    if ws_filter is not None:
        try:
            for line in open(WFILE).read().splitlines():
                if not line.strip():
                    continue
                parts = line.split(None, 5)
                if len(parts) < 6:
                    continue
                ws_e = int(parts[0])
                if ws_e not in ws_filter:
                    existing.append(line)
        except FileNotFoundError:
            pass

    with open(WFILE, "w") as f:
        for line in existing:
            f.write(line + "\n")
        for cmd, ws, x, y, w, h in windows:
            f.write(f"{ws} {x} {y} {w} {h} {cmd}\n")

    print(f"[claude] {len(windows)} " + T["saved"].format(n=len(windows)) + f" → {WFILE}")
    for cmd, ws, x, y, w, h in windows:
        print(f"  {WS_NAMES.get(ws, f'Desktop {ws+1}')} | {app_label(cmd):15s} {x},{y} {w}x{h}")
    return windows

def load_windowlist():
    by_ws = {}
    try:
        for line in open(WFILE).read().splitlines():
            if not line.strip():
                continue
            parts = line.split(None, 5)
            if len(parts) < 6:
                continue
            ws, x, y, w, h, cmd = int(parts[0]), int(parts[1]), int(parts[2]), \
                                    int(parts[3]), int(parts[4]), parts[5]
            by_ws.setdefault(ws, []).append((cmd, ws, x, y, w, h))
    except FileNotFoundError:
        pass
    return by_ws

def get_all_wids():
    return set(line.split()[0]
               for line in run("wmctrl -lp").splitlines()
               if len(line.split()) >= 3)

CMD_MAP = {
    "/usr/libexec/gnome-terminal-server": "gnome-terminal --window",
    "/usr/bin/nautilus --gapplication-service": "nautilus -w",
    "/usr/bin/nautilus": "nautilus -w",
}

def user_cmd(cmd):
    for pattern, replacement in CMD_MAP.items():
        if cmd.startswith(pattern):
            return replacement
    return cmd

def launch_and_position(cmd, ws, x, y, w, h):
    cmd = user_cmd(cmd)
    before = get_all_wids()
    subprocess.Popen(cmd, shell=True)
    wid = None
    for _ in range(TIMEOUT * 2):
        time.sleep(0.5)
        new = get_all_wids() - before
        if new:
            wid = next(iter(new))
            break
    if not wid:
        print(f"  TIMEOUT : {cmd[:50]}")
        return
    run(f"wmctrl -ir {wid} -t {ws}")
    time.sleep(0.3)
    run(f"wmctrl -ir {wid} -b remove,maximized_vert,maximized_horz")
    time.sleep(0.1)
    run(f"wmctrl -ir {wid} -e 0,{x},{y},{w},{h}")
    print(f"  OK {WS_NAMES.get(ws, ws)} | {app_label(cmd):15s} {x},{y} {w}x{h}")

def run_remembered(ws_filter=None):
    by_ws = load_windowlist()
    if not by_ws:
        print(f"[claude] " + T["no_layout"])
        return
    if ws_filter:
        by_ws = {k: v for k, v in by_ws.items() if k in ws_filter}
    total = sum(len(v) for v in by_ws.values())
    print(f"[claude] " + T["restoring"].format(n=total))
    for ws in sorted(by_ws):
        run(f"wmctrl -s {ws}")
        time.sleep(0.5)
        for item in by_ws[ws]:
            launch_and_position(*item)
    print(f"[claude] " + T["restored"])

# ── Autostart ─────────────────────────────────────────────────────────────────

def autostart_path():
    return os.path.expanduser("~/.config/autostart/recall-windows.desktop")

def is_autostart_enabled():
    return os.path.isfile(autostart_path())

def enable_autostart():
    script = os.path.abspath(__file__)
    os.makedirs(os.path.expanduser("~/.config/autostart"), exist_ok=True)
    content = f"""[Desktop Entry]
Encoding=UTF-8
Name=Recall Windows
Comment=Restore window layout at session start
Exec=python3 {script} -run
Icon=computer
Terminal=false
Type=Application
StartupWMClass=recall-windows.py
Categories=GNOME;Application;Utility;
X-GNOME-Autostart-enabled=true
"""
    with open(autostart_path(), "w") as f:
        f.write(content)

def disable_autostart():
    try:
        os.remove(autostart_path())
    except FileNotFoundError:
        pass

# ── Interface GTK3 ────────────────────────────────────────────────────────────

def run_ui():
    import gi
    gi.require_version("Gtk", "3.0")
    from gi.repository import Gtk, GLib, Gio

    by_ws = load_windowlist()
    app = Gtk.Application.new("org.tof.recall-windows", Gio.ApplicationFlags.FLAGS_NONE)

    def on_activate(application):
        win = Gtk.ApplicationWindow(application=application, title=T["title"])
        win.set_border_width(16)
        win.set_resizable(False)
        try:
            win.set_icon_from_file(os.path.expanduser(
                "~/.local/share/icons/KoraTof/devices/scalable/computer.svg"))
        except Exception:
            win.set_icon_name("computer")

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        win.add(main_box)

        # Titre
        title = Gtk.Label()
        title.set_markup(f"<b>{T['title']}</b>")
        title.set_halign(Gtk.Align.START)
        main_box.pack_start(title, False, False, 0)

        main_box.pack_start(Gtk.Separator(), False, False, 0)

        ws_checks  = {}
        app_checks = {}

        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        main_box.pack_start(content_box, True, True, 0)

        def populate(data):
            for child in content_box.get_children():
                content_box.remove(child)
            ws_checks.clear()
            app_checks.clear()

            if data:
                for ws in sorted(data):
                    ws_name = WS_NAMES.get(ws, f"Desktop {ws+1}")
                    ws_cb = Gtk.CheckButton(label=ws_name)
                    ws_cb.set_active(True)
                    content_box.pack_start(ws_cb, False, False, 0)
                    ws_checks[ws] = ws_cb
                    app_checks[ws] = []
                    for cmd, _, x, y, w, h in data[ws]:
                        lbl = f"  {app_label(cmd)}  ({x},{y}  {w}×{h})"
                        app_cb = Gtk.CheckButton(label=lbl)
                        app_cb.set_active(True)
                        app_cb.set_margin_start(20)
                        content_box.pack_start(app_cb, False, False, 0)
                        app_checks[ws].append((app_cb, (cmd, ws, x, y, w, h)))

                    def on_ws_toggle(cb, _ws=ws):
                        for app_cb, _ in app_checks[_ws]:
                            app_cb.set_sensitive(cb.get_active())
                            app_cb.set_active(cb.get_active())
                    ws_cb.connect("toggled", on_ws_toggle)
            else:
                content_box.pack_start(
                    Gtk.Label(label=T["no_layout"]), False, False, 0)

            content_box.show_all()

        populate(by_ws)

        main_box.pack_start(Gtk.Separator(), False, False, 0)

        status = Gtk.Label(label="")
        status.set_halign(Gtk.Align.START)
        status.set_line_wrap(True)
        main_box.pack_start(status, False, False, 0)

        # ── Boutons principaux ────────────────────────────────────────────────
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        btn_box.set_homogeneous(True)
        main_box.pack_start(btn_box, False, False, 0)

        btn_save    = Gtk.Button(label=T["save"])
        btn_restore = Gtk.Button(label=T["restore"])
        btn_restore.get_style_context().add_class("suggested-action")
        btn_box.pack_start(btn_save,    True, True, 0)
        btn_box.pack_start(btn_restore, True, True, 0)

        # ── Bouton autostart ──────────────────────────────────────────────────
        autostart_lbl = T["autostart_on"] if is_autostart_enabled() else T["autostart"]
        btn_autostart = Gtk.Button(label=autostart_lbl)
        btn_autostart.add_css_class("flat") if hasattr(btn_autostart, "add_css_class") else None
        btn_autostart.get_style_context().add_class("flat")
        main_box.pack_start(btn_autostart, False, False, 0)

        def do_autostart(_):
            if is_autostart_enabled():
                disable_autostart()
                btn_autostart.set_label(T["autostart"])
                status.set_markup(f"<i>Autostart disabled.</i>")
            else:
                try:
                    enable_autostart()
                    btn_autostart.set_label(T["autostart_on"])
                    status.set_markup(f"<b>[claude]</b> {T['autostart_msg']}")
                except Exception as e:
                    status.set_markup(f"<i>{T['autostart_err']} {e}</i>")

        btn_autostart.connect("clicked", do_autostart)

        # ── Actions ───────────────────────────────────────────────────────────
        def do_save(_):
            status.set_markup(f"<i>{T['saving']}</i>")
            while Gtk.events_pending():
                Gtk.main_iteration()
            ws_sel = [ws for ws, cb in ws_checks.items() if cb.get_active()] or None
            saved  = read_windows(ws_sel)
            n      = len(saved)
            status.set_markup(f"<b>[claude]</b> {T['saved'].format(n=n)}")
            populate(load_windowlist())

        def do_restore(_):
            items_by_ws = {}
            for ws, entries in app_checks.items():
                if not ws_checks.get(ws, Gtk.CheckButton()).get_active():
                    continue
                for app_cb, item in entries:
                    if app_cb.get_active():
                        items_by_ws.setdefault(ws, []).append(item)

            if not items_by_ws:
                status.set_markup(f"<i>{T['nothing']}</i>")
                return

            total = sum(len(v) for v in items_by_ws.values())
            status.set_markup(f"<i>{T['restoring'].format(n=total)}</i>")
            btn_restore.set_sensitive(False)
            while Gtk.events_pending():
                Gtk.main_iteration()

            def _work():
                for ws in sorted(items_by_ws):
                    run(f"wmctrl -s {ws}")
                    time.sleep(0.5)
                    for item in items_by_ws[ws]:
                        launch_and_position(*item)
                GLib.idle_add(lambda: (
                    status.set_markup(f"<b>[claude]</b> {T['restored']}"),
                    btn_restore.set_sensitive(True)
                ) and False)

            import threading
            threading.Thread(target=_work, daemon=True).start()

        btn_save.connect("clicked", do_save)
        btn_restore.connect("clicked", do_restore)

        win.show_all()

    app.connect("activate", on_activate)
    app.run(None)

# ── Main ──────────────────────────────────────────────────────────────────────
if len(sys.argv) != 2 or sys.argv[1] not in ("-read", "-run", "-ui"):
    print("Usage : recall-windows.py -read | -run | -ui")
    sys.exit(1)

if sys.argv[1] == "-read":
    read_windows()
elif sys.argv[1] == "-run":
    run_remembered()
elif sys.argv[1] == "-ui":
    run_ui()
