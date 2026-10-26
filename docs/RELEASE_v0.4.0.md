# DeskShelf v0.4.0

This release adds persistent ordering and scoped batch removal.

## What's new

- Reorder categories within their own column, using drag-and-drop or Up/Down buttons.
- Reorder entries only inside their own category; invalid destinations are rejected.
- Select multiple rows with Ctrl/Shift. Selection stays in one column and one type
  (categories OR entries). Switching column or type starts a new selection.
- Remove several entries or categories at once, with counts shown before confirmation.
- Choose whether removed categories move their entries to General or remove those
  DeskShelf entries too. Original files and folders are never deleted.
- Undo a whole removal batch in one step, restoring categories, entries and order.
- Updated interface strings and offline guides in all 12 languages.

General can be reordered but remains protected from removal/renaming. Reordering
is disabled while searching or selecting multiple rows. Entry selections can span
several categories within the same column.

## Downloads

- `DeskShelf-v0.4.0-windows-x64-portable.zip`: extract completely and run `DeskShelf.exe`.
- `DeskShelf-v0.4.0-source.zip`: follow README.md and run `build_windows.bat`.
- `SHA256SUMS.txt`: hashes for the two downloads.

## Upgrading from v0.3.0

Export a backup and keep a copy of `data` before upgrading. Extract v0.4.0 into a new
folder and restore your backup. Verify the result before removing the old version.
If reverting to the old app, use the pre-upgrade backup; the old app may reject
saved data after General has been moved from the first position.

Automated regression tests run with Qt offscreen. Windows-native dragging, EXE
launch, file pickers, taskbar behavior and display scaling require Windows checks.
The portable Windows ZIP must be built on Windows before attaching it to the release.
