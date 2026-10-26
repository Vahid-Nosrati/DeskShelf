# Maintainer setup and public releases

## Where to add the missing public details

Open **`app_info.json` in the project root**. The exact keys are:

```json
{
  "author": "Vahid Nosrati",
  "github_profile": "",
  "repository_url": "",
  "public_contact": ""
}
```

- `github_profile`: your complete public profile URL, starting with `https://`.
- `repository_url`: the complete URL of this DeskShelf repository.
- `public_contact`: an optional public email, `mailto:` link or website.

Replace only the text between the quotation marks. Keep commas, braces and quotation
marks intact. Empty fields are intentionally hidden in About. Malformed JSON falls
back to safe defaults rather than preventing launch. Restart/reopen Help after editing.

The build script copies this file beside `dist/DeskShelf/DeskShelf.exe`. That external
copy remains editable without rebuilding. To make the same public details appear in
future builds, update the source copy too. The version is maintained separately as
`VERSION` in `app_meta.py`; author metadata does not change the license file automatically.

## Prepare the repository

Use this `DeskShelf` source directory as the repository root: `README.md`, `main.py`
and `LICENSE` should be at the top level. The README links to Releases descriptively
so the project works without a guessed username or repository URL. Once your repository
exists, you can add direct download links to the README if desired.

Commit source, icons, locales, guide resources, docs and licenses. Do not commit `.venv`,
`build`, `dist`, `data`, `release` or personal backups. `.gitignore` handles the standard
folders but cannot recognize a personal backup saved under an arbitrary filename.

## Build and test on Windows

1. Run `build_windows.bat`; inspect its errors if it fails.
2. Run `.venv\Scripts\python.exe -m unittest discover -p "test_*.py" -v`.
3. Launch the built EXE. Test English, Persian and Arabic in both styles. Check that
   labels and mixed-script entry titles never change alignment when toggling style.
4. Check Help and About, missing/filled metadata, all languages, search and display
   scales. Native Windows dialogs and launcher behavior need an actual Windows check.
5. `BUILD_INFO.json` records the Python, Qt and package versions used in that build.
   Keep it and dependency notices with the portable package. Review notices if the
   dependency set changes; the automated collector is not a license compliance audit.

## Create the two downloads

Run `package_release.bat` from the source directory after a successful build. It creates:

- `release/DeskShelf-v0.4.0-source.zip`
- `release/DeskShelf-v0.4.0-windows-x64-portable.zip`
- `release/SHA256SUMS.txt`

The public portable ZIP always excludes its top-level `data` directory, even if you
used that built copy for private tests. Packaging does not erase your local data.
It retains `_internal`, metadata, guides and license files. Never delete individual
DLLs to reduce size without checking the application and all required plugins.

To package source only: `py -3 scripts\package_release.py --source-only`.
Package scripts use Python's standard library; they do not need Qt to make a ZIP.
They do not upload or publish anything.

## Publish manually on GitHub

Create the repository and push the source. Under Releases create a release matching
the application version, add the two ZIPs and `SHA256SUMS.txt`, summarize the changelog
and publish after your Windows checks. Tell users to extract the ready-made portable
ZIP completely and run `DeskShelf.exe`. GitHub's automatic source archives are source
only and do not contain that EXE. Do not claim Windows 11 or another platform has been
tested unless it actually has. The source is MIT; bundled dependencies keep their
own licenses and notices.

## Updating users safely

Recommend a backup before replacement. Users should close the old app, export/copy
their data, extract a new release separately and restore the backup. Once verified,
they can delete the old app. Their existing language choice is retained; English is
only the default for a new data folder. Do not ship your personal data as defaults.

## v0.4.0 regression checks

Check Ctrl/Shift selection, switching column/type, General protection and both batch
category-removal modes. Verify counts include every item in selected categories,
including filtered-out entries. Check one-step undo restores the batch and order.
Drag rows only onto valid siblings; verify rejected cross-column and cross-category
moves do not import or relocate entries. Reordering must be disabled in search and
with multiple selections. Check order survives closing and reopening.

Before upgrading export a backup. v0.4.0 can read older backups. Earlier versions may
reject data after General has been moved from the first position; use a pre-upgrade
backup when reverting to an older app. Publish v0.4.0 as a new release, keeping v0.3.0.
