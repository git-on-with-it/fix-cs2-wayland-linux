# fix-cs2-wayland

One-command fix for two related CS2 (Counter-Strike 2, native Linux) bugs on
Wayland desktops — Ubuntu Steam Snap in particular. No root, no python.

Current version: **v1.0.0** (see `fix-cs2-wayland --version`).

## Symptoms it fixes

1. **Mouse barely moves in-game** (stuck near center, only a few mm of movement,
   random per launch) — tracked at
   [ValveSoftware/csgo-osx-linux#4354](https://github.com/ValveSoftware/csgo-osx-linux/issues/4354)
   and [libsdl-org/SDL#16163](https://github.com/libsdl-org/SDL/issues/16163).
   Root cause: CS2's launcher forces `SDL_VIDEO_DRIVER=x11`, which on a Wayland
   desktop means XWayland, and CS2's bundled SDL3 mis-decodes XInput2 relative
   valuators there.
2. **CS2 won't launch after changing it to `wayland` on Ubuntu's Steam Snap.**
   Root cause: the Snap sets `DISABLE_WAYLAND=1` and
   `XDG_RUNTIME_DIR=/run/user/$UID/snap.steam` and never links the real
   Wayland socket there, so Steam's container runtime
   (`SteamLinuxRuntime_sniper` / pressure-vessel) drops the socket and
   CS2 exits on startup.

## What it does

- Sets `export SDL_VIDEO_DRIVER=wayland` in `game/cs2.sh` (only on Wayland sessions).
- Creates `$XDG_RUNTIME_DIR/snap.steam/$WAYLAND_DISPLAY -> ../$WAYLAND_DISPLAY`
  and installs a small oneshot user systemd unit so it survives reboots.
- Patches `SteamLinuxRuntime_sniper/_v2-entry-point` to create that symlink
  itself before the container is built (covers Snaps with the disabled bridge).
- Saves a `.backup-before-wayland-fix` copy next to every file it touches.
- Re-running is safe (idempotent), and it repairs itself after CS2 or
  Steam Runtime updates.

## Install

```bash
mkdir -p ~/.local/bin
cp fix-cs2-wayland ~/.local/bin/
chmod +x ~/.local/bin/fix-cs2-wayland   # adjust PATH if needed
```

## Usage

```bash
fix-cs2-wayland            # apply (default); safely skips pure X11 sessions
fix-cs2-wayland --status   # inspect without changing anything
fix-cs2-wayland --revert   # restore all backups, remove service + symlink
fix-cs2-wayland --force    # apply even without a Wayland session detected
STEAM_DIR=/games/Steam fix-cs2-wayland   # override library discovery
```

## Supported setups

| Install         | Detected via                                   | Notes                                  |
|-----------------|------------------------------------------------|----------------------------------------|
| Native (deb/rpm)| `~/.local/share/Steam`, `~/.steam/steam`       | No Snap bridge installed               |
| Ubuntu Snap     | `~/snap/steam/common/.local/share/Steam`       | Bridge + service + entry-point patch   |
| Flatpak         | `~/.var/app/com.valvesoftware.Steam/...`       | No Snap bridge installed               |
| Custom libraries| `libraryfolders.vdf` or `STEAM_DIR`            | All libraries scanned                  |

## Troubleshooting

- **Still stuck mouse after applying?** Fully quit CS2 and Steam, launch Steam
  again, and verify with `--status` that `cs2.sh` shows
  `SDL_VIDEO_DRIVER=wayland` and the entry point shows `patched`.
- **CS2 crashes on Wayland after an update?** `fix-cs2-wayland --revert`
  restores the stock behaviour; the mouse bug returns with it.
- Launch CS2 once from a terminal via Steam ("Launch in a terminal") if you hit
  a different failure; the Valve wayland backend needs a running Wayland
  compositor (GNOME/KDE/Sway etc.).

## Feedback

Works for you? Please say so on the
[issue thread](https://github.com/ValveSoftware/csgo-osx-linux/issues/4354) —
Valve needs to know how many players this affects.

## Tested On
- Ubuntu 26.10 (GNOME Wayland, XDG_SESSION_TYPE=wayland)
- Steam Snap 1.0.0.87 (core24), SteamLinuxRuntime_sniper 3.0.20261021.x
- CS2 native Linux client, bundled `libSDL3.so.0` (`3.5.0-HEAD` as of 2026-10)
- AMD RADV (GFX11); NVIDIA/other GPU reports welcome

## License

MIT (see [LICENSE](LICENSE))
