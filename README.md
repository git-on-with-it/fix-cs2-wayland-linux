# fix-cs2-wayland

This script fixes two related CS2 (Counter-Strike 2, native Linux) bugs on
Wayland desktops. It is for the Ubuntu Steam Snap in particular. It also works
with other Steam installs. It does not need root. It does not need Python.

Version: **v1.1.0**. Run `fix-cs2-wayland --version` to print it.

## Background

The author installed Ubuntu with the Steam Snap and GNOME Wayland. CS2 showed
the stuck-mouse bug in the first session. A search found no working fix. The
common suggestions did not fix the mouse, or CS2 did not start on the Snap.
The author then inspected the running game container and the Steam Linux
Runtime. The inspection showed the root cause. This script is the result.

## Symptoms it fixes

**1. The mouse does not move in CS2.** It stays near the screen center.
Only a few millimeters of movement remain. The problem is random at each
start.

- Root cause 1: `game/cs2.sh` sets `SDL_VIDEO_DRIVER=x11`.
- On a Wayland desktop, this runs CS2 in XWayland.
- The SDL3 library inside CS2 has an XInput2 bug in XWayland.
- See [ValveSoftware/csgo-osx-linux#4354](https://github.com/ValveSoftware/csgo-osx-linux/issues/4354)
  and [libsdl-org/SDL#16163](https://github.com/libsdl-org/SDL/issues/16163).

**2. CS2 does not start after you set `SDL_VIDEO_DRIVER=wayland`.** This
happens on the Ubuntu Steam Snap only.

- Root cause 2: the Snap sets `DISABLE_WAYLAND=1`.
- The Snap sets `XDG_RUNTIME_DIR=/run/user/$UID/snap.steam`.
- It does not put the real Wayland socket in that directory.
- The container runtime (`SteamLinuxRuntime_sniper`, pressure-vessel) then
  does not mount the socket into the game container.
- CS2 cannot connect to Wayland. It exits at start.

## See the bug

Video clip and screenshots by
[u/Pretty_Library_2373](https://www.reddit.com/user/Pretty_Library_2373/).
This repo uses them with credit. If you are the author and do not want them
here, open an issue. They will be removed.

GIF of the bug, 12 seconds, from the original video:

![Stuck mouse demonstration](docs/media/mouse-bug-stuck.gif)

Full clip, 84 seconds, with sound:
[`docs/media/mouse-bug-linux-native.mp4`](docs/media/mouse-bug-linux-native.mp4).
You can also watch it in the original Reddit thread (see below).

The line in `game/cs2.sh` that forces X11:

![cs2.sh snippet](docs/media/cs2sh-snippet.png)

Original report, r/cs2, May 14 2026:

- Thread: <https://www.reddit.com/r/cs2/comments/1td29d6/mouse_bug_linux_native/>
- Video: <https://v.redd.it/tnzdwqp6i41h1>
- Full post screenshot: [`docs/media/original-post-screenshot.png`](docs/media/original-post-screenshot.png)

## Upstream fix status (checked 2026-11-01)

| Layer | Status |
|---|---|
| SDL bug ([libsdl-org/SDL#16163](https://github.com/libsdl-org/SDL/issues/16163)) | **Fixed.** PR [#16267](https://github.com/libsdl-org/SDL/pull/16267), merged 2026-09-10. Shipped in SDL 3.4.18. |
| Steam Linux Runtime sniper ([steam-runtime#857](https://github.com/ValveSoftware/steam-runtime/issues/857)) | **Closed** 2026-10-23. Runtime 3.0.20261021 ships `libSDL3.so.0.4.18`. |
| CS2 ([csgo-osx-linux#4354](https://github.com/ValveSoftware/csgo-osx-linux/issues/4354)) | **Open.** Reports continued in November 2026. |

Why is CS2 still affected? CS2 does not use the SDL from the runtime. It
uses its own copy: `game/bin/linuxsteamrt64/libSDL3.so.0`. This copy is from
a `3.5.0-HEAD` build. Thus the runtime fix does not reach CS2. This is why
reports continue after #857 closed. This script uses the Wayland path
instead. The bug does not exist on that path.

## What the script does

- Sets `SDL_VIDEO_DRIVER=wayland` in `game/cs2.sh`. It does this only on
  Wayland sessions.
- Creates `$XDG_RUNTIME_DIR/snap.steam/$WAYLAND_DISPLAY -> ../$WAYLAND_DISPLAY`.
- Installs a small user systemd unit. The symlink is rebuilt at each login.
- Patches `SteamLinuxRuntime_sniper/_v2-entry-point`. The entry point then
  creates the symlink before the container starts.
- Saves a `.backup-before-wayland-fix` copy next to every file it changes.
- You can run it again at any time. It also repairs the files after a CS2 or
  Steam Runtime update.

## Display mode: fullscreen vs borderless

The script does not change CS2 display settings. It only changes the graphics
driver. The config file is
`~/…/userdata/<UID>/730/local/cfg/cs2_video.txt`. The author uses borderless
mode: `fullscreen=0`, `nowindowborder=1`.

Note: borderless fills the whole screen. It looks like true fullscreen, but
it is not. Check your `cs2_video.txt` to know your mode:

- `setting.fullscreen "0"` + `setting.nowindowborder "1"` = borderless.
- `setting.fullscreen "1"` = true fullscreen.

Change the mode in the game menu only (Settings → Video). CS2 writes the
config file again at each start. Manual edits do not stay.

Before the fix, true fullscreen failed on this machine:

- Sometimes input lag or the stuck mouse occurred.
- Sometimes the GNOME top bar stayed over the game.
- Sometimes CS2 changed back to borderless at the next start.

Important: all these tests ran on X11/XWayland, not on Wayland. After the
fix, CS2 runs on Wayland here. The result is different:

- On Wayland, the CS2 video menu offers only `Windowed` and
  `Fullscreen Windowed`. Plain `Fullscreen` is not in the list anymore.
- Reason: the SDL Wayland backend does not give CS2 an exclusive fullscreen
  mode. On Wayland, borderless is the normal fullscreen path. The
  compositor manages it directly.
- Thus the old fullscreen problems do not apply on Wayland. Borderless is
  the mode to use here. The author tested it on 2026-11-01:
  no input lag, no stuck mouse.

**Community test (voluntary).** If you had the fullscreen lag symptom, and
you applied this fix:

1. Open Settings → Video in CS2. Select true Fullscreen.
2. Play one round. Compare the input lag with borderless mode.
3. Post your result on the [issue thread](https://github.com/ValveSoftware/csgo-osx-linux/issues/4354).

Every result helps: better, same, or worse. Write down your `cs2_video.txt`
values before the test.

Update 2026-11-01, author test: on Wayland, plain `Fullscreen` is not in the
CS2 menu at all. Only `Windowed` and `Fullscreen Windowed` are offered.
`Fullscreen Windowed` works with no input lag and no stuck mouse. If your
menu still shows plain `Fullscreen`, you are still running on XWayland —
check `fix-cs2-wayland --status`.

## Install

```bash
mkdir -p ~/.local/bin
cp fix-cs2-wayland ~/.local/bin/
chmod +x ~/.local/bin/fix-cs2-wayland   # adjust PATH if needed
```

## Usage

```bash
fix-cs2-wayland            # apply (default); skips pure X11 sessions safely
fix-cs2-wayland --status   # show detection and state; changes nothing
fix-cs2-wayland --revert   # restore all backups; remove service and symlink
fix-cs2-wayland --force    # apply without a detected Wayland session
STEAM_DIR=/games/Steam fix-cs2-wayland   # set the Steam library location
```

## Supported setups

| Install         | Detected via                                   | Notes                                  |
|-----------------|------------------------------------------------|----------------------------------------|
| Native (deb/rpm)| `~/.local/share/Steam`, `~/.steam/steam`       | Snap bridge is not installed          |
| Ubuntu Snap     | `~/snap/steam/common/.local/share/Steam`       | Bridge + service + entry-point patch  |
| Flatpak         | `~/.var/app/com.valvesoftware.Steam/...`       | Snap bridge is not installed          |
| Custom libraries| `libraryfolders.vdf` or `STEAM_DIR`            | The script scans all libraries        |

## Troubleshooting

- The mouse is still stuck? Stop CS2 and Steam fully. Start Steam again.
  Run `fix-cs2-wayland --status`. Verify:
  `cs2.sh` shows `SDL_VIDEO_DRIVER=wayland`, and the entry point shows
  `patched`.
- CS2 crashes on Wayland after an update? Run `fix-cs2-wayland --revert`.
  This restores the original files. The mouse bug returns with them.
- Other start failures? Start CS2 from a terminal
  (Steam → "Launch in a terminal"). The SDL Wayland backend needs a running
  Wayland compositor (GNOME, KDE, Sway, and others).

## Feedback

- It works? Write a comment on the
  [issue thread](https://github.com/ValveSoftware/csgo-osx-linux/issues/4354)
  and in the
  [Reddit thread](https://www.reddit.com/r/cs2/comments/1td29d6/mouse_bug_linux_native/).
  Valve needs the number of affected players.
- It does not work? Open an issue here. Include the output of
  `fix-cs2-wayland --status`.

## Tested on

- Ubuntu 26.10, GNOME Wayland (`XDG_SESSION_TYPE=wayland`)
- Steam Snap 1.0.0.87 (core24), SteamLinuxRuntime_sniper 3.0.20261021.x
- CS2 native Linux client with its own `libSDL3.so.0` (`3.5.0-HEAD`, 2026-10)
- AMD RADV (GFX11). NVIDIA and other GPU reports are welcome.

## License

MIT. See [LICENSE](LICENSE).
