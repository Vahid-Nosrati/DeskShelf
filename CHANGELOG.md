# Changelog

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
