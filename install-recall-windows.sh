#!/usr/bin/env bash
# install-recall-windows.sh — Installateur de Recall Windows

set -e

SCRIPT="recall-windows.py"
BIN_DIR="$HOME/.local/bin"
APP_DIR="$HOME/.local/share/applications"
DESKTOP="recall-windows.desktop"

echo "Installation de Recall Windows..."

# Créer les répertoires si nécessaire
mkdir -p "$BIN_DIR"
mkdir -p "$APP_DIR"

# Copier le script
cp "$SCRIPT" "$BIN_DIR/$SCRIPT"
chmod +x "$BIN_DIR/$SCRIPT"
echo "  ✓ Script installé → $BIN_DIR/$SCRIPT"

# Créer le .desktop
cat > "$APP_DIR/$DESKTOP" << DESK
[Desktop Entry]
Encoding=UTF-8
Name=Recall Windows
Comment=Sauvegarde et restauration de layouts de fenêtres
Exec=$BIN_DIR/$SCRIPT -ui
Icon=computer
Terminal=false
Type=Application
StartupWMClass=recall-windows.py
Categories=GNOME;Application;Utility;
DESK
echo "  ✓ Lanceur créé → $APP_DIR/$DESKTOP"

# Mettre à jour la base des applications
update-desktop-database "$APP_DIR" 2>/dev/null || true

echo ""
echo "Installation terminée ✓"
echo "Recall Windows est disponible dans vos applications."
echo ""
echo "Raccourcis :"
echo "  python3 ~/.local/bin/recall-windows.py -read   # Sauvegarder"
echo "  python3 ~/.local/bin/recall-windows.py -run    # Restaurer"
echo "  python3 ~/.local/bin/recall-windows.py -ui     # Interface"
