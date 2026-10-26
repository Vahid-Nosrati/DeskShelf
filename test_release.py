import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from PySide6.QtCore import Qt,QRect
from PySide6.QtGui import QPixmap,QPainter
from PySide6.QtWidgets import QApplication,QStyleOptionViewItem,QStyle
from core import initial,Store,validate
from main import Main
from settings import AppearanceDialog
from info_dialogs import HelpDialog
from i18n import LANGUAGES,RTL_LANGUAGES,catalog,guide
from app_meta import app_info

APP=QApplication.instance() or QApplication([])
ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('release_pack',ROOT/'scripts'/'package_release.py')
pack=importlib.util.module_from_spec(spec);spec.loader.exec_module(pack)

class TranslationTests(unittest.TestCase):
    def test_all_catalogs_and_guides_complete(self):
        self.assertEqual(len(LANGUAGES),12)
        keys=set(catalog('en'));sections=[s['id'] for s in guide('en')]
        for code in LANGUAGES:
            with self.subTest(code=code):
                self.assertEqual(set(catalog(code)),keys)
                self.assertTrue(all(isinstance(v,str) and v.strip() for v in catalog(code).values()))
                self.assertEqual([s['id'] for s in guide(code)],sections)
                self.assertTrue(all(s['title'] and len(s['body'])>80 for s in guide(code)))
                d=initial();d['language']=code;self.assertEqual(validate(d)['language'],code)
        self.assertEqual(initial()['language'],'en')
    def test_existing_language_is_retained(self):
        with tempfile.TemporaryDirectory() as p:
            s=Store(p);s.data['language']='fa';s.save();self.assertEqual(Store(p).data['language'],'fa')

class RaisedDirectionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.w=Main(Store(self.tmp.name));self.w.show();APP.processEvents()
    def tearDown(self):self.w.close();APP.processEvents();self.tmp.cleanup()
    def test_all_languages_both_styles_help_and_settings(self):
        for code in LANGUAGES:
            self.w.data['language']=code;self.w.build();expected=Qt.RightToLeft if code in RTL_LANGUAGES else Qt.LeftToRight
            for style in ('flat','raised'):
                with self.subTest(code=code,style=style):
                    self.w.data['theme']['style']=style;self.w.apply_theme();APP.processEvents()
                    self.assertEqual(self.w.layoutDirection(),expected)
                    for t in self.w.columns.values():self.assertEqual(t.layoutDirection(),expected);self.assertIsNone(t.parentWidget().graphicsEffect())
                    self.assertFalse(self.w.grab().isNull())
            h=HelpDialog(self.w);self.assertEqual(h.sections.count(),12);h.search.setText('THIS_QUERY_DOES_NOT_EXIST');self.assertEqual(h.sections.count(),0);h.close()
            d=AppearanceDialog(self.w);self.assertEqual(d.language.count(),12);d.reject()
    def test_raised_looks_different_and_ignores_option_direction(self):
        self.w.data['language']='fa';self.w.data['items']=[{'id':'x','kind':'web','category':'general','title':'عنوان Test 42','path':'https://example.com','note':''}];self.w.build();APP.processEvents()
        tree=self.w.columns['web'];idx=tree.indexFromItem(tree.topLevelItem(0).child(0));delegate=tree.itemDelegate()
        def render(style,direction):
            self.w.data['theme']['style']=style;pix=QPixmap(320,70);pix.fill(Qt.white);p=QPainter(pix)
            option=QStyleOptionViewItem();option.rect=QRect(0,0,320,70);option.direction=direction;option.font=self.w.font();option.state=QStyle.State_Enabled
            delegate.paint(p,option,idx);p.end();return pix.toImage()
        flat=render('flat',Qt.RightToLeft);raised=render('raised',Qt.RightToLeft)
        self.assertNotEqual(flat,raised)
        self.assertEqual(raised,render('raised',Qt.LeftToRight),'Effect-provided direction must not move Persian text')
        self.assertEqual(flat,render('flat',Qt.LeftToRight))

class PublicReleaseTests(unittest.TestCase):
    def test_metadata_empty_invalid_and_escaped(self):
        with tempfile.TemporaryDirectory() as p,patch('app_meta.app_root',return_value=Path(p)):
            target=Path(p)/'app_info.json';self.assertEqual(app_info()['author'],'Vahid Nosrati')
            target.write_text('{broken');self.assertEqual(app_info()['repository_url'],'')
            target.write_text(json.dumps({'author':'Example','repository_url':'https://example.com','public_contact':None}))
            self.assertEqual(app_info()['author'],'Example');self.assertEqual(app_info()['public_contact'],'')
    def test_archive_excludes_personal_data_and_build_files(self):
        with tempfile.TemporaryDirectory() as p:
            root=Path(p)
            for name in ['main.py','LICENSE','app_info.json','data/data.json','.venv/private.py','build/private.txt','dist/DeskShelf.exe','.git/config','backup-personal.json','docs/guide.md']:
                path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text('fixture')
            names={str(r) for _,r in pack.source_files(root)}
            self.assertEqual(names,{'main.py','LICENSE','app_info.json','docs/guide.md'})
            portable=root/'portable';(portable/'data').mkdir(parents=True);(portable/'_internal').mkdir()
            (portable/'DeskShelf.exe').write_bytes(b'fixture');(portable/'data'/'data.json').write_text('private');(portable/'_internal'/'library.dll').write_bytes(b'fixture')
            files=list(pack.portable_files(portable));self.assertNotIn('data/data.json',{r.as_posix() for _,r in files})
            out=root/'release.zip';pack.archive(out,files)
            import zipfile
            with zipfile.ZipFile(out) as z:self.assertIn('DeskShelf/_internal/library.dll',z.namelist())
    def test_no_personal_links_and_standard_mit(self):
        info=json.loads((ROOT/'app_info.json').read_text());self.assertEqual(info,{'author':'Vahid Nosrati','github_profile':'','repository_url':'','public_contact':''})
        license=(ROOT/'LICENSE').read_text();self.assertIn('Copyright (c) 2026 Vahid Nosrati',license);self.assertIn('THE SOFTWARE IS PROVIDED "AS IS"',license)
        self.assertTrue((ROOT/'licenses'/'GPL-3.0.txt').exists())

if __name__=='__main__':unittest.main(verbosity=2)
