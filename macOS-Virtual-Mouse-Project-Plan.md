# Project Spec: macOS Webcam Virtual Mouse

> This document is written to be handed directly to a coding agent (e.g. Claude Code) as a build brief. It defines the goal, constraints, architecture, and phased tasks unambiguously so the agent can execute without needing to re-derive scope.

## 1. Objective

Build a standalone macOS application that uses the built-in or external webcam to track hand movements and gestures in real time, and translates them into **system-wide (OS-level) mouse control** — cursor movement, left click, right click, drag, scroll, and zoom — functioning across any application, not just inside a browser.

This is explicitly **not** a Chrome extension. Chrome extensions run in a sandbox and cannot move the OS-level cursor outside the browser tab. The deliverable is a native Python application (packageable into a `.app` later).

## 2. Hardware & OS Compatibility Requirement

The app must run on a **wide range of Mac hardware**, not just Apple Silicon M4. Concretely:

| Requirement | Detail |
|---|---|
| Chip support | Both Apple Silicon (M1/M2/M3/M4 series) and Intel-based Macs (x86_64) |
| OS version | macOS 12 (Monterey) and above, to cover most machines still in active use |
| Camera | Any camera exposed via AVFoundation — built-in FaceTime camera or external USB webcam |
| Performance scaling | On lower-power machines (older Intel Macs, base M1), the app should auto-reduce processing load (see Section 6, adaptive performance) rather than assume high-end GPU/Neural Engine throughput |
| Python architecture | Must install cleanly under both `arm64` and `x86_64` Python environments — flag any dependency (e.g. certain MediaPipe or OpenCV wheel versions) that lacks a universal or per-arch build, and document the correct install path for each |

