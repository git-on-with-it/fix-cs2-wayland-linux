# Community Post — ready to publish

Two ready-to-paste texts follow. Use the text that matches your target.
Repository URL used in both texts:
<https://github.com/git-on-with-it/fix-cs2-wayland-linux>

---

## 1) Comment for the Valve issue thread

Target: https://github.com/ValveSoftware/csgo-osx-linux/issues/4354

**Root cause found for the "stuck mouse" and for the "SDL_VIDEO_DRIVER=wayland does not start" reports on the Ubuntu Steam Snap. Script and diagnosis included.**

I found this bug after a clean Ubuntu install (Steam Snap, GNOME Wayland).
CS2 showed the bug in the first session. A search found no working fix.
Existing suggestions did not fix the mouse, or CS2 did not start on the Snap.

I inspected the running game container. I tested SDL inside the Steam Linux
Runtime. Results, verified on Ubuntu 26.10, GNOME Wayland, Steam Snap
1.0.0.87:

**1. The mouse bug happens in XWayland.**

- `game/cs2.sh` sets `export SDL_VIDEO_DRIVER=x11`.
- On a Wayland desktop, this runs CS2 in XWayland.
- The SDL3 library inside CS2 decodes XInput2 relative valuators wrongly
  there (libsdl-org/SDL#16163). Some starts lose the mouse movement.

**2. `SDL_VIDEO_DRIVER=wayland` does not start on the Snap because the socket
is missing.**

- The Snap sets `DISABLE_WAYLAND=1`.
- The Snap sets `XDG_RUNTIME_DIR=/run/user/$UID/snap.steam`.
- The Snap launcher (`/snap/steam/*/bin/desktop-launch`, near line 275)
  skips the socket link because of `DISABLE_WAYLAND=1`.
- The runtime (`SteamLinuxRuntime_sniper`, pressure-vessel) looks for
  `$XDG_RUNTIME_DIR/$WAYLAND_DISPLAY`. The file does not exist.
- The runtime does not mount the socket into the game container.
- SDL cannot connect. CS2 exits.

**Evidence:**

- I created the socket link. Then I ran `SDL_Init(SDL_INIT_VIDEO)` and
  Vulkan window creation inside the running sniper container. Both
  succeeded. `SDL_GetCurrentVideoDriver()` returned `wayland`.
- After the fix, CS2 runs with no X11 window (no XWayland). The mouse bug
  did not occur again in many starts.
- Extra data point: under the Wayland driver, CS2's video menu offers only
  `Windowed` and `Fullscreen Windowed`. Plain exclusive `Fullscreen` is no
  longer listed (the SDL Wayland backend does not expose one). This matches
  the pre-fix reports of failing fullscreen: those runs were XWayland runs.

**Fix (one command, no root, reversible):** https://github.com/git-on-with-it/fix-cs2-wayland-linux

`fix-cs2-wayland` (bash, no sudo, no Python):

- Creates `$XDG_RUNTIME_DIR/snap.steam/$WAYLAND_DISPLAY -> ../$WAYLAND_DISPLAY`
  and installs a user systemd unit. The symlink is rebuilt at each login.
- Patches `SteamLinuxRuntime_sniper/_v2-entry-point` to create the same
  symlink before pressure-vessel runs.
- Sets `SDL_VIDEO_DRIVER=wayland` in `game/cs2.sh`.
- Saves a `.backup-before-wayland-fix` copy next to every file it changes.
  `--revert` restores all backups.

**Notes on the SDL fix timeline:** steam-runtime#857 closed on 2026-10-23.
Steam Linux Runtime sniper now ships SDL 3.4.18. SDL 3.4.18 contains the
upstream XInput2 fix (libsdl-org/SDL PR #16267). But CS2 uses its own
`libSDL3.so.0` in `game/bin/linuxsteamrt64/`. Thus the runtime fix does not
reach CS2. Reports continue after #857 closed for this reason.

**Suggested Valve-side fixes (one item is enough):**

1. Remove `DISABLE_WAYLAND=1` from the Snap launcher gate, or create the
   compat symlink in all cases.
2. Or: let pressure-vessel also look at
   `<XDG_RUNTIME_DIR>/../$WAYLAND_DISPLAY`. It already accepts such symlinks.

Can other Snap users test and confirm? Run
`fix-cs2-wayland --status`. It shows what it detected. The Snap-side socket
fix is the fastest item Valve can land.

---

## 2) Reddit post

Suggested title: **Fix: CS2 Linux native stuck-mouse bug on Ubuntu (Wayland) — and why the cs2.sh Wayland change did not start**

Body:

Are you on Ubuntu with the Snap Steam? Then you may know both problems:

1. The mouse stays near the center in CS2. Only a few millimeters of
   movement remain. A restart helps sometimes.
2. You set `SDL_VIDEO_DRIVER=wayland` in `game/cs2.sh`, as some threads
   suggest. CS2 then does not start at all. There is no useful error.

The root causes are two:

- `cs2.sh` forces X11. On a Wayland desktop this is XWayland. There, the SDL3
  library in CS2 has a known relative-mouse bug.
- The Snap hides the Wayland socket from the game container. Thus the Wayland
  change fails without a message.

**One-command fix (no sudo, reversible):** https://github.com/git-on-with-it/fix-cs2-wayland-linux

```
sudo apt install git   # if needed
git clone https://github.com/git-on-with-it/fix-cs2-wayland-linux && cd fix-cs2-wayland
./fix-cs2-wayland
```

Then stop Steam and CS2 fully. Start Steam again.

- `fix-cs2-wayland --status` shows what the script detected.
- `fix-cs2-wayland --revert` puts every file back. The script saves a backup
  next to each file it changes.

Tested on Ubuntu 26.10, GNOME Wayland, Steam Snap:

- No stuck-mouse event since the fix.
- CS2 runs as a true Wayland window now.
- The script also works with native and Flatpak Steam installs.
- Bash only. The script changes about 10 lines on your system. All backups
  are saved.

**Original report and video (credit u/Pretty_Library_2373):**
<https://www.reddit.com/r/cs2/comments/1td29d6/mouse_bug_linux_native/>
A demo GIF and the full 84-second clip are in the repo README.
