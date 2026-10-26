# v0.4.0 validation

Result: **52 automated tests passed** using Qt offscreen on Linux.

Coverage includes:

- Existing saves, backup compatibility, Unicode, invalid-data rejection and appearance.
- Category ordering, including General, stays within its column and survives reload.
- Entry ordering stays in its category and leaves unrelated entries untouched.
- Real Qt Ctrl/Shift selection, type switching, column switching and General protection.
- Up/Down boundaries, multiple-selection and search guards, and drop indicator behavior.
- Internal drop handlers accept valid siblings and reject foreign categories/columns,
  malformed payloads and filtered reorder requests. External URL import is retained.
- Both category-removal modes, unique counts, cancellation, and category/item batches.
- One-step undo restores the full original batch/order, keeps later additions and edits,
  and respects later manual recategorization. Twenty-batch history limit is exercised.
- Original target files remain untouched. Right-click preserves batches. Enter without
  focus on the removal button cancels the confirmation dialog.
- All 12 locale catalogs and guides remain complete; confirmation placeholders match.
- Public archive rules exclude saved personal data and development directories.

Persian selection and removal-dialog previews were inspected. The public metadata
from the supplied project is retained. The Windows build script and release names
use v0.4.0. No Windows EXE was produced in this Linux environment.

Before public release on Windows, verify native drag gestures and edge auto-scroll,
EXE startup, file picker/launcher integration and display scaling. Automated drop
handler tests do not substitute for an operating-system drag-and-drop check.

Run the suite from the source directory:

    .venv\Scripts\python.exe -m unittest discover -p "test_*.py" -v

## Same-version visual corrections

Seven additional regression tests check inline/wrapped column headers, window and
splitter resizing, long translated titles and font metrics, RTL/LTR geometry for
all 12 locales, arrowhead/shaft rendering, category-sensitive empty hints and search
no-results behavior. Version remains 0.4.0. Preview images use fictional entries.
