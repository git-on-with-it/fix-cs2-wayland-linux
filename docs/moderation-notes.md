# Moderation notes — for keeping the upstream issue useful

This file is for repo maintainers. It holds ready-to-use replies for
[ValveSoftware/csgo-osx-linux#4354](https://github.com/ValveSoftware/csgo-osx-linux/issues/4354)
and the posting rules we follow there.

## Rules

1. No mass comments. One reply per user report. This issue is not a chat.
2. Post new data as replies to the affected user, not as a new top post.
3. Update your own big comments with an edit when new data arrives
   (confirmation table in the main comment). Do not post a second report.
4. No @-mentions of Valve staff. They read the issue.
5. No "any updates?" posts. The issue cites every report; a teammate replies
   once Valve answers.

## Data checklist — ask every reporter for these four items

1. Distro + desktop (example: Arch 2026.10, mangoWM).
2. Steam install type (Ubuntu Snap, native deb/rpm, Flatpak) and Steam version.
3. GPU + driver (example: AMD RADV GFX1150, mesa 25.3).
4. Output of `fix-cs2-wayland --status` after the fix, if they tried it.

Reason: the bug is launch-random. A bare "same here" post does not tell use
whether the user hit XWayland again or hit a new edge case. The four items plus
a confirm after N starts (five or more starts without symptom) form usable
data rows.

## Confirmation table — keep in the main Valve comment (edit, do not repost)

| # | Distro/desktop | Steam type | GPU | Confirmed starts | Result |
|---|----------------|------------|-----|------------------|--------|
| 1 | Ubuntu 26.10, GNOME Wayland | Snap 1.0.0.87 | AMD RADV GFX1150 | 20+ | fixed |

Add a row per report. In a row, an opening report counts like this:
`works` = user applied the fix and saw no stuck mouse in 5+ starts.
`n/a` = user reports before the fix ran (no row yet).

## Template: reply to a fresh "same here" report

Keep it to three sentences (paste in this order):

```
The XWayland valuator bug is random per launch, so your report is probably a
second instance of the same issue — see the root cause in the main comment.
If you are on the Ubuntu Steam Snap, the socket fix + real-Wayland switch is
tested and reversible: https://github.com/git-on-with-it/fix-cs2-wayland-linux
To make your report count for the fix, add: distro/desktop, Steam install
type, GPU, and the output of `fix-cs2-wayland --status` after the fix, plus
the start count that stayed clean.
```

Notes:

- Do not paste the full table or diagnosis again. Point at the main comment.
- If the reporter is not on a Snap, the reply needs the native or Flatpak
  note: the script detects those Steam types and applies the same fix.

## Template: reply to the "empty SDL_VIDEO_DRIVER works for me" workaround

This workaround returns when someone posts it. The reply explains why not:

```
Empty SDL_VIDEO_DRIVER still runs the game on X11/XWayland (SDL silently falls
back to X11). That is the path with the valuator bug, and it is random per
launch — so the bug can return at any start; the fix was also to run on the
Wayland path (no XWayland): https://github.com/git-on-with-it/fix-cs2-wayland-linux
```

A long-form version of this reply is already posted (comment 6556105718).

## When the issue closes

Valve fixes this in one of these ways (the main comment explains both):

1. Valve updates `game/bin/linuxsteamrt64/libSDL3.so.0` in CS2 to a build
   that contains the SDL 3.4.18 valuator fix, or
2. Valve removes the `SDL_VIDEO_DRIVER=x11` default in `game/cs2.sh`, and
3. (Snap only) the Snap launcher stops eating the Wayland socket.

When (1) or (2) lands, `fix-cs2-wayland --status` detects the new bundled
SDL version: it prints "includes the upstream mouse fix; run --revert".
That is the signal to post a short "fixed-in-CS2, script marked deprecated"
comment and tag v2.0.0 of this repo with the check removed.
