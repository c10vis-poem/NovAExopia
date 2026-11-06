---
name: android-adb
description: "Control the phone via claw.device: Termux:API and adb (tap, shell, install, screenshot). Use when touching the phone."
---
`claw.device action=<termux name>`: battery, wifi, location, clipboard-get/set, toast, tts, vibrate, notify (args [title, text]), open-url. Needs Termux:API app + `pkg install termux-api`.

`action=adb args=[...]` passes argv to adb: `["shell","input","tap","x","y"]`, `["exec-out","screencap","-p"]`, `["install","-r","a.apk"]`, `["forward","tcp:9222","localabstract:chrome_devtools_remote"]`. `adb-devices` lists devices.

Built-in client, no adb binary, Shizuku or Tasker: `adb-connect` (port from the Wireless debugging screen), `adb-shell` (command; returns stdout, stderr, exit), `adb-tap` (x, y), `adb-install` (path), `adb-status`, `adb-disconnect`. Prefer these; use `action=adb` for what they lack, such as `forward`.

Pairing (once, by the operator): Wireless debugging on, `adb pair 127.0.0.1:<pair-port> <code>`. That trusts `~/.android/adbkey`, which the built-in client reuses. No device is paired on this phone as of 2026-11-05, so the built-in client is proven only against a fake adbd.

`CHOICE:` in a result means the operator must act or pick (allow the prompt, turn on debugging, which device).

ADB loopback (AEthX-AEsc/adb_loopback/POINTER.md is only a pointer; plain TCP/TLS to adbd is implemented, the AF_UNIX + SCM_RIGHTS handshake is not). Source donors not on this phone: Goodbye-Termux-ADB, claude-android-skill.
