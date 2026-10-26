"""Collect available dependency notices from the actual build environment."""
import importlib.metadata as metadata
import json
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[1]

def collect():
    target=ROOT/'third_party_licenses';target.mkdir(exist_ok=True)
    versions={}
    for name in ('PySide6','PySide6_Essentials','PySide6_Addons','shiboken6','pyinstaller'):
        try:dist=metadata.distribution(name)
        except metadata.PackageNotFoundError:continue
        versions[name]=dist.version
        for entry in dist.files or []:
            if any(x in str(entry).lower() for x in ('license','copying','notice')):
                source=Path(dist.locate_file(entry))
                if source.is_file():
                    # Use only the package-relative suffix, never parent traversals.
                    safe=[p for p in entry.parts if p not in ('.','..')]
                    dest=target/name/Path(*safe);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,dest)
    import PySide6
    from PySide6.QtCore import qVersion
    qt_root=Path(PySide6.__file__).resolve().parent
    for folder in [qt_root/'Qt'/'licenses',qt_root/'licenses']:
        if folder.is_dir():shutil.copytree(folder,target/'Qt',dirs_exist_ok=True)
    for folder in [Path(sys.base_prefix),Path(sys.base_prefix)/'Lib']:
        for filename in ('LICENSE.txt','LICENSE','LICENSE.md'):
            source=folder/filename
            if source.is_file():shutil.copy2(source,target/('Python-'+filename))
    from app_meta import VERSION
    info={'DeskShelf':VERSION,'Python':sys.version.split()[0],'Qt':qVersion(),'packages':versions}
    (ROOT/'BUILD_INFO.json').write_text(json.dumps(info,indent=2)+'\n','utf-8')
    (target/'README.txt').write_text('Dependency notices copied from the installed build packages.\nSee THIRD_PARTY_NOTICES.md and licenses/ for license texts and upstream sources.\n','utf-8')
    print('Dependency notices collected.')

if __name__=='__main__':
    sys.path.insert(0,str(ROOT));collect()
