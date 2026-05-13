# Recall Windows

**Save and restore window layouts on Linux/X11**

---

## Description

Recall Windows saves the layout of your open windows (position, size, workspace) and restores it in one click. Perfect for instantly recovering your usual work environment after a reboot or a different work session.

## Features

- Save windows per workspace
- Selective restore by desktop and application
- GTK3 graphical interface with checkboxes
- Autostart toggle — restore your layout automatically at session start
- Automatic exclusion of system windows (conky, etc.)
- Intelligent mapping of server processes to the correct launch commands
- Real-time feedback during restore
- French 🇫🇷 · English 🇬🇧 · German 🇩🇪

## Requirements

```bash
sudo apt install wmctrl xprop python3-gi
```

## Installation

```bash
# Run the installer from the folder containing recall-windows.py
chmod +x install-recall-windows.sh
./install-recall-windows.sh
```

The installer copies the script to `~/.local/bin/` and creates a launcher in `~/.local/share/applications/`.

## Usage

### Command line

```bash
# Save the current layout
python3 recall-windows.py -read

# Restore the saved layout
python3 recall-windows.py -run

# Open the graphical interface
python3 recall-windows.py -ui
```

### Graphical interface

The interface displays saved desktops and applications with checkboxes to select what you want to restore.

- **Save** — saves the current layout and refreshes the list
- **Restore** — restores checked windows to their saved position
- **Autostart** — toggles automatic restore at session start (creates/removes `~/.config/autostart/recall-windows.desktop`)

## Save file

The layout is stored in `~/.windowlist` in the following format:

```
workspace x y width height command
```

Example:
```
0 0 0 1920 1080 /opt/brave.com/brave/brave
1 960 0 960 540 gnome-terminal --window
1 960 540 960 540 nautilus -w
```

## Keyboard shortcut

Via system settings → Keyboard shortcuts → Custom shortcut:

| Command | Suggested shortcut |
|---|---|
| `python3 ~/.local/bin/recall-windows.py -ui` | `Super+R` |
| `python3 ~/.local/bin/recall-windows.py -run` | `Super+Shift+R` |

## Adding an application to CMD_MAP

If an application does not restore correctly, add its mapping in the script:

```python
CMD_MAP = {
    "/usr/libexec/gnome-terminal-server": "gnome-terminal --window",
    "/usr/bin/nautilus --gapplication-service": "nautilus -w",
    # Add your applications here
    "/usr/lib/firefox/firefox": "firefox --new-window",
}
```

To find the exact process command of an application:

```bash
cat /proc/$(pgrep -f myapp)/cmdline | tr '\0' ' '
```

## Limitations

- **X11 only** — not compatible with Wayland
- Requires `wmctrl` and `xprop`
- Restore is sequential — each window waits to be visible before moving to the next

## License

GNU General Public License v3.0 — see [https://www.gnu.org/licenses/](https://www.gnu.org/licenses/)

## Author

Tof

---

# Recall Windows (Français)

**Sauvegarde et restauration de layouts de fenêtres sous Linux/X11**

---

## Description

Recall Windows permet de sauvegarder la disposition de vos fenêtres (position, taille, workspace) et de la restaurer en un clic. Idéal pour retrouver instantanément votre environnement de travail habituel après un redémarrage ou une session de travail différente.

## Fonctionnalités

- Sauvegarde des fenêtres par workspace
- Restauration sélective par desktop et par application
- Interface graphique GTK3 avec checkboxes
- Démarrage automatique — restaure votre layout au démarrage de session
- Exclusion automatique des fenêtres système (conky, etc.)
- Mapping intelligent des process serveurs vers les bonnes commandes
- Feedback en temps réel pendant la restauration
- Français 🇫🇷 · Anglais 🇬🇧 · Allemand 🇩🇪

## Prérequis

```bash
sudo apt install wmctrl xprop python3-gi
```

## Installation

```bash
# Lancer l'installateur depuis le dossier contenant recall-windows.py
chmod +x install-recall-windows.sh
./install-recall-windows.sh
```

L'installateur copie le script dans `~/.local/bin/` et crée un lanceur dans `~/.local/share/applications/`.

## Utilisation

### Ligne de commande

```bash
# Sauvegarder le layout actuel
python3 recall-windows.py -read

# Restaurer le layout sauvegardé
python3 recall-windows.py -run

# Ouvrir l'interface graphique
python3 recall-windows.py -ui
```

### Interface graphique

L'interface affiche la liste des desktops et applications sauvegardés avec des checkboxes pour sélectionner ce que vous souhaitez restaurer.

- **Sauvegarder** — enregistre le layout actuel et rafraîchit la liste
- **Restaurer** — restaure les fenêtres cochées dans leur position d'origine
- **Démarrage auto** — active/désactive la restauration automatique au démarrage de session (crée/supprime `~/.config/autostart/recall-windows.desktop`)

## Fichier de sauvegarde

Le layout est stocké dans `~/.windowlist` au format :

```
workspace x y largeur hauteur commande
```

Exemple :
```
0 0 0 1920 1080 /opt/brave.com/brave/brave
1 960 0 960 540 gnome-terminal --window
1 960 540 960 540 nautilus -w
```

## Ajouter un raccourci clavier

Via les paramètres système → Raccourcis clavier → Raccourci personnalisé :

| Commande | Raccourci suggéré |
|---|---|
| `python3 ~/.local/bin/recall-windows.py -ui` | `Super+R` |
| `python3 ~/.local/bin/recall-windows.py -run` | `Super+Shift+R` |

## Ajouter une application au CMD_MAP

Si une application ne se restaure pas correctement, ajoutez son mapping dans le script :

```python
CMD_MAP = {
    "/usr/libexec/gnome-terminal-server": "gnome-terminal --window",
    "/usr/bin/nautilus --gapplication-service": "nautilus -w",
    # Ajouter ici vos applications
    "/usr/lib/firefox/firefox": "firefox --new-window",
}
```

Pour trouver le process exact d'une application :

```bash
cat /proc/$(pgrep -f monapp)/cmdline | tr '\0' ' '
```

## Limitations

- **X11 uniquement** — non compatible Wayland
- Nécessite `wmctrl` et `xprop`
- La restauration est séquentielle — chaque fenêtre attend d'être visible avant de passer à la suivante

## Licence

GNU General Public License v3.0 — voir [https://www.gnu.org/licenses/](https://www.gnu.org/licenses/)

## Auteur

Tof
