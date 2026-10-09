# Compatibility and validation

This describes the published **1.2.2 beta**, not the intended final feature set.

| Revision | Implementation in this beta | Evidence and remaining work |
| --- | --- | --- |
| USA 1.0 | Main editor | Reference Memories, UI tests and selected prior console checks; complete semantic validation pending |
| PAL 1.1 | Main editor | Reference Memories, UI tests and selected prior console checks; complete semantic validation pending |
| PAL 1.0 | Regional panel in the main window | Real captures, UI tests and selected manual observations; parity pending, native reset button disabled in this release |
| Japan 1.1 / Rev A | Regional panel in the main window | Reference RDRAM, UI tests and selected manual loading/persistence observations; parity and runtime checks pending |
| Japan 1.0 | Revision research and detection evidence | ROM inspection; full editor integration and reference-Memory validation pending; not a complete editing target |
| PAL Debug | Research material | Not advertised as a supported target of this retail beta |

An available revision profile is not a claim that every editing path is complete. Unknown cartridge IDs and ambiguous structures must not be treated as supported simply because a file opens.

## Evidence levels

- **Implemented:** an editing path exists in the application.
- **Verified by software:** a specified fixture and operation passed a named test.
- **Verified on Analogue 3D:** a specific exported change was loaded and its behavior checked on console.
- **Pending:** implementation, fixtures or semantic/console checks are missing.

A successful load does not validate an entire feature group. A manual Song of Time test does not automatically validate an editor-generated native reset request.

## 1.2.2 interface regression results

USA 1.0, PAL 1.1, PAL 1.0 and Japan 1.1 inputs passed checks for one main window, four languages preserving edited output bytes, complete navigation entries and unchanged input hashes. Capacity-label checks and regional health-input checks also passed.

The Japanese UI fixture was a **reconstructed container using retained reference RDRAM**, not an untouched original Memory. It does not establish physical compatibility of that container.

Packaged-executable UI smoke tests passed for USA, PAL 1.0 and Japan 1.1. They add no new physical console validation.

## Data distinctions

- Wallet rupees and bank rupees are separate fields.
- Temporary cycle data and permanent progress are separate structures.
- Inventory possession does not necessarily complete acquisition quests.
- Counters and individual pickup flags are not interchangeable.
- Notebook marks do not grant rewards or complete quests.
- Imported photo pixels do not establish a valid quest subject.
- Advancing the final night is not equivalent to a Song of Time reset.
- Persistent cartridge storage and the in-memory save context are different.
