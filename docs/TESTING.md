# Testing and bug reports

## Automated checks

```console
python tests/test_source.py
```

This compiles shipped modules, parses JSON and imports the entry point without opening a window. It does not verify game semantics or console behavior.

The optional UI suite needs a desktop session, Tkinter and four local Memory archives in this order:

```console
python tests/test_ui.py USA.zip PAL11.zip PAL10.zip JP11.zip
```

The suite selects the first PNG in each archive. Use compatible normal-gameplay captures. Dialogs, transitions or incompatible edit states may be rejected by the backend; a rejection is not a passing test. The suite checks language preservation, output bytes, window/navigation behavior and input hashes. It writes `test-results.json` without modifying input archives.

## Organized console test round

Use copies of your own captures and test only features available for that revision.

| Group | Checks |
| --- | --- |
| Resources | Set distinct amounts, load the copy, check values, then change areas |
| Inventory and equipment | Check selected items, bottle contents and masks; equip/use where allowed |
| Songs | Check learned songs, define a valid eight-note Scarecrow melody, test playback and invocation |
| Collectibles | Check counters and pickup flags; ensure marked hearts do not add excess capacity |
| Permanent data | Check bank, name and selected fields before/after native Song of Time saving |
| Temporary data | Compare ammunition, trade items, fairies, keys and events before/after reset |
| Cycle | Test eligible morning/night advance; native reset only from the recognized confirmation dialog |
| Advanced edits | Test equipment, character, clock and photo changes so a failure can be attributed |
| Persistence | Change areas, save natively, restart; compare file selection and in-game state |

Flashcart `.sav` testing is not a substitute for native cartridge persistence testing. Record your storage device.

## Report contents

- Editor and Windows versions.
- Game region, revision and cartridge ID.
- Analogue 3D firmware if known, and original cartridge or flashcart.
- Capture area, day/time and visible dialog state.
- Exact edits, expected behavior and actual behavior.
- Whether loading, changing areas, saving and restarting worked.
- Screenshots with personal paths removed if helpful.

Do not publish ROMs, private Memories or personal information. Arrange private sharing with the maintainer if a reference capture is essential.
