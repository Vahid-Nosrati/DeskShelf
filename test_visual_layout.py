import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import tempfile
import unittest
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication,QLabel
from core import Store,KINDS
from main import Main,AdaptiveHeader
from i18n import LANGUAGES
from visuals import icon
APP=QApplication.instance() or QApplication([])

def settle():
    for _ in range(8):APP.processEvents()

class HeaderAndHintTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.w=Main(Store(self.tmp.name));self.w.resize(1368,800);self.w.show();settle()
    def tearDown(self):self.w.close();settle();self.tmp.cleanup()
    def header(self,k='apps'):return self.w.panels[k].findChild(AdaptiveHeader)
    def test_standard_width_keeps_all_titles_inline(self):
        for k in KINDS:
            h=self.header(k);self.assertFalse(h.wrapped,k)
            self.assertFalse(h.title.geometry().intersects(h.controls.geometry()))
            self.assertEqual(h.title.geometry().center().y(),h.controls.geometry().center().y())
    def test_window_and_splitter_resize_wrap_and_unwrap(self):
        self.w.resize(960,800);settle();self.assertTrue(all(self.header(k).wrapped for k in KINDS))
        for k in KINDS:
            h=self.header(k);self.assertGreater(h.controls.y(),h.title.geometry().bottom())
        self.w.resize(1600,800);settle();self.assertFalse(any(self.header(k).wrapped for k in KINDS))
        self.w.splitter.setSizes([210,500,430,350]);settle();self.assertTrue(self.header('web').wrapped)
        self.w.splitter.setSizes([400]*4);settle();self.assertFalse(self.header('web').wrapped)
    def test_long_title_and_font_changes_trigger_wrap_without_resizing_window(self):
        h=self.header();label=h.findChild(QLabel,'heading_apps');original=label.text()
        label.setText('A deliberately long translated column heading');settle();self.assertTrue(h.wrapped)
        label.setText(original);settle();self.assertFalse(h.wrapped)
        label.setStyleSheet('font-size:26pt');settle();self.assertTrue(h.wrapped)
        label.setStyleSheet('');settle();self.assertFalse(h.wrapped)
    def test_all_languages_have_non_overlapping_geometry(self):
        for code in LANGUAGES:
            self.w.data['language']=code;self.w.build();settle()
            for k in KINDS:
                h=self.header(k)
                self.assertEqual(h.wrapped,h.width()<h.inline_width(),(code,k))
                self.assertFalse(h.title.geometry().intersects(h.controls.geometry()),(code,k))
                for button in self.w.buttons[k].values():self.assertTrue(h.controls.rect().contains(button.geometry()),(code,k))
                if not h.wrapped:
                    if code in ('fa','ar'):self.assertGreater(h.title.x(),h.controls.x())
                    else:self.assertLess(h.title.x(),h.controls.x())
    def test_empty_hint_tracks_categories_and_returns_after_removal(self):
        tree=self.w.columns['folders'];self.assertTrue(tree.empty.isVisible())
        self.w.data['categories']['folders'].append({'id':'empty','name':'Empty'});self.w.refresh();settle()
        self.assertFalse(tree.empty.isVisible())
        for n in range(15):self.w.data['categories']['folders'].append({'id':'cat'+str(n),'name':'Category '+str(n)})
        self.w.refresh();settle();self.assertFalse(tree.empty.isVisible())
        self.w.data['categories']['folders']=[{'id':'general','name':''}];self.w.refresh();settle();self.assertTrue(tree.empty.isVisible())
        self.w.data['items'].append({'id':'x','kind':'folders','category':'general','title':'Example','path':'C:/Example','note':''})
        self.w.refresh();settle();self.assertFalse(tree.empty.isVisible())
        self.w.data['items'].clear();self.w.refresh();settle();self.assertTrue(tree.empty.isVisible())
    def test_no_results_hint_remains_visible_without_overlaying_categories(self):
        self.w.data['categories']['folders'].append({'id':'empty','name':'Empty'});self.w.refresh()
        self.w.search.setText('not found');settle();tree=self.w.columns['folders']
        self.assertTrue(tree.empty.isVisible());self.assertEqual(tree.empty.text(),self.w.t('no_results'))
        self.assertTrue(all(tree.topLevelItem(n).isHidden() for n in range(tree.topLevelItemCount())))
        self.w.search.clear();settle();self.assertFalse(tree.empty.isVisible())
    def test_arrows_have_broad_heads_and_short_thin_shafts(self):
        up=icon('up',size=96).pixmap(96,96).toImage();down=icon('down',size=96).pixmap(96,96).toImage()
        def count(image,y):return sum(image.pixelColor(x,y).alpha()>150 for x in range(image.width()))
        self.assertGreater(count(up,38),count(up,65)*2)
        self.assertGreater(count(down,58),count(down,28)*2)
        self.assertGreater(count(up,65),0);self.assertGreater(count(down,28),0)
        self.assertNotEqual(up,down)

if __name__=='__main__':unittest.main(verbosity=2)
