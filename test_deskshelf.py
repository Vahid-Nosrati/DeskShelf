import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PySide6.QtCore import Qt,QTimer,QPoint
from PySide6.QtGui import QImage
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication,QDialog,QMessageBox,QTabWidget
from core import initial,theme_defaults,validate,Store,KINDS
from main import Main,EntryDialog
from settings import AppearanceDialog
from visuals import blend

APP=QApplication.instance() or QApplication([])
APP.setStyle('Fusion')

class PersistenceTests(unittest.TestCase):
    def test_roundtrip_unicode_and_previous(self):
        with tempfile.TemporaryDirectory() as p:
            s=Store(p);s.save();s.data['categories']['web'].append({'id':'research','name':'تحقیق'});s.save()
            self.assertEqual(Store(p).data['categories']['web'][1]['name'],'تحقیق')
            self.assertEqual(len(json.loads((Path(p)/'previous.json').read_text())['categories']['web']),1)
    def test_bad_data_cannot_overwrite_good_file(self):
        with tempfile.TemporaryDirectory() as p:
            s=Store(p);s.save();before=s.path.read_bytes();s.data['theme']['opacity']['web']=101
            with self.assertRaises(ValueError):s.save()
            self.assertEqual(s.path.read_bytes(),before)
    def test_old_format_and_orphan_validation(self):
        d=initial();d['version']=1;d.pop('theme');self.assertEqual(validate(d)['theme'],theme_defaults())
        d=initial();d['items']=[{'id':'x','kind':'web','category':'missing','title':'','path':'https://example.com','note':''}]
        with self.assertRaises(ValueError):validate(d)
    def test_invalid_backups(self):
        for key,value in [('order',['web']*4),('widths',[-1,2,3,4]),('collapsed',{'x':'true'})]:
            d=initial();d[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):validate(d)

class InterfaceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.w=Main(Store(self.tmp.name));self.w.show();APP.processEvents()
    def tearDown(self):
        self.w.close();APP.processEvents();self.tmp.cleanup()
    def add_item(self,id='x',kind='web',category='general'):
        item={'id':id,'kind':kind,'category':category,'title':'عنوان نمونه','path':'https://example.com/'+id,'note':'ادامه از بخش سوم'}
        self.w.data['items'].append(item);self.w.refresh();return item
    def test_languages_search_and_path_direction(self):
        self.add_item()
        for lang,dir in [('fa',Qt.RightToLeft),('en',Qt.LeftToRight)]:
            self.w.data['language']=lang;self.w.build();APP.processEvents()
            self.assertEqual(self.w.layoutDirection(),dir);self.assertEqual(len(self.w.columns),4)
            dialog=EntryDialog(self.w,'files');self.assertEqual(dialog.path.layoutDirection(),Qt.LeftToRight);dialog.deleteLater()
            self.w.search.setText('بخش سوم');self.assertEqual(self.w.columns['web'].topLevelItem(0).childCount(),1)
            self.w.search.setText('no such item');self.assertTrue(self.w.columns['web'].empty.isVisible())
    def test_live_preview_cancel_does_not_save(self):
        self.w.save();before=self.w.store.path.read_bytes();original=copy.deepcopy(self.w.data['theme'])
        d=AppearanceDialog(self.w);d.option('style','raised');d.alpha('web',0);d.choose('item',0)
        self.assertEqual(self.w.theme()['style'],'raised');self.assertEqual(self.w.theme()['opacity']['web'],0)
        self.assertEqual(self.w.data['theme'],original);self.assertEqual(self.w.store.path.read_bytes(),before)
        d.reject();self.assertEqual(self.w.theme(),original);self.assertIsNone(self.w.preview_theme)
    def test_settings_accept_and_reload(self):
        d=AppearanceDialog(self.w);d.option('style','raised');d.option('density','compact');d.alpha('item',22)
        d.language.setCurrentIndex(d.language.findData('en'));d.order.setCurrentRow(0);d.move(1)
        QTimer.singleShot(0,d.accept)
        with patch('main.AppearanceDialog',return_value=d):self.w.settings()
        loaded=Store(self.tmp.name).data
        self.assertEqual(loaded['theme']['style'],'raised');self.assertEqual(loaded['theme']['opacity']['item'],22)
        self.assertEqual(loaded['language'],'en');self.assertEqual(loaded['order'][1],'web')
    def test_delete_category_undo_preserves_new_items(self):
        self.w.data['categories']['web'].append({'id':'research','name':'تحقیق'});self.add_item(category='research')
        tree=self.w.columns['web'];tree.setCurrentItem(tree.topLevelItem(1))
        with patch.object(self.w,'question',return_value=QMessageBox.Yes):self.w.remove(tree)
        self.assertEqual(self.w.find('x')['category'],'general');self.add_item('new');self.w.undo()
        self.assertEqual(self.w.find('x')['category'],'research');self.assertIsNotNone(self.w.find('new'))
    def test_category_click_and_keyboard_open(self):
        self.add_item();tree=self.w.columns['web'];group=tree.topLevelItem(0)
        rect=tree.visualItemRect(group);QTest.mouseClick(tree.viewport(),Qt.LeftButton,pos=rect.center());APP.processEvents()
        self.assertFalse(group.isExpanded());self.assertTrue(self.w.data['collapsed']['web:general'])
        QTest.keyClick(tree,Qt.Key_Return);self.assertTrue(group.isExpanded())
        tree.setCurrentItem(group.child(0))
        with patch('main.QDesktopServices.openUrl',return_value=True) as opened:
            QTest.keyClick(tree,Qt.Key_Return);opened.assert_called_once()
    def test_palette_extremes_render_and_density(self):
        self.add_item();tree=self.w.columns['web'];idx=tree.indexFromItem(tree.topLevelItem(0).child(0));delegate=tree.itemDelegate()
        from PySide6.QtWidgets import QStyleOptionViewItem
        comfortable=delegate.sizeHint(QStyleOptionViewItem(),idx).height()
        for c in ['#000000','#FFFFFF','#FF0000']:
            for style in ['flat','raised']:
                self.w.data['theme']['style']=style
                for k in self.w.data['theme']['colors']:self.w.data['theme']['colors'][k]=c;self.w.data['theme']['opacity'][k]=100
                self.w.apply_theme();APP.processEvents();self.assertFalse(self.w.grab().isNull())
        self.w.data['theme']['density']='compact';self.w.apply_theme();self.assertLess(delegate.sizeHint(QStyleOptionViewItem(),idx).height(),comfortable)
    def test_clipboard_keeps_complete_path(self):
        d=EntryDialog(self.w,'folders');value=r'C:\Projects\Research';d.path.setText(value);d.copy(d.path)
        self.assertEqual(APP.clipboard().text(),value);d.deleteLater()

if __name__=='__main__':unittest.main(verbosity=2)
