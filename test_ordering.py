import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from PySide6.QtCore import Qt,QItemSelectionModel,QMimeData,QPointF
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication,QDialog
from core import initial,validate,Store
from operations import reorder,remove_batch,undo_batch,can_reorder,removal_summary
from main import Main,Column,DeletionDialog

APP=QApplication.instance() or QApplication([])

def fixture():
    d=initial()
    d['categories']['web'] += [{'id':'a','name':'A'},{'id':'b','name':'B'},{'id':'c','name':'C'}]
    d['categories']['files'] += [{'id':'f','name':'Files'}]
    for kind,cat,count in [('web','general',2),('web','a',5),('web','b',4),('web','c',1),('files','f',3)]:
        for n in range(count):
            identifier=kind+'-'+cat+str(n)
            d['items'].append({'id':identifier,'kind':kind,'category':cat,'title':identifier,
                               'path':'https://example.com/'+identifier,'note':''})
    d['collapsed']['web:b']=True
    return d

def ids(d,cat,kind='web'):
    return [i['id'] for i in d['items'] if i['kind']==kind and i['category']==cat]

class OrderingTests(unittest.TestCase):
    def test_category_scope_general_move_and_roundtrip(self):
        d=fixture();other=copy.deepcopy(d['categories']['files'])
        self.assertTrue(reorder(d,'web',('category','b'),('category','general')))
        self.assertEqual([c['id'] for c in d['categories']['web']],['b','general','a','c'])
        self.assertEqual(d['categories']['files'],other);validate(d)
        with tempfile.TemporaryDirectory() as p:
            s=Store(p);s.data=d;s.save();self.assertEqual(Store(p).data,d)
    def test_reject_cross_category_type_column_and_noop(self):
        d=fixture();before=copy.deepcopy(d)
        for source,target in [(('item','web-a0'),('item','web-b0')),
                              (('item','web-a0'),('item','files-f0')),
                              (('category','a'),('item','web-a0')),
                              (('category','a'),('category','f')),
                              (('category','a'),('category','a'))]:
            self.assertFalse(reorder(d,'web',source,target));self.assertEqual(d,before)
    def test_item_reorder_only_bucket_and_reload(self):
        d=fixture();untouched=[copy.deepcopy(i) for i in d['items'] if i['category']!='a']
        self.assertTrue(reorder(d,'web',('item','web-a4'),('item','web-a0')))
        self.assertEqual(ids(d,'a'),['web-a4','web-a0','web-a1','web-a2','web-a3'])
        self.assertEqual([i for i in d['items'] if i['category']!='a'],untouched)
        with tempfile.TemporaryDirectory() as p:
            s=Store(p);s.data=d;s.save();self.assertEqual(ids(Store(p).data,'a'),ids(d,'a'))
    def test_batch_items_across_categories_exact_undo(self):
        d=fixture();before=copy.deepcopy(d);chosen={'web-a1','web-a3','web-b0','web-b3'}
        record=remove_batch(d,'web','item',chosen,'remove')
        self.assertEqual(removal_summary(before,'web','item',chosen),(0,4))
        self.assertTrue(chosen.isdisjoint(i['id'] for i in d['items']))
        undo_batch(d,record);self.assertEqual(d,before)
    def test_keep_mode_append_visual_category_order_and_full_undo(self):
        d=fixture();reorder(d,'web',('category','b'),('category','a'))
        # Deliberately interleave global entries: transfer order follows the visible groups.
        d['items'].reverse();before=copy.deepcopy(d)
        expected=ids(d,'general')+ids(d,'b')+ids(d,'a')
        record=remove_batch(d,'web','category',{'a','b'},'keep')
        self.assertEqual(ids(d,'general'),expected)
        self.assertEqual([c['id'] for c in d['categories']['web']],['general','c'])
        undo_batch(d,record);self.assertEqual(d,before)
    def test_remove_mode_unique_counts_and_exact_full_undo(self):
        d=fixture();before=copy.deepcopy(d)
        self.assertEqual(removal_summary(d,'web','category',['a','b','a']),(2,9))
        record=remove_batch(d,'web','category',['a','b','a'],'remove')
        self.assertEqual(len(record['removed_items']),9);self.assertEqual(ids(d,'general'),ids(before,'general'))
        self.assertEqual(len(d['items']),len(before['items'])-9)
        undo_batch(d,record);self.assertEqual(d,before)
    def test_general_and_foreign_ids_rejected_atomically(self):
        d=fixture();before=copy.deepcopy(d)
        for typ,selected in [('category',{'general'}),('category',{'a','f'}),('item',{'web-a0','files-f0'})]:
            with self.assertRaises(ValueError):remove_batch(d,'web',typ,selected)
            self.assertEqual(d,before)
        with self.assertRaises(ValueError):remove_batch(d,'web','category',{'a'},'invalid')
        self.assertEqual(d,before)
    def test_undo_keeps_later_additions_and_edits(self):
        d=fixture();record=remove_batch(d,'web','category',{'a'},'keep')
        item=next(i for i in d['items'] if i['id']=='web-a0');item['title']='Edited after removal'
        new={'id':'new','kind':'web','category':'general','title':'New','path':'https://example.org','note':''};d['items'].append(new)
        undo_batch(d,record)
        self.assertEqual(next(i for i in d['items'] if i['id']=='web-a0')['title'],'Edited after removal')
        self.assertEqual(ids(d,'a'),['web-a0','web-a1','web-a2','web-a3','web-a4']);self.assertIn(new,d['items']);validate(d)
    def test_empty_category_and_name_conflict(self):
        d=fixture();d['categories']['web'].append({'id':'empty','name':'Empty'})
        record=remove_batch(d,'web','category',{'empty'},'remove')
        d['categories']['web'].append({'id':'new','name':'Empty'})
        undo_batch(d,record);validate(d)
        self.assertEqual(next(c for c in d['categories']['web'] if c['id']=='empty')['name'],'Empty (restored)')
    def test_undo_never_overwrites_later_manual_recategorization(self):
        d=fixture();record=remove_batch(d,'web','category',{'a'},'keep')
        item=next(i for i in d['items'] if i['id']=='web-a0');item['category']='b'
        undo_batch(d,record);self.assertEqual(item['category'],'b');validate(d)