**Agent instruction:** when writing setup/install scripts, do not hardcode assumptions about Apple Silicon-only paths (e.g. Homebrew's `/opt/homebrew` prefix). Detect architecture at setup time (`uname -m`) and branch install paths accordingly (`/opt/homebrew` for arm64, `/usr/local` for Intel Homebrew installs).

## 3. Prior Art Research (for reference / cloning as a base)

We researched existing open-source hand-gesture virtual mouse projects. None target macOS specifically or support a hardware range out of the box — all require adaptation. Comparison:

| Repo | Stack | Strengths | Gaps to fill |
|---|---|---|---|
| **[hannishreddi/virtual_mouse](https://github.com/hannishreddi/virtual_mouse)** — recommended base | OpenCV + MediaPipe, modular (`main.py`, `hand_tracker.py`, `mouse_controller.py`, `utils.py`) | Clean separation of concerns, OS-agnostic, easy to extend | Zoom gesture, drag, debounce logic, macOS permission handling, packaging, Intel/Apple Silicon compatibility |
| [Viral-Doshi/Gesture-Controlled-Virtual-Mouse](https://github.com/Viral-Doshi/Gesture-Controlled-Virtual-Mouse) | MediaPipe + voice commands (Windows-targeted) | Good gesture mapping ideas (pinch-drag → scroll/volume/brightness) | Windows-only, unnecessary voice-assistant baggage |
| [maanjk/hand-gesture-virtual-mouse](https://github.com/maanjk/hand-gesture-virtual-mouse) | OpenCV + MediaPipe (Windows explicit) | Simple, CPU-only, lightweight | Needs full porting to macOS |
| [whitehatboy005/Virtual-Mouse](https://github.com/whitehatboy005/Virtual-Mouse) | OpenCV + MediaPipe + PyAutoGUI | Drag + scroll gestures already implemented | No macOS-specific handling |
| [GuhanAein/VirtualMouse](https://github.com/GuhanAein/VirtualMouse) | MediaPipe, thumb-index distance = click | Simple click-threshold reference implementation | Very barebones, missing drag/scroll/zoom |

**Decision:** clone `hannishreddi/virtual_mouse` as the base and upgrade it.

```bash
git clone https://github.com/hannishreddi/virtual_mouse.git
cd virtual_mouse
```

## 4. Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌───────────────────┐     ┌──────────────────┐
│   Webcam Feed    │ --> │  Hand Tracking    │ --> │  Gesture Logic     │ --> │  OS Mouse Control │
│  (OpenCV/         │     │  (MediaPipe Hands)│     │  (state machine +  │     │  (pynput +        │
│   AVFoundation)   │     │  21 landmarks/hand│     │   debounce)        │     │   Accessibility)  │
└─────────────────┘     └──────────────────┘     └───────────────────┘     └──────────────────┘
```

## 5. Tech Stack

| Component | Library | Cross-hardware note |
|---|---|---|
| Camera capture | `opencv-python` | Uses AVFoundation backend on macOS; works on Intel and Apple Silicon identically |
| Hand tracking | `mediapipe` | CPU-based inference by default — runs on both Intel and Apple Silicon; Apple Silicon gets a speed bonus but is not required |
| Mouse control | `pynput` (preferred over `pyautogui` for lower-level, smoother control) | Requires macOS Accessibility permission on any chip |
| Screen coordinate mapping | `pyobjc` (`Quartz`) — optional, for multi-monitor precision | Architecture-independent |
| Packaging (Phase 6) | `py2app` or `PyInstaller` | **Must build separate artifacts for arm64 and x86_64**, or a universal2 build if feasible — a `.app` built on an M-series Mac will not run on an Intel Mac and vice versa without this |

### Install commands (architecture-aware)
```bash
python3 -m venv venv
source venv/bin/activate
pip install opencv-python mediapipe pynput pyobjc
```

## 6. Adaptive Performance (for lower-end hardware)

Since target range includes older/weaker Macs, the agent should implement:
- Configurable camera capture resolution (default lower on Intel Macs, e.g. 640×480, vs higher on Apple Silicon, e.g. 1280×720)
- Frame-skipping option: process every Nth frame for hand tracking if FPS drops below a threshold (e.g. 15fps)
- A runtime check (simple timing benchmark on startup) to auto-select a "performance" vs "quality" mode

## 7. macOS Permissions (critical — required on every Mac regardless of chip)

1. **Camera access** — first run triggers a system prompt; must be allowed.
2. **Accessibility access** (mandatory for OS-level mouse control):
   `System Settings → Privacy & Security → Accessibility → (+) → add the app/terminal used to run the script`.
   Without this, `pynput` fails **silently** — no error is thrown, the cursor simply does not move. This is the most common debugging trap and applies identically on Intel and Apple Silicon.
3. When packaged as a `.app` (Phase 6), the bundled app itself must be re-added to the Accessibility list — permission does not carry over from the Terminal/IDE used during development.

## 8. Gesture Mapping (v1 scope)

| Gesture | Landmark logic | Action |
|---|---|---|
| Index finger extended, hand moves | Track index fingertip (landmark #8) | Cursor move (camera frame → screen coordinate mapping) |
| Thumb tip + index tip close (short pinch) | Distance(#4, #8) < threshold, held <200ms | Left click |
| Pinch held + move | Same pinch, sustained >200ms while moving | Drag |
| Thumb tip + middle tip pinch | Distance(#4, #12) < threshold | Right click |
| Two hands, distance between them changes | Track centroid distance between both hands | Zoom in/out (simulate `Cmd + '+'/'-'` or `Cmd + scroll`) |
| Open palm, held still | All 5 fingers extended, no movement | Pause tracking (safety, prevents accidental clicks) |
| Index + middle fingers together, vertical move | Distance(#8, #12) small + vertical movement | Scroll |

### Debounce logic (mandatory)
Raw pinch detection flickers between pinched/unpinched across frames due to landmark noise. Require the pinch state to remain stable for ~150–200ms before registering an action; otherwise ignore.

## 9. Phased Build Roadmap

- [ ] **Phase 0 — Setup & compatibility check**: Clone base repo, detect chip architecture, set up venv, verify webcam access via AVFoundation, verify MediaPipe landmark visualization overlay works
- [ ] **Phase 1 — Cursor movement**: Index fingertip → screen coordinate mapping with smoothing (exponential moving average) to remove jitter
- [ ] **Phase 2 — Click gestures**: Pinch-to-click with debounce logic
- [ ] **Phase 3 — Drag & right-click**: Sustained pinch = drag; thumb+middle pinch = right-click
- [ ] **Phase 4 — Scroll & Zoom**: Two-finger scroll gesture; two-hand distance = zoom
- [ ] **Phase 5 — Safety & UX polish**: Open-palm pause gesture, on-screen gesture guide overlay, calibration step mapping camera field-of-view to actual screen bounds
- [ ] **Phase 6 — Packaging**: Build `.app` via `py2app`/`PyInstaller` for **both** arm64 and x86_64 (or universal2 if the toolchain supports it); add a menu-bar toggle using `rumps`
- [ ] **Phase 7 (optional)**: Browser-scoped mode via a Chrome extension + Native Messaging host, for users who only want in-tab control without full OS access

## 10. Suggested File Structure (post-upgrade)

```
virtual_mouse/
├── main.py                # Entry point, camera loop, architecture detection
├── hand_tracker.py        # MediaPipe wrapper, returns landmarks
├── gesture_recognizer.py  # NEW — gesture state machine + debounce
├── mouse_controller.py    # pynput-based OS mouse actions
├── coordinate_mapper.py   # NEW — camera frame → screen coords, smoothing
├── config.py               # NEW — thresholds, sensitivity, resolution, performance mode
├── utils.py
├── requirements.txt
└── README.md
```

## 11. Known Challenges

1. **Jittery cursor** — raw landmark coordinates are noisy frame-to-frame. Fix: exponential moving average smoothing.
2. **Low-light performance** — MediaPipe hand detection degrades in poor lighting; tune minimum detection confidence and consider exposure adjustment.
3. **False clicks** — unreliable without debounce (Section 8).
4. **Screen-edge mapping** — camera field of view doesn't naturally match screen aspect ratio; needs a calibration step (map hand movement at frame corners to screen corners).
5. **Silent Accessibility permission failures** — most common trap across all hardware (Section 7).
6. **Cross-architecture packaging** — a `.app` built on one chip architecture will not run on the other without explicit universal2 build or separate builds per architecture (Section 5, 9).

## 12. Acceptance Criteria (for agent to self-check against)

- [ ] App runs on both an Intel Mac and an Apple Silicon Mac without code changes (only environment/install steps may differ)
- [ ] Cursor movement is smooth (no visible jitter) at normal hand movement speed
- [ ] Click/drag/right-click/scroll/zoom gestures each work reliably with <5% false-trigger rate in normal lighting
- [ ] App clearly instructs the user to grant Camera + Accessibility permissions if missing, rather than failing silently
- [ ] Performance mode auto-adjusts on lower-spec hardware to maintain usable frame rate (Section 6)
