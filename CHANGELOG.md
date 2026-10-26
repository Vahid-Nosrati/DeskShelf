# Changelog

## 0.4.0

### Visual corrections (same version)

- Column controls remain beside the title whenever measured text and buttons fit.
  They wrap only when needed and return inline after resizing or changing language.
- Up/Down icons use filled arrowheads joined to short shafts.
- The empty-column hint is hidden whenever a custom category exists and returns when
  only an empty General category remains. Search no-results hints are unchanged.
- Seven added visual/layout regression checks cover all twelve interface languages.


- Scoped drag-and-drop and Up/Down controls for persistent category and item ordering.
- Categories stay in their column; items stay in their own category. General is movable.
- Single-column, same-type Ctrl/Shift selection; changing type or column clears the old selection.
- Batch item/category removal with counts, safe cancellation and two category-removal modes.
- One-step batch undo restores entries, categories, collapsed state and original ordering.
- Reordering is disabled during search or multiselection. Right-click preserves selected batches.
- New behavior translated in all 12 catalogs and offline guides; existing public metadata retained.
- All 52 automated tests pass, covering data persistence, invalid destinations, selection, deletion and undo.
- See docs/VALIDATION_v0.4.0.md for verification scope and Windows checks.


## 0.3.0

- English default for a new installation; retain existing language preferences.
- Twelve complete UI catalogs and searchable offline guides: English, Persian,
  Arabic, Spanish, French, German, Brazilian Portuguese, Russian, Simplified Chinese,
  Japanese, Turkish and Hindi.
- Help button and F1 shortcut, with an About tab and editable optional public metadata.
- Raised mode uses directly painted card shadows, gradients and panel depth instead
  of a graphics effect on whole widgets. RTL alignment is set explicitly and independently
  of style; path fallbacks remain left to right.
- MIT license, Copyright (c) 2026 Vahid Nosrati; third-party notices and license texts.
- English/Persian README, contribution guidelines, issue templates, optional contributor
  list and one-command public packaging with private-data exclusions and SHA-256 hashes.

### Validation scope

Automated tests run with Qt offscreen, including all locale/guide completeness checks,
style rendering differences, RTL invariance, metadata handling, backup compatibility,
search, keyboard operation and archive privacy. GUI previews are inspected separately.
No Windows EXE is built in the Linux development environment. Windows native dialogs,
EXE launch/shortcuts, taskbar behavior and display scaling require Windows verification.
Translations are initial translations and welcome review by fluent speakers.

## 0.2.0

Card layout, custom icon, appearance controls, pastel palettes and portable build script.
