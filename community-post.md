# Community Post — ready to publish

Below are two ready-to-paste announcements. Pick the matching target.
Replace `<REPO_URL>` with your published GitHub repository URL once pushed.

---

## 1) Comment for the Valve issue thread
Target: https://github.com/ValveSoftware/csgo-osx-linux/issues/4354

**Subject: Root cause found for the "stuck mouse" AND the "SDL_VIDEO_DRIVER=wayland won't launch" reports on Ubuntu's Steam Snap — script + diagnosis**

Short version: on Ubuntu's Steam **Snap**, setting `SDL_VIDEO_DRIVER=wayland` does fail to launch CS2 — but it's not CS2 or SDL to blame; it's the Snap's isolated runtime dir, and it's fixable in one command.

**Diagnosis (verified on Ubuntu 26.10, GNOME Wayland, Steam Snap 1.0.0.87:**)

1. The mouse-stuck bug occurs when CS2 runs through **XWayland**. The stock `game/cs2.sh` forces `export SDL_VIDEO_DRIVER=x11`, which on Wayland desktops means XWayland, where CS2's bundled SDL3 mis-decodes XInput2 relative valuators (see libsdl-org/SDL#16163) — some launches lose all horizontal/vertical movement.
2. Switching to `SDL_VIDEO_DRIVER=wayland` historically "doesn't launch" on the Snap because the Snap sets `DISABLE_WAYLAND=1` and repoints `XDG_RUNTIME_DIR` to `/run/user/$UID/snap.steam` **without** linking the real Wayland socket there (`/snap/steam/279/bin/desktop-launch`, ~line 275, skips that block because of `DISABLE_WAYLAND=1`). When `SteamLinuxRuntime_sniper` (pressure-vessel) builds CS2's container, `$XDG_RUNTIME_DIR/$WAYLAND_DISPLAY` doesn't exist, so the socket is never mounted — SDL can't connect and the game exits.

**Evidence:**
- Inside the running sniper container, `SDL_Init(SDL_INIT_VIDEO)` + Vulkan window creation succeed and `SDL_GetCurrentVideoDriver()` returns `wayland` once the socket link exists.
- After the fix, CS2 runs with **no X11 window at all** (no XWayland), and the stuck-mouse symptom is gone across many launches.

**Fix (one command, user-level, idempotent, reversible):** <REPO_URL>

`fix-cs2-wayland` (bash, no sudo/python):
- links `$XDG_RUNTIME_DIR/snap.steam/$WAYLAND_DISPLAY -> ../$WAYLAND_DISPLAY` and installs a tiny user systemd oneshot to keep it across logins,
- patches `SteamLinuxRuntime_sniper/_v2-entry-point` to do the same before pressure-vessel runs,
- sets `SDL_VIDEO_DRIVER=wayland` in `game/cs2.sh`,
- writes a `.backup-before-wayland-fix` next to every file it touches; `--revert` restores everything.

**Suggested Valve-side fixes (either one):**
- Drop `DISABLE_WAYLAND=1` from the snap's `desktop-launch` gate, or create the compat symlink regardless of that flag;
- and/or have pressure-vessel fall back to probing `<XDG_RUNTIME_DIR>/../$WAYLAND_DISPLAY` (it already accepts such symlinks fine).

If others on the Snap can test and confirm (`fix-cs2-wayland --status` shows what it detected), that would strengthen the case. The upstream SDL fix exists already; CS2 just ships its own copy, so the snap-side socket fix is the piece Valve can land fastest.

---

## 2) Reddit post
Suggested title: **Fix: CS2 Linux native stuck-mouse bug on Ubuntu (Wayland) — and why switching cs2.sh to Wayland wouldn't launch**

Body:

If you're on Ubuntu with the **Snap Steam**, you've probably seen both of these:
1. In-game mouse randomly gets stuck near the center (only a few mm of movement) → restarting CS2 until it "gets lucky",
2. Editing `game/cs2.sh` to `SDL_VIDEO_DRIVER=wayland` as people suggest → game refuses to launch at all.

Both have one common root: CS2 forced to X11 = XWayland = a known SDL3 relative-mouse bug, and the Snap hides your Wayland socket from the game's container so the Wayland switch fails with no useful error.

**One-command fix (no sudo, fully reversible):** <REPO_URL>

```
sudo apt install git   # if needed
git clone <REPO_URL> && cd fix-cs2-wayland
./fix-cs2-wayland
```

Then fully restart Steam + CS2. `--status` shows what it detected, `--revert` puts everything back exactly as before (it saves per-file backups).

Tested on Ubuntu 26.10 GNOME Wayland + Steam Snap: 0 stuck-mouse launches since, and the game now runs as a true Wayland window. Works also on native/Flatpak Steam installs. Bash-only, ~10 lines changed on your system, everything backed up.

**Original report & video (credit u/Pretty_Library_2373):** <https://www.reddit.com/r/cs2/comments/1td29d6/mouse_bug_linux_native/> — a 30-second demo GIF and the full 84-second clip are embedded in the repo README, so newcomers can recognize their exact symptom at a glance and land directly on the fix.
