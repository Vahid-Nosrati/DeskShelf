"""Create public archives without saved entries, backups or development environments."""
import argparse
import hashlib
from pathlib import Path
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from app_meta import VERSION
SOURCE_DIRS={'assets','locales','help','docs','scripts','licenses','.github'}
SOURCE_FILES={'main.py','core.py','i18n.py','settings.py','visuals.py','info_dialogs.py','app_meta.py',
 'app_info.json','test_deskshelf.py','test_release.py','test_ordering.py','test_visual_layout.py','operations.py','requirements.txt','build_windows.bat',
 'run_windows.bat','package_release.bat','README.md','README_FA.md','LICENSE','CONTRIBUTORS',
 'CONTRIBUTING.md','CHANGELOG.md','THIRD_PARTY_NOTICES.md','.gitignore'}

def source_files(root=ROOT):
    for p in sorted(root.rglob('*')):
        rel=p.relative_to(root)
        if p.is_symlink() or not p.is_file() or '__pycache__' in rel.parts:continue
        if (len(rel.parts)==1 and rel.name in SOURCE_FILES) or rel.parts[0] in SOURCE_DIRS:yield p,rel

def portable_files(folder):
    for p in sorted(folder.rglob('*')):
        rel=p.relative_to(folder)
        if p.is_symlink() or not p.is_file() or rel.parts[0]=='data' or p.suffix.lower()=='.log' or p.name=='DeskShelf.lock':continue
        yield p,rel

def archive(path,files):
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        for p,rel in files:z.write(p,Path('DeskShelf')/rel)
    with zipfile.ZipFile(path) as z:
        if z.testzip():raise RuntimeError('Archive verification failed')

def package(source_only=False):
    out=ROOT/'release';out.mkdir(exist_ok=True);files=[]
    source=out/f'DeskShelf-v{VERSION}-source.zip';archive(source,source_files());files.append(source)
    if not source_only:
        folder=ROOT/'dist'/'DeskShelf'
        if not (folder/'DeskShelf.exe').is_file():raise FileNotFoundError('Build dist/DeskShelf/DeskShelf.exe first, or use --source-only.')
        for required in ['_internal','app_info.json','LICENSE','licenses','locales','help']:
            if not (folder/required).exists():raise FileNotFoundError('Incomplete portable build: '+required)
        path=out/f'DeskShelf-v{VERSION}-windows-x64-portable.zip';archive(path,portable_files(folder));files.append(path)
    checksum=out/'SHA256SUMS.txt';checksum.write_text(''.join(hashlib.sha256(f.read_bytes()).hexdigest()+'  '+f.name+'\n' for f in files),'utf-8')
    for f in files:print(f.name, f.stat().st_size,'bytes')
    print(checksum.name)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--source-only',action='store_true');args=parser.parse_args();package(args.source_only)