class FakeDrop:
    def __init__(self,source,mime,point):self.src=source;self.mime=mime;self.point=QPointF(point);self.accepted=False
    def source(self):return self.src
    def mimeData(self):return self.mime
    def position(self):return self.point
    def setDropAction(self,action):self.action=action
    def accept(self):self.accepted=True
    def ignore(self):self.accepted=False
    def acceptProposedAction(self):self.accepted=True

class SelectionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();store=Store(self.tmp.name);store.data=fixture()
        self.w=Main(store);self.w.resize(1360,850);self.w.show();self.tree=self.w.columns['web']
        self.tree.expandAll();APP.processEvents()
    def tearDown(self):self.w.close();APP.processEvents();self.tmp.cleanup()
    def node(self,ref,tree=None):
        tree=tree or self.tree
        for n in range(tree.topLevelItemCount()):
            g=tree.topLevelItem(n)
            if g.data(0,Qt.UserRole)==ref:return g
            for c in range(g.childCount()):
                item=g.child(c)
                if item.data(0,Qt.UserRole)==ref:return item
        raise AssertionError(ref)
    def click(self,ref,mod=Qt.NoModifier,tree=None):
        tree=tree or self.tree;node=self.node(ref,tree);tree.scrollToItem(node);APP.processEvents()
        QTest.mouseClick(tree.viewport(),Qt.LeftButton,mod,tree.visualItemRect(node).center());APP.processEvents()
    def selected(self,tree=None):return {tuple(n.data(0,Qt.UserRole)) for n in (tree or self.tree).selectedItems()}
    def test_ctrl_and_shift_items_across_categories_no_mixed_selection(self):
        self.click(('item','web-a3'));self.click(('item','web-b1'),Qt.ControlModifier)
        self.assertEqual(self.selected(),{('item','web-a3'),('item','web-b1')})
        self.click(('item','web-a4'));self.click(('item','web-b2'),Qt.ShiftModifier)
        self.assertEqual(self.selected(),{('item','web-a4'),('item','web-b0'),('item','web-b1'),('item','web-b2')})
    def test_type_switch_replaces_selection_in_both_directions(self):
        self.click(('item','web-a0'));self.click(('item','web-a1'),Qt.ControlModifier)
        self.click(('category','b'),Qt.ControlModifier);self.assertEqual(self.selected(),{('category','b')})
        self.tree.expandAll();self.click(('item','web-a2'),Qt.ControlModifier);self.assertEqual(self.selected(),{('item','web-a2')})
    def test_general_excluded_from_batch_but_can_move_alone(self):
        self.click(('category','a'));self.click(('category','b'),Qt.ControlModifier);self.click(('category','general'),Qt.ControlModifier)
        self.assertEqual(self.selected(),{('category','a'),('category','b')})
        self.click(('category','general'));self.assertFalse(self.w.buttons['web']['delete'].isEnabled())
        self.w.move_selected(self.tree,1);self.assertEqual(self.w.data['categories']['web'][1]['id'],'general')
    def test_column_switch_clears_other_selection_and_inactive_delete_is_noop(self):
        self.click(('item','web-a0'));files=self.w.columns['files'];files.expandAll()
        self.click(('item','files-f0'),tree=files);self.assertEqual(self.selected(),set());self.assertEqual(self.w.active_kind,'files')
        before=copy.deepcopy(self.w.data)
        with patch.object(self.w,'confirm_removal') as confirm:self.w.remove(self.tree);confirm.assert_not_called()
        self.assertEqual(self.w.data,before)
    def test_move_buttons_multiselect_filter_and_persistence(self):
        self.click(('item','web-a0'));self.assertFalse(self.w.can_move(self.tree,-1));self.assertTrue(self.w.can_move(self.tree,1))
        self.w.move_selected(self.tree,1);self.assertEqual(ids(self.w.data,'a')[:2],['web-a1','web-a0'])
        self.assertEqual(ids(Store(self.tmp.name).data,'a'),ids(self.w.data,'a'))
        self.click(('item','web-a2'),Qt.ControlModifier);self.assertFalse(self.w.can_move(self.tree,1));self.assertFalse(self.tree.dragEnabled())
        self.w.search.setText('web-a');self.assertEqual(self.selected(),set())
        self.click(('item','web-a0'));before=copy.deepcopy(self.w.data);self.w.move_selected(self.tree,1)
        self.assertEqual(self.w.data,before);self.assertFalse(self.tree.dragEnabled())
    def test_actual_internal_drop_and_forbidden_destinations(self):
        self.click(('item','web-a0'));mime=QMimeData();mime.setData(Column.ORDER_MIME,json.dumps({'kind':'web','ref':['item','web-a0']}).encode())
        target=self.node(('item','web-a3'));point=self.tree.visualItemRect(target).bottomLeft()+__import__('PySide6.QtCore',fromlist=['QPoint']).QPoint(20,-1)
        event=FakeDrop(self.tree,mime,point);self.tree.dropEvent(event);self.assertTrue(event.accepted)
        self.assertEqual(ids(self.w.data,'a'),['web-a1','web-a2','web-a3','web-a0','web-a4'])
        self.tree.expandAll();APP.processEvents();before=copy.deepcopy(self.w.data)
        for targetref in [('item','web-b0'),('category','b')]:
            point=self.tree.visualItemRect(self.node(targetref)).center();event=FakeDrop(self.tree,mime,point);self.tree.dropEvent(event)
            self.assertFalse(event.accepted);self.assertEqual(self.w.data,before)
        files=self.w.columns['files'];files.expandAll();event=FakeDrop(self.tree,mime,files.visualItemRect(files.topLevelItem(0)).center())
        files.dropEvent(event);self.assertFalse(event.accepted);self.assertEqual(self.w.data,before)
    def test_batch_dialog_defaults_counts_cancellation_and_two_modes(self):
        d=DeletionDialog(self.w,'web','category',2,9)
        self.assertEqual(d.mode(),'keep');d.remove_all.setChecked(True);self.assertEqual(d.mode(),'remove');d.close()
        self.click(('category','a'));self.click(('category','b'),Qt.ControlModifier);before=copy.deepcopy(self.w.data)
        with patch.object(self.w,'confirm_removal',return_value=None):self.w.remove(self.tree)
        self.assertEqual(self.w.data,before)
        for mode in ['keep','remove']:
            with patch.object(self.w,'confirm_removal',return_value=mode) as confirm:self.w.remove(self.tree)
            self.assertEqual(len(self.w.undo_stack),1);self.assertEqual(confirm.call_args.args,('web','category',{'a','b'}))
            self.w.undo();self.assertEqual(self.w.data,before)
            self.tree.expandAll();self.click(('category','a'));self.click(('category','b'),Qt.ControlModifier)
    def test_batch_item_delete_through_delete_key_and_one_undo(self):
        self.click(('item','web-a1'));self.click(('item','web-b2'),Qt.ControlModifier);before=copy.deepcopy(self.w.data)
        with patch.object(self.w,'confirm_removal',return_value='remove'):QTest.keyClick(self.tree,Qt.Key_Delete)
        self.assertIsNone(self.w.find('web-a1'));self.assertIsNone(self.w.find('web-b2'));self.assertEqual(len(self.w.undo_stack),1)
        self.w.undo();self.assertEqual(self.w.data,before)
    def test_shift_category_range_ignores_children_and_general(self):
        self.click(('category','general'))
        self.click(('category','c'),Qt.ShiftModifier)
        self.assertEqual(self.selected(),{('category','a'),('category','b'),('category','c')})
    def test_internal_drag_indicator_search_guard_and_external_import(self):
        self.click(('item','web-a0'));mime=QMimeData()
        mime.setData(Column.ORDER_MIME,json.dumps({'kind':'web','ref':['item','web-a0']}).encode())
        point=self.tree.visualItemRect(self.node(('item','web-a2'))).center()
        event=FakeDrop(self.tree,mime,point);self.tree.dragMoveEvent(event)
        self.assertTrue(event.accepted);self.assertFalse(self.tree.drop_line.isHidden());self.tree.reset_drop()
        self.w.search.setText('web-a');self.click(('item','web-a0'))
        before=copy.deepcopy(self.w.data);event=FakeDrop(self.tree,mime,point);self.tree.dropEvent(event)
        self.assertFalse(event.accepted);self.assertEqual(self.w.data,before)
        self.w.search.clear();mime2=QMimeData();from PySide6.QtCore import QUrl
        mime2.setUrls([QUrl('https://example.net/resource')]);event=FakeDrop(None,mime2,point)
        with patch.object(self.w,'edit') as edit:
            self.tree.dropEvent(event);edit.assert_called_once_with('web',prefill='https://example.net/resource')
        self.assertTrue(event.accepted)
    def test_forged_payload_cannot_fall_back_to_external_import(self):
        self.click(('item','web-a0'));before=copy.deepcopy(self.w.data);mime=QMimeData()
        mime.setData(Column.ORDER_MIME,b'{invalid');mime.setText('https://example.com')
        event=FakeDrop(self.tree,mime,self.tree.visualItemRect(self.node(('item','web-a1'))).center())
        with patch.object(self.w,'edit') as edit:self.tree.dropEvent(event);edit.assert_not_called()
        self.assertFalse(event.accepted);self.assertEqual(self.w.data,before)
    def test_drag_category_order_and_general_boundary(self):
        self.click(('category','c'));mime=QMimeData()
        mime.setData(Column.ORDER_MIME,json.dumps({'kind':'web','ref':['category','c']}).encode())
        point=self.tree.visualItemRect(self.node(('category','general'))).topLeft()+__import__('PySide6.QtCore',fromlist=['QPoint']).QPoint(40,3)
        event=FakeDrop(self.tree,mime,point);self.tree.dropEvent(event);self.assertTrue(event.accepted)
        self.assertEqual([c['id'] for c in self.w.data['categories']['web']],['c','general','a','b'])
        self.assertEqual(Store(self.tmp.name).data['categories']['web'],self.w.data['categories']['web'])
    def test_original_target_files_are_never_deleted(self):
        path=Path(self.tmp.name)/'original.txt';path.write_text('Important original')
        item=self.w.find('files-f0');item['path']=str(path);files=self.w.columns['files'];files.expandAll()
        self.click(('item','files-f0'),tree=files)
        with patch.object(self.w,'confirm_removal',return_value='remove'):self.w.remove(files)
        self.assertEqual(path.read_text(),'Important original');self.w.undo()
        self.assertEqual(self.w.find('files-f0')['path'],str(path))
    def test_dialog_enter_cancels_and_right_click_retains_batch(self):
        from PySide6.QtCore import QTimer
        from PySide6.QtGui import QMouseEvent
        self.click(('item','web-a0'));self.click(('item','web-a1'),Qt.ControlModifier)
        selected=self.selected();node=self.node(('item','web-a0'));point=self.tree.visualItemRect(node).center()
        event=QMouseEvent(__import__('PySide6.QtCore',fromlist=['QEvent']).QEvent.MouseButtonPress,QPointF(point),QPointF(self.tree.viewport().mapToGlobal(point)),Qt.RightButton,Qt.RightButton,Qt.NoModifier)
        self.tree.mousePressEvent(event);self.assertEqual(self.selected(),selected)
        d=DeletionDialog(self.w,'web','category',2,9)
        QTimer.singleShot(0,lambda:QTest.keyClick(d,Qt.Key_Return))
        self.assertEqual(d.exec(),QDialog.Rejected)
    def test_twenty_batch_undo_limit(self):
        for n in range(25):
            identifier='extra'+str(n)
            self.w.data['items'].append({'id':identifier,'kind':'web','category':'general','title':identifier,'path':'https://example.com/'+identifier,'note':''})
        self.w.refresh()
        with patch.object(self.w,'confirm_removal',return_value='remove'):
            for n in range(25):
                node=self.node(('item','extra'+str(n)));self.tree.setCurrentItem(node,0,QItemSelectionModel.ClearAndSelect)
                self.w.remove(self.tree)
        self.assertEqual(len(self.w.undo_stack),20)
        for _ in range(20):self.w.undo()
        for n in range(25):self.assertEqual(self.w.find('extra'+str(n)) is not None,n>=5)
    def test_edited_fields_and_selection_survive_title_refresh(self):
        self.click(('item','web-a0'));self.click(('item','web-a1'),Qt.ControlModifier);selected=self.selected()
        self.w.find('web-a0')['title']='New fetched title';self.w.refresh();self.assertEqual(self.selected(),selected)
        self.assertEqual(self.w.active_kind,'web')

if __name__=='__main__':unittest.main(verbosity=2)
