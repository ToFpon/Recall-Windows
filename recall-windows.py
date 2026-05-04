#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# recall-windows.py — Sauvegarde et restauration de layout de fenêtres
# Usage : python3 recall-windows.py -read   (sauvegarder)
#         python3 recall-windows.py -run    (restaurer)
#         python3 recall-windows.py -ui     (interface graphique)
#License: GPLv3

import subprocess
import os
import sys
import time

WFILE   = os.path.expanduser("~/.windowlist")
TIMEOUT = 15

# Noms lisibles pour les workspaces
WS_NAMES = {
    0: "Bureau 1",
    1: "Bureau 2",
    2: "Bureau 3",
    3: "Bureau 4",
}

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
    """Nom lisible d'une commande."""
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
    """Sauvegarde le layout. ws_filter = liste de ws à sauvegarder, None = ws != -1."""
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

    # Si filtre → garder les autres workspaces, sinon tout écraser
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

    print(f"[claude] {len(windows)} fenêtres sauvegardées → {WFILE}")
    for cmd, ws, x, y, w, h in windows:
        print(f"  {WS_NAMES.get(ws, f'Bureau {ws+1}')} | {app_label(cmd):15s} {x},{y} {w}x{h}")
    return windows

def load_windowlist():
    """Charge ~/.windowlist → dict {ws: [(cmd,ws,x,y,w,h), ...]}"""
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
        print(f"[claude] Aucun layout sauvegardé ({WFILE})")
        return
    if ws_filter:
        by_ws = {k: v for k, v in by_ws.items() if k in ws_filter}
    total = sum(len(v) for v in by_ws.values())
    print(f"[claude] Restauration de {total} fenêtres...")
    for ws in sorted(by_ws):
        run(f"wmctrl -s {ws}")
        time.sleep(0.5)
        for item in by_ws[ws]:
            launch_and_position(*item)
    print("[claude] Layout restauré ✓")

# ── Interface GTK3 ────────────────────────────────────────────────────────────

def run_ui():
    import gi
    gi.require_version("Gtk", "3.0")
    from gi.repository import Gtk, GLib, Gio

    by_ws = load_windowlist()

    app = Gtk.Application.new("org.tof.recall-windows", Gio.ApplicationFlags.FLAGS_NONE)

    def on_activate(application):
        win = Gtk.ApplicationWindow(application=application, title="Recall Windows")
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
        title.set_markup("<b>Recall Windows</b>")
        title.set_halign(Gtk.Align.START)
        main_box.pack_start(title, False, False, 0)
    
        main_box.pack_start(Gtk.Separator(), False, False, 0)
    
        # ── Desktops + apps ───────────────────────────────────────────────────────
        ws_checks  = {}   # ws → Gtk.CheckButton desktop
        app_checks = {}   # ws → [Gtk.CheckButton app, ...]
    
        # Zone scrollable pour la liste des desktops/apps
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        main_box.pack_start(content_box, True, True, 0)
    
        if by_ws:
            for ws in sorted(by_ws):
                ws_name = WS_NAMES.get(ws, f"Bureau {ws+1}")
                ws_cb = Gtk.CheckButton(label=ws_name)
                ws_cb.set_active(True)
                content_box.pack_start(ws_cb, False, False, 0)
                ws_checks[ws] = ws_cb
                app_checks[ws] = []
                for cmd, _, x, y, w, h in by_ws[ws]:
                    label = f"  {app_label(cmd)}  ({x},{y}  {w}×{h})"
                    app_cb = Gtk.CheckButton(label=label)
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
                Gtk.Label(label="Aucun layout sauvegardé."), False, False, 0)
    
        main_box.pack_start(Gtk.Separator(), False, False, 0)
    
        # ── Status ────────────────────────────────────────────────────────────────
        status = Gtk.Label(label="")
        status.set_halign(Gtk.Align.START)
        status.set_line_wrap(True)
        main_box.pack_start(status, False, False, 0)
    
        # ── Boutons ───────────────────────────────────────────────────────────────
        def refresh_list():
            """Recharge ~/.windowlist et met à jour les checkboxes."""
            # Vider les widgets existants
            for child in content_box.get_children():
                content_box.remove(child)
    
            new_by_ws = load_windowlist()
            ws_checks.clear()
            app_checks.clear()
    
            if new_by_ws:
                for ws in sorted(new_by_ws):
                    ws_name = WS_NAMES.get(ws, f"Bureau {ws+1}")
                    ws_cb = Gtk.CheckButton(label=ws_name)
                    ws_cb.set_active(True)
                    content_box.pack_start(ws_cb, False, False, 0)
                    ws_checks[ws] = ws_cb
                    app_checks[ws] = []
                    for cmd, _, x, y, w, h in new_by_ws[ws]:
                        label = f"  {app_label(cmd)}  ({x},{y}  {w}×{h})"
                        app_cb = Gtk.CheckButton(label=label)
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
                    Gtk.Label(label="Aucun layout sauvegardé."), False, False, 0)
    
            content_box.show_all()
    
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        btn_box.set_homogeneous(True)
        main_box.pack_start(btn_box, False, False, 0)
    
        btn_save    = Gtk.Button(label="💾  Sauvegarder")
        btn_restore = Gtk.Button(label="▶  Restaurer")
        btn_restore.get_style_context().add_class("suggested-action")
        btn_box.pack_start(btn_save,    True, True, 0)
        btn_box.pack_start(btn_restore, True, True, 0)
    
        # ── Actions ───────────────────────────────────────────────────────────────
        def do_save(_):
            status.set_markup("<i>Sauvegarde en cours…</i>")
            while Gtk.events_pending():
                Gtk.main_iteration()
    
            ws_sel = [ws for ws, cb in ws_checks.items() if cb.get_active()]
            if not ws_sel:
                ws_sel = None
    
            saved = read_windows(ws_sel)
            n = len(saved)
            status.set_markup(f"<b>[claude]</b> {n} fenêtre(s) sauvegardée(s) ✓")
    
            # Rafraîchir la liste des desktops/apps
            refresh_list()
    
        def do_restore(_):
            # Collecter les items cochés
            items_by_ws = {}
            for ws, entries in app_checks.items():
                if not ws_checks.get(ws, Gtk.CheckButton()).get_active():
                    continue
                for app_cb, item in entries:
                    if app_cb.get_active():
                        items_by_ws.setdefault(ws, []).append(item)
    
            if not items_by_ws:
                status.set_markup("<i>Rien de sélectionné.</i>")
                return
    
            total = sum(len(v) for v in items_by_ws.values())
            status.set_markup(f"<i>Restauration de {total} fenêtre(s)…</i>")
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
                    status.set_markup("<b>[claude]</b> Layout restauré ✓"),
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
