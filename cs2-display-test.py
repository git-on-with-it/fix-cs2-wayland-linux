#!/usr/bin/env python3
"""Interactive, cross-platform CS2 VSync/VRR test assistant.

The tool does not change system, driver, Steam, or CS2 settings. It guides
the user through repeatable tests and writes a Markdown report.
"""

from __future__ import annotations

import datetime as dt
import os
import platform
import shutil
import subprocess
from pathlib import Path


TESTS = (
    ("1", "Off", "Off"),
    ("2", "On", "Off"),
    ("3", "Off", "On"),
    ("4", "On", "On"),
)


def ask(question: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    answer = input(f"{question}{suffix}: ").strip()
    return answer or default


def command_version(command: str) -> str | None:
    path = shutil.which(command)
    if not path:
        return None
    try:
        result = subprocess.run(
            [command, "--version"],
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return path
    line = (result.stdout or result.stderr).splitlines()
    return f"{path} ({line[0]})" if line else path


def detect() -> dict[str, str]:
    system = platform.system()
    session = os.environ.get("XDG_SESSION_TYPE", "") if system == "Linux" else ""
    desktop = os.environ.get("XDG_CURRENT_DESKTOP", "") or os.environ.get(
        "DESKTOP_SESSION", ""
    )
    tools = []
    for name in ("mangohud", "vulkaninfo", "nvidia-smi", "glxinfo"):
        version = command_version(name)
        if version:
            tools.append(version)
    return {
        "system": system,
        "release": platform.release(),
        "machine": platform.machine(),
        "desktop": desktop or "unknown",
        "session": session or "not applicable",
        "tools": "\n".join(f"- `{tool}`" for tool in tools) or "- None detected",
    }


def launch_hint(info: dict[str, str]) -> str:
    if "mangohud" in info["tools"].lower():
        return "`mangohud %command%` (try `mangohud --dlsym %command%` if needed)"
    if info["system"] == "Windows":
        return "Use PresentMon, CapFrameX, or the Xbox Game Bar performance overlay."
    if info["system"] == "Darwin":
        return "Use an available macOS frame-time overlay or record FPS manually."
    return "Install MangoHud, then use `mangohud %command%` in Steam launch options."


def setting_hint(system: str) -> str:
    if system == "Linux":
        return (
            "Set VSync in CS2. Set VRR in your desktop display settings or "
            "monitor control panel."
        )
    if system == "Windows":
        return (
            "Set VSync in CS2. Set VRR in Windows Advanced display settings, "
            "the GPU control panel, or the monitor menu."
        )
    if system == "Darwin":
        return (
            "Set VSync in CS2. macOS may manage variable refresh automatically "
            "on supported ProMotion displays."
        )
    return "Set VSync in CS2 and VRR in the operating-system or monitor settings."


def collect_test(number: str, vsync: str, vrr: str) -> dict[str, str]:
    print(f"\nTest {number}: VSync {vsync} / VRR {vrr}")
    input("Set these values, launch CS2, and play the same scene. Press Enter when ready.")
    return {
        "vsync": vsync,
        "vrr": vrr,
        "fps": ask("Observed FPS", "unknown"),
        "frametime": ask("Observed frametime or MangoHud graph", "unknown"),
        "spikes": ask("Frame-time spikes? (yes/no/unknown)", "unknown"),
        "latency": ask("Input feel (low/medium/high/unknown)", "unknown"),
        "tearing": ask("Visible tearing? (yes/no/unknown)", "unknown"),
        "notes": ask("Notes", ""),
    }


def markdown(info: dict[str, str], hardware: dict[str, str], tests: list[dict[str, str]]) -> str:
    now = dt.datetime.now().astimezone().isoformat(timespec="seconds")
    lines = [
        "# CS2 VSync/VRR test report",
        "",
        f"Generated: `{now}`",
        "",
        "## System",
        "",
        f"- OS: `{info['system']} {info['release']}`",
        f"- Architecture: `{info['machine']}`",
        f"- Desktop: `{info['desktop']}`",
        f"- Session: `{info['session']}`",
        f"- GPU: `{hardware['gpu']}`",
        f"- GPU driver: `{hardware['driver']}`",
        f"- Monitor: `{hardware['monitor']}`",
        f"- Refresh rate: `{hardware['refresh']}`",
        f"- Steam type: `{hardware['steam']}`",
        "",
        "## Detected tools",
        "",
        info["tools"],
        "",
        "## Results",
        "",
        "| Test | VSync | VRR | FPS | Frametime | Spikes | Input feel | Tearing |",
        "|---:|---|---|---|---|---|---|---|",
    ]
    for index, test in enumerate(tests, 1):
        values = [
            str(index),
            test["vsync"],
            test["vrr"],
            test["fps"],
            test["frametime"],
            test["spikes"],
            test["latency"],
            test["tearing"],
        ]
        lines.append("| " + " | ".join(value.replace("|", "\\|") for value in values) + " |")
    lines += [
        "",
        "## Notes",
        "",
        *[f"### Test {i}\n\n{test['notes'] or 'No notes.'}" for i, test in enumerate(tests, 1)],
        "",
        "## Reproduction",
        "",
        "- Keep the same map, resolution, display mode, and FPS limit for every test.",
        "- This report measures frame pacing and perceived input feel.",
        "- It does not measure end-to-end mouse-to-pixel latency.",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    print("CS2 display test assistant")
    print("This tool changes nothing. It only guides tests and writes a report.\n")
    info = detect()
    print(f"Detected: {info['system']} / {info['desktop']} / {info['session']}")
    print(f"Overlay suggestion: {launch_hint(info)}")
    print(f"Setting hint: {setting_hint(info['system'])}")
    print("\nUse the same CS2 scene for every test. Do not change the FPS limit between tests.")

    hardware = {
        "gpu": ask("GPU", "unknown"),
        "driver": ask("GPU driver", "unknown"),
        "monitor": ask("Monitor model", "unknown"),
        "refresh": ask("Monitor refresh rate", "unknown"),
        "steam": ask("Steam type (Snap/native/Flatpak/Windows/macOS)", "unknown"),
    }
    tests = [collect_test(number, vsync, vrr) for number, vsync, vrr in TESTS]
    default = Path.cwd() / f"cs2-display-test-{dt.date.today().isoformat()}.md"
    output = Path(ask("Report path", str(default))).expanduser()
    output.write_text(markdown(info, hardware, tests), encoding="utf-8")
    print(f"\nReport written to: {output}")


if __name__ == "__main__":
    main()
