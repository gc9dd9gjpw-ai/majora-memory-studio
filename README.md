# Majora Memory Studio

**Public Beta 1.2.2** — a Windows editor for *The Legend of Zelda: Majora's Mask* Memories captured with Analogue 3D.

[Download on itch.io](https://alexlazzzz.itch.io/majoras-mask-memory-studio) · [Report a bug](https://github.com/gc9dd9gjpw-ai/majora-memory-studio/issues/new/choose) · [Compatibility](docs/COMPATIBILITY.md)

## Download and use

1. Download `Majora-Memory-Editor-v1.2.2-Windows.zip` from itch.io.
2. Extract it and run `Majora-Memory-Editor-v1.2.2.exe`. Python is not required.
3. Open an Analogue 3D Memory ZIP or PNG and select a capture.
4. Edit the values, review the changes, and export a separate copy.
5. Load the copy on Analogue 3D. Keep the original as your backup.

This edits **Analogue 3D Memories**, not ROMs or arbitrary emulator/flashcart `.sav` files. Loading a Memory and writing a permanent cartridge save are separate operations; use the game's native save procedure when required.

## Features

- Hearts, magic, wallet rupees, bank balance, ammunition and capacity upgrades.
- Inventory, bottle contents and the 24 mask slots.
- Learned songs and the eight-note custom Scarecrow melody.
- Temple items and keys, fairy and Skulltula data, Notebook marks and other documented progress.
- Individual collectible flags and related counters.
- Equipment, character, clock and photo options where implemented.
- Cycle inspection and native cycle operations in recognized states.
- Change review and copy export.
- English, Spanish, French and German interfaces.

**Availability varies by revision and capture state.** This list describes the application as a whole; it does not promise every operation on every revision. Inventory possession does not necessarily complete the associated quest. Advanced fields can create inconsistent progress if combined incorrectly.

## Beta status

**Complete support for all planned USA, PAL and Japanese revisions has not been finished or verified.** See [compatibility](docs/COMPATIBILITY.md). Implementation, software checks and physical console validation are tracked separately.

Version 1.2.2 adds a light interface, visible resource limits, full navigation names across multiple rows, regional panels inside the main window, health controls expressed in hearts, and pending values preserved across language changes. These interface checks add no new console validation.

## Testing and reporting problems

Read the [tester guide](docs/TESTING.md). Include your game region and revision, editor version, exact changes, expected result and actual behavior. Please do not upload ROMs or private Memories to public issues.

## Run from source

Requires Python 3.12 with Tkinter. No third-party packages are needed to run the editor:

```console
python src/Majora-Memory-Editor-v1.2.2.py
```

Keep the entire `src` directory together. Historical module names are runtime dependencies of this beta, not optional downloads.

## Build for Windows

```console
python -m pip install -r requirements-build.txt
python build_windows.py
```

The executable is written to `dist/`. See the tester guide for source checks and optional UI tests with your own captures.

## Research and attribution

Research uses the [Majora's Mask decompilation](https://github.com/zeldaret/mm), revision-specific code inspection and local Analogue 3D reference captures. Source evidence is not physical validation. No ROMs or reference Memories are distributed here.

Independent project; not affiliated with or endorsed by Nintendo or Analogue. Game names and trademarks belong to their owners.

No open-source license has been selected yet. Public source availability alone does not grant a general reuse license.
