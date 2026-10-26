# Contributing to DeskShelf

Bug reports, usability feedback, code changes and translation corrections are welcome.
Use Issues to discuss larger changes before opening a pull request.

## Development

Use a supported Python version and install `requirements.txt` in a virtual environment.
Run `python main.py` for development and `python -m unittest discover -p "test_*.py" -v`
for tests. Public executables are built on Windows with `build_windows.bat`.

Keep changes focused. Include the reason for a change and how it was checked. A UI
change should include screenshots with fictional, non-private entries. Do not commit
personal `data`, backups, `.venv`, `build`, `dist`, downloaded wheels or generated releases.

## Translations

- UI strings: `locales/<code>.json`; all keys must match `locales/en.json`.
- Offline guide: `help/<code>.json`; all 12 section identifiers must match English.
- Preserve keyboard shortcuts, protocol examples and paths such as `data/data.json`.
- Translate meaning naturally; do not translate user-supplied titles or notes.
- Avoid adding personal links or translator signatures to the visible interface.
- Run tests and check the language in both Flat and Raised modes, including Settings
  and Help. Check long text, mixed-script titles, focus, scrolling and display scaling.
- New locales require `LANGUAGES` registration and validation updates in `core.py`.

The initial translations are open for review by speakers of each language. Please
report awkward wording or terminology with the locale, key/section and a suggestion.

## Credits and licensing

By submitting a contribution, you agree it may be distributed under the project MIT
license. Keep existing copyright and dependency notices. You may ask to be listed in
`CONTRIBUTORS` under your chosen public name or handle; listing is voluntary. Never
add someone else's personal contact details without their agreement.
