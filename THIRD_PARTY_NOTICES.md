# Third-party software

DeskShelf application source and original artwork are licensed under MIT,
Copyright (c) 2026 Vahid Nosrati. This license does not relicense dependencies.

| Component | Use | Upstream license / source |
| --- | --- | --- |
| Python | Runtime and standard library | PSF License and included notices: https://www.python.org/downloads/source/ |
| PySide6 and Shiboken6 | Qt Python bindings | LGPLv3; https://code.qt.io/pyside/pyside-setup.git/ |
| Qt Core, Gui, Widgets and associated plugins | Desktop UI | LGPLv3 where applicable, plus component notices: https://code.qt.io/qt/ |
| PyInstaller | Build tool and bootloader | GPL with bootloader exception; https://pyinstaller.org/en/stable/license.html |

PyInstaller's bootloader exception allows bundled applications to use their own
licenses; it does not remove other bundled components' license obligations.
No changes to the upstream Qt, PySide6 or Shiboken libraries are made here.

The onedir package retains shared libraries in _internal. Recipients may replace
compatible shared libraries with their modified builds and may debug modifications
as permitted by the applicable library license. Keep those libraries, this notice,
and their license texts when redistributing. Complete corresponding source for
the library versions used is available from the upstream source repositories and
release archives. Match the versions in BUILD_INFO.json, including Qt's patch version.
PySide/Shiboken: https://download.qt.io/official_releases/QtForPython/
Qt: https://download.qt.io/archive/qt/
Python: https://www.python.org/downloads/source/

The licenses/ directory includes LGPLv3, GPLv3 (incorporated by LGPLv3) and the
Python license. During a Windows build, scripts/collect_notices.py copies available
package license/notice files and runtime information into third_party_licenses/.
Review the resulting file inventory and the Qt third-party catalog before public
redistribution, particularly if build dependencies or plugins change. Installed
packages do not always ship every upstream notice; this collector is not a legal
compliance certification. Qt's catalog: https://doc.qt.io/qt-6/licenses-used-in-qt.html

Windows platform runtimes retain their original terms and notices. This project
provides no claim that dependency software is covered by the DeskShelf MIT license.
