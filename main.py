import copy
import html
import json
import os
from pathlib import Path
import re
import sys
import uuid
import urllib.request
from concurrent.futures import ThreadPoolExecutor

from PySide6.QtCore import Qt,QTimer,QUrl,QLockFile,QTranslator,QLibraryInfo,QLocale
from PySide6.QtGui import QAction,QKeySequence,QDesktopServices,QIcon,QColor,QPalette
from PySide6.QtWidgets import (QApplication,QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,
 QLineEdit,QTreeWidget,QTreeWidgetItem,QDialog,QDialogButtonBox,QFormLayout,QComboBox,QFileDialog,
 QMessageBox,QPlainTextEdit,QInputDialog,QSplitter,QFrame,QAbstractItemView)
from core import KINDS,Store,validate
from i18n import text,RTL_LANGUAGES
from app_meta import VERSION,app_root
from info_dialogs import HelpDialog
from visuals import logo,icon,blend,ink,CardDelegate
from settings import AppearanceDialog


def tooltip(title,path,note=''):
    return '<html><b>'+html.escape(title)+'</b><p dir="ltr">'+html.escape(path)+'</p><p>'+html.escape(note).replace('\n','<br>')+'</p></html>'

class Column(QTreeWidget):
    def __init__(self,window,kind):
        super().__init__();self.window=window;self.kind=kind;self.setHeaderHidden(True)
        self.setAcceptDrops(True);self.setMouseTracking(True);self.viewport().setMouseTracking(True)
        self.setRootIsDecorated(False);self.setIndentation(13);self.setExpandsOnDoubleClick(False)
        self.setUniformRowHeights(False);self.setAnimated(False);self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff);self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setFrameShape(QFrame.NoFrame);self.setItemDelegate(CardDelegate(window,self))
        self.itemDoubleClicked.connect(lambda node,col:window.open_item(node))
        self.itemClicked.connect(self.clicked_node)
        self.itemCollapsed.connect(lambda node:self.remember(node,True));self.itemExpanded.connect(lambda node:self.remember(node,False))
        self.itemSelectionChanged.connect(lambda:window.update_buttons(self))
        self.empty=QLabel(self);self.empty.setAlignment(Qt.AlignCenter);self.empty.setWordWrap(True)
        self.empty.setAttribute(Qt.WA_TransparentForMouseEvents);self.empty.setObjectName('emptyHint')
        self.setContextMenuPolicy(Qt.ActionsContextMenu)
        for key,fn in [('add',lambda:window.edit(kind)),('edit',lambda:window.edit_selected(self)),('rename',lambda:window.rename_category(self)),('delete',lambda:window.remove(self))]:
            a=QAction(window.t(key),self);a.triggered.connect(fn);self.addAction(a)
    def resizeEvent(self,e):
        super().resizeEvent(e);self.empty.setGeometry(self.rect().adjusted(15,60,-15,-20))
    def clicked_node(self,node,col):
        if node.data(0,Qt.UserRole)[0]=='category':node.setExpanded(not node.isExpanded())
    def remember(self,node,collapsed):
        if self.signalsBlocked():return
        self.window.data['collapsed'][self.kind+':'+node.data(0,Qt.UserRole)[1]]=collapsed;self.window.save()
    def keyPressEvent(self,e):
        if e.key() in (Qt.Key_Return,Qt.Key_Enter):
            node=self.currentItem()
            if node and node.data(0,Qt.UserRole)[0]=='category':node.setExpanded(not node.isExpanded())
            else:self.window.open_item(node)
            return
        if e.key()==Qt.Key_Delete:self.window.remove(self);return
        if e.key()==Qt.Key_F2:self.window.edit_selected(self);return
        super().keyPressEvent(e)
    def dragEnterEvent(self,e):
        if e.mimeData().hasUrls() or e.mimeData().hasText():
            self.setProperty('dropActive',True);self.style().unpolish(self);self.style().polish(self);e.acceptProposedAction()
    def dragMoveEvent(self,e):e.acceptProposedAction()
    def reset_drop(self):self.setProperty('dropActive',False);self.style().unpolish(self);self.style().polish(self)
    def dragLeaveEvent(self,e):self.reset_drop();e.accept()
    def dropEvent(self,e):
        self.reset_drop()
        values=[u.toLocalFile() if u.isLocalFile() else u.toString() for u in e.mimeData().urls()]
        if not values:values=[e.mimeData().text().strip()]
        for value in values:
            if value:self.window.edit(self.kind,prefill=value)
        e.acceptProposedAction()

class EntryDialog(QDialog):
    def __init__(self,window,kind,entry=None,prefill='',category=None):
        super().__init__(window);self.window=window;self.kind=kind;self.entry=entry
        self.setWindowTitle(window.t('edit' if entry else 'add')+' — '+window.t(kind));self.resize(650,440)
        self.setLayoutDirection(window.layoutDirection());layout=QFormLayout(self);layout.setContentsMargins(22,22,22,22);layout.setSpacing(12)
        self.category=QComboBox()
        for c in window.data['categories'][kind]:self.category.addItem(window.cat_name(c),c['id'])
        if category:self.category.setCurrentIndex(self.category.findData(category))
        layout.addRow(window.t('category'),self.category)
        if kind!='web':
            b=QPushButton(window.t('browse'));b.setIcon(icon(kind));b.clicked.connect(self.browse);layout.addRow(b)
        self.title=QLineEdit();self.path=QLineEdit();self.path.setLayoutDirection(Qt.LeftToRight);self.path.setAlignment(Qt.AlignLeft)
        self.note=QPlainTextEdit();self.note.setPlaceholderText(window.t('note_hint'));self.note.setMaximumHeight(105)
        for key,field in [('title',self.title),('path',self.path)]:
            row=QHBoxLayout();row.addWidget(field,1);b=QPushButton();b.setIcon(icon('copy'));b.setFixedWidth(36);b.setToolTip(window.t('copy'));b.setAccessibleName(window.t('copy'))
            b.clicked.connect(lambda checked=False,f=field:self.copy(f));row.addWidget(b);layout.addRow(window.t(key),row)
        layout.addRow(window.t('note'),self.note)
        if kind=='web':
            label=QLabel(window.t('fetch'));label.setWordWrap(True);layout.addRow(label)
        buttons=QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText(window.t('ok'));buttons.button(QDialogButtonBox.Cancel).setText(window.t('cancel'))
        buttons.accepted.connect(self.check);buttons.rejected.connect(self.reject);layout.addRow(buttons)
        if entry:
            self.title.setText(entry['title']);self.path.setText(entry['path']);self.note.setPlainText(entry['note']);self.category.setCurrentIndex(self.category.findData(entry['category']))
        elif prefill:self.set_path(prefill)
    def copy(self,field):
        QApplication.clipboard().setText(field.text());self.window.statusBar().showMessage(self.window.t('copied'),1800)
    def set_path(self,p):
        self.path.setText(p)
        if self.kind!='web':self.title.setText(Path(p).name)
    def browse(self):
        current=self.path.text()
        if self.kind=='folders':p=QFileDialog.getExistingDirectory(self,self.window.t('browse'),current)
        else:
            filters=self.window.t('program_filter')+' (*.exe *.lnk *.url *.bat *.cmd);;'+self.window.t('all_files')+' (*)' if self.kind=='apps' else self.window.t('all_files')+' (*)'
            p,_=QFileDialog.getOpenFileName(self,self.window.t('browse'),current,filters)
        if p:self.set_path(os.path.normpath(p))
    def check(self):
        p=self.path.text().strip();error=''
        if not p:error=self.window.t('required')
        elif self.kind=='web':
            url=QUrl(p)
            if not url.isValid() or url.scheme().lower() not in ('http','https') or not url.host():error=self.window.t('url_error')
        elif not (Path(p).is_dir() if self.kind=='folders' else Path(p).is_file()):error=self.window.t('missing')
        if not error:
            for item in self.window.data['items']:
                same=item['path']==p if self.kind=='web' else os.path.normcase(os.path.abspath(item['path']))==os.path.normcase(os.path.abspath(p))
                if item['kind']==self.kind and same and (not self.entry or item['id']!=self.entry['id']):
                    c=next(c for c in self.window.data['categories'][self.kind] if c['id']==item['category']);error=self.window.t('duplicate')+self.window.cat_name(c);break
        if error:QMessageBox.warning(self,self.window.t('error'),error);return
        self.value={'id':self.entry['id'] if self.entry else uuid.uuid4().hex,'kind':self.kind,'category':self.category.currentData(),
                    'title':self.title.text().strip(),'path':p,'note':self.note.toPlainText()}
        self.accept()

def fetch_title(url):
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'DeskShelf/0.3'})
        with urllib.request.urlopen(req,timeout=8) as response:
            if 'html' not in response.headers.get('Content-Type',''):return ''
            body=response.read(512000).decode(response.headers.get_content_charset() or 'utf-8',errors='replace')
        m=re.search(r'<title\b[^>]*>(.*?)</title\s*>',body,re.I|re.S)
        return re.sub(r'\s+',' ',html.unescape(m.group(1))).strip()[:500] if m else ''
    except Exception:return ''

class Main(QMainWindow):
    def __init__(self,store):
        super().__init__();self.store=store;self.data=store.data;self.preview_theme=None;self.undo_stack=[]
        self.pool=ThreadPoolExecutor(max_workers=3);self.pending=[];self.columns={};self.panels={};self.buttons={};self.save_failed=False
        self.resize(1360,790);self.setMinimumSize(920,520);self.setWindowIcon(QIcon(logo()));self.setWindowTitle('DeskShelf')
        self.timer=QTimer(self);self.timer.timeout.connect(self.poll);self.timer.start(250)
        for key,shortcut,fn in [('search','Ctrl+F',lambda:self.search.setFocus()),('undo','Ctrl+Z',self.undo),('help','F1',self.help)]:
            a=QAction(self.t(key),self);a.setShortcut(QKeySequence(shortcut));a.triggered.connect(fn);self.addAction(a)
        self.build()
    def install_qt_language(self):
        app=QApplication.instance()
        if hasattr(self,'qt_translator'):app.removeTranslator(self.qt_translator)
        self.qt_translator=QTranslator(self)
        code=self.data['language']
        QLocale.setDefault(QLocale(code))
        self.qt_translator.load(QLocale(code),'qtbase','_',QLibraryInfo.path(QLibraryInfo.TranslationsPath))
        app.installTranslator(self.qt_translator)
    def t(self,key):return text(key,self.data['language'])
    def cat_name(self,c):return self.t('general') if c['id']=='general' else c['name']
    def theme(self):return self.preview_theme or self.data['theme']
    def canvas_color(self):return blend(self.theme()['colors']['canvas'],'#FFFFFF',self.theme()['opacity']['canvas'])
    def column_color(self,kind):return blend(self.theme()['colors'][kind],self.canvas_color(),self.theme()['opacity'][kind])
    def save(self):
        self.store.data=self.data
        try:self.store.save();self.save_failed=False;return True
        except Exception as e:
            self.save_failed=True;QMessageBox.critical(self,self.t('error'),self.t('save_error')+'\n'+str(e));return False
    def build(self):
        self.install_qt_language()
        self.setLayoutDirection(Qt.RightToLeft if self.data['language'] in RTL_LANGUAGES else Qt.LeftToRight)
        root=QWidget();root.setObjectName('root');v=QVBoxLayout(root);v.setContentsMargins(18,16,18,8);v.setSpacing(15);self.setCentralWidget(root)
        toolbar=QFrame();toolbar.setObjectName('toolbar');top=QHBoxLayout(toolbar);top.setContentsMargins(13,10,13,10);top.setSpacing(10)
        mark=QLabel();mark.setPixmap(logo(38));top.addWidget(mark);brand=QLabel('DeskShelf');brand.setObjectName('brand');top.addWidget(brand)
        self.search=QLineEdit();self.search.setClearButtonEnabled(True);self.search.setPlaceholderText(self.t('search'));self.search.addAction(icon('search'),QLineEdit.LeadingPosition)
        self.search.setMaximumWidth(880);self.search.textChanged.connect(self.refresh);top.addWidget(self.search,1);top.addStretch(0)
        for key,fn in [('undo',self.undo),('export',self.export),('restore',self.restore),('help',self.help),('settings',self.settings)]:
            b=QPushButton();b.setIcon(icon(key));b.setFixedSize(38,36);b.setToolTip(self.t(key));b.setAccessibleName(self.t(key));b.clicked.connect(fn);top.addWidget(b)
        v.addWidget(toolbar);self.splitter=QSplitter(Qt.Horizontal);self.splitter.setChildrenCollapsible(False);self.splitter.setHandleWidth(12);v.addWidget(self.splitter,1)
        self.columns={};self.panels={};self.buttons={}
        for kind in self.data['order']:
            panel=QFrame();panel.setObjectName('panel_'+kind);panel.setMinimumWidth(185);panel.setAttribute(Qt.WA_StyledBackground)
            box=QVBoxLayout(panel);box.setContentsMargins(9,11,9,8);box.setSpacing(8)
            header=QHBoxLayout();header.setSpacing(3);kind_icon=QLabel();kind_icon.setObjectName('kindIcon_'+kind);header.addWidget(kind_icon)
            label=QLabel(self.t(kind));label.setObjectName('heading_'+kind);header.addWidget(label,1)
            tree=Column(self,kind);self.columns[kind]=tree;self.panels[kind]=panel;self.buttons[kind]={}
            for name,key,fn in [('add','add',lambda checked=False,k=kind:self.edit(k)),('category','new_category',lambda checked=False,k=kind:self.new_category(k)),('edit','edit',lambda checked=False,t=tree:self.edit_selected(t)),('delete','delete',lambda checked=False,t=tree:self.remove(t))]:
                b=QPushButton();b.setIcon(icon(name));b.setFixedSize(29,30);b.setToolTip(self.t(key));b.setAccessibleName(self.t(key));b.clicked.connect(fn);header.addWidget(b);self.buttons[kind][name]=b
            box.addLayout(header);box.addWidget(tree,1);self.splitter.addWidget(panel)
        self.splitter.setSizes(self.data['widths'] or [310]*4);self.splitter.splitterMoved.connect(self.widths_changed)
        self.statusBar().showMessage(self.t('ready'));self.apply_theme();self.refresh()
    def apply_theme(self):
        th=self.theme();canvas=self.canvas_color();fg=ink(canvas).name()
        qss=f'''
        QWidget {{ font-family:"Segoe UI","Tahoma"; font-size:10pt; }}
        QMainWindow,QWidget#root {{ background:{canvas.name()}; }}
        QLabel#brand {{ font-size:19pt; font-weight:700; color:#172338; }}
        QFrame#toolbar {{ background:#FFFFFF; border:1px solid #DCE3ED; border-radius:13px; }}
        QDialog {{ background:#F4F6FA; color:#172338; }}
        QDialog QLabel {{ color:#172338; }}
        QLineEdit,QPlainTextEdit,QComboBox,QSpinBox,QListWidget {{ background:#FFFFFF; color:#172338; border:1px solid #C7D2E2; border-radius:6px; padding:6px; selection-background-color:#D5E4FC; selection-color:#172338; }}
        QLineEdit:focus,QPlainTextEdit:focus,QComboBox:focus,QSpinBox:focus {{ border:1px solid #3977C9; }}
        QPushButton {{ background:#FFFFFF; color:#263D5C; border:1px solid #C6D1E0; border-radius:6px; padding:5px 9px; }}
        QPushButton:hover {{ background:#E7F0FF; border:1px solid #6D97CF; }}
        QPushButton:pressed {{ background:#C8DBF5; border:1px solid #356BC3; padding-top:7px; padding-bottom:3px; }}
        QPushButton:focus {{ border:2px solid #356BC3; }}
        QPushButton:disabled {{ background:#EDF0F4; border-color:#DCE1E9; color:#9CA7B7; }}
        QTreeWidget {{ background:transparent; border:1px solid transparent; outline:none; padding:0; }}
        QTreeWidget[dropActive="true"] {{ border:2px dashed #356BC3; border-radius:9px; background:rgba(210,230,255,90); }}
        QTreeWidget::branch {{ background:transparent; border-image:none; image:none; }}
        QScrollBar:vertical {{ background:transparent; width:9px; margin:1px; }}
        QScrollBar::handle:vertical {{ background:#A0AFC4; min-height:32px; border-radius:4px; }}
        QScrollBar::handle:vertical:hover {{ background:#6F89AD; }}
        QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical {{ height:0px; }}
        QScrollBar::add-page:vertical,QScrollBar::sub-page:vertical {{ background:transparent; }}
        QSplitter::handle {{ background:transparent; }}
        QSplitter::handle:hover {{ background:#B4C9E5; border-radius:5px; }}
        QStatusBar {{ color:{fg}; background:transparent; }}
        QToolTip {{ background:#233751; color:#FFFFFF; border:0; padding:8px; }}
        QFrame#colorRow {{ background:#FFFFFF; border:1px solid #DEE5EF; border-radius:9px; }}
        QTabWidget::pane {{ border:1px solid #D3DCE9; border-radius:8px; }}
        QTabBar::tab {{ padding:9px 20px; background:#E8EDF5; color:#263D5C; }}
        QTabBar::tab:selected {{ background:#FFFFFF; border-bottom:2px solid #356BC3; }}
        QSlider::groove:horizontal {{ height:5px; background:#D8E1EF; border-radius:2px; }}
        QSlider::handle:horizontal {{ width:14px; margin:-5px 0; background:#507FBF; border-radius:7px; }}
        '''
        for kind,panel in self.panels.items():
            color=self.column_color(kind);heading_ink=ink(color).name()
            qss+=f'QFrame#panel_{kind} {{ background:{color.name()}; border:1px solid {blend("#627A99",color,22).name()}; border-radius:13px; }} '
            qss+=f'QLabel#heading_{kind} {{ color:{heading_ink}; font-weight:600; }} '
            panel.findChild(QLabel,'kindIcon_'+kind).setPixmap(icon(kind,heading_ink,21).pixmap(21,21))
            # Draw depth without a widget graphics effect: effects can alter inherited RTL painting.
            if th['style']=='raised':
                qss+=f'QFrame#panel_{kind} {{ border-top:2px solid #FFFFFF; border-bottom:4px solid {blend("#526987",color,42).name()}; border-right:2px solid {blend("#526987",color,25).name()}; }} '
            tree=self.columns[kind];tree.empty.setStyleSheet(f'color:{heading_ink};background:transparent;border:none;')
            tree.doItemsLayout();tree.viewport().update()
        self.setStyleSheet(qss)
    def widths_changed(self,*args):self.data['widths']=self.splitter.sizes();self.save()
    def refresh(self,*args):
        query=self.search.text().strip().casefold()
        for kind,tree in self.columns.items():
            selected=tree.currentItem().data(0,Qt.UserRole) if tree.currentItem() else None;scroll=tree.verticalScrollBar().value()
            tree.blockSignals(True);tree.clear();visible=0
            for c in self.data['categories'][kind]:
                name=self.cat_name(c);items=[i for i in self.data['items'] if i['kind']==kind and i['category']==c['id']]
                matches=[i for i in items if not query or query in ' '.join([i['title'],i['path'],i['note'],name]).casefold()]
                group=QTreeWidgetItem([name+'  ·  '+str(len(matches))]);group.setData(0,Qt.UserRole,('category',c['id']));group.setToolTip(0,name);tree.addTopLevelItem(group)
                if selected==('category',c['id']):tree.setCurrentItem(group)
                for item in matches:
                    child=QTreeWidgetItem([item['title'] or item['path']]);child.setData(0,Qt.UserRole,('item',item['id']))
                    child.setToolTip(0,tooltip(item['title'] or item['path'],item['path'],item['note']));group.addChild(child)
                    if selected==('item',item['id']):tree.setCurrentItem(child)
                group.setExpanded(bool(query) or not self.data['collapsed'].get(kind+':'+c['id'],False))
                group.setHidden(bool(query) and not matches);visible+=len(matches)
            tree.empty.setText(self.t('no_results') if query else self.t('empty'))
            tree.empty.setVisible(visible==0);tree.empty.raise_();tree.blockSignals(False);tree.verticalScrollBar().setValue(scroll);self.update_buttons(tree)
    def update_buttons(self,tree):
        selected=self.selected(tree);enabled=bool(selected and selected!=('category','general'))
        if tree.kind in self.buttons:
            self.buttons[tree.kind]['edit'].setEnabled(enabled);self.buttons[tree.kind]['delete'].setEnabled(enabled)
    def question(self,title,message):
        box=QMessageBox(self);box.setWindowTitle(title);box.setText(message);box.setIcon(QMessageBox.Question)
        box.setStandardButtons(QMessageBox.Yes|QMessageBox.No)
        box.button(QMessageBox.Yes).setText(self.t('ok'));box.button(QMessageBox.No).setText(self.t('cancel'))
        box.setDefaultButton(QMessageBox.No);return box.exec()
    def input_name(self,title,value=''):
        dialog=QInputDialog(self);dialog.setWindowTitle(title);dialog.setLabelText(self.t('title'));dialog.setTextValue(value)
        dialog.setOkButtonText(self.t('ok'));dialog.setCancelButtonText(self.t('cancel'))
        accepted=dialog.exec()==QDialog.Accepted
        return dialog.textValue(),accepted
    def selected(self,tree):return tree.currentItem().data(0,Qt.UserRole) if tree.currentItem() else None
    def find(self,id):return next((i for i in self.data['items'] if i['id']==id),None)
    def edit_selected(self,tree):
        sel=self.selected(tree)
        if sel and sel[0]=='item':self.edit(tree.kind,self.find(sel[1]))
        elif sel:self.rename_category(tree)
    def edit(self,kind,entry=None,prefill=''):
        selected=self.selected(self.columns[kind]);cat=selected[1] if selected and selected[0]=='category' else None
        dialog=EntryDialog(self,kind,entry,prefill,cat)
        if dialog.exec()!=QDialog.Accepted:return
        value=dialog.value
        if entry:entry.update(value)
        else:self.data['items'].append(value)
        if kind=='web' and not value['title']:self.pending.append((value['id'],value['path'],self.pool.submit(fetch_title,value['path'])))
        self.save();self.refresh()
    def poll(self):
        for id,url,future in self.pending[:]:
            if future.done():
                self.pending.remove((id,url,future));title=future.result();item=self.find(id)
                if item and item['path']==url and not item['title'] and title:item['title']=title;self.save();self.refresh()
    def new_category(self,kind):
        name,ok=self.input_name(self.t('new_category'))
        if not ok or not name.strip():return
        name=name.strip()
        if name.casefold() in [self.cat_name(c).casefold() for c in self.data['categories'][kind]]:QMessageBox.warning(self,self.t('error'),self.t('category_exists'));return
        self.data['categories'][kind].append({'id':uuid.uuid4().hex,'name':name});self.save();self.refresh()
    def rename_category(self,tree):
        sel=self.selected(tree)
        if not sel or sel[0]!='category' or sel[1]=='general':return
        c=next(c for c in self.data['categories'][tree.kind] if c['id']==sel[1]);name,ok=self.input_name(self.t('rename'),c['name'])
        if not ok or not name.strip():return
        if name.strip().casefold() in [self.cat_name(v).casefold() for v in self.data['categories'][tree.kind] if v!=c]:QMessageBox.warning(self,self.t('error'),self.t('category_exists'));return
        c['name']=name.strip();self.save();self.refresh()
    def remove(self,tree):
        sel=self.selected(tree)
        if not sel or sel==('category','general'):return
        key='confirm' if sel[0]=='item' else 'delete_category'
        if self.question(self.t('delete'),self.t(key))!=QMessageBox.Yes:return
        if sel[0]=='item':
            item=self.find(sel[1]);self.undo_stack.append(('item',copy.deepcopy(item)));self.data['items'].remove(item)
        else:
            c=next(c for c in self.data['categories'][tree.kind] if c['id']==sel[1]);affected=[]
            for item in self.data['items']:
                if item['kind']==tree.kind and item['category']==c['id']:affected.append(item['id']);item['category']='general'
            self.undo_stack.append(('category',tree.kind,copy.deepcopy(c),affected));self.data['categories'][tree.kind].remove(c)
        self.undo_stack=self.undo_stack[-20:];self.save();self.refresh()
    def undo(self):
        if not self.undo_stack:return
        action=self.undo_stack.pop()
        if action[0]=='item':
            item=action[1]
            if item['category'] not in [c['id'] for c in self.data['categories'][item['kind']]]:item['category']='general'
            if not self.find(item['id']):self.data['items'].append(item)
        else:
            _,kind,category,ids=action
            if category['id'] not in [c['id'] for c in self.data['categories'][kind]]:
                if category['name'].casefold() in [self.cat_name(c).casefold() for c in self.data['categories'][kind]]:category['name']+=' ('+self.t('recovered')+')'
                self.data['categories'][kind].append(category)
            for id in ids:
                item=self.find(id)
                if item and item['category']=='general':item['category']=category['id']
        self.save();self.refresh()
    def open_item(self,node):
        if not node:return
        typ,id=node.data(0,Qt.UserRole)
        if typ!='item':return
        item=self.find(id)
        try:
            if item['kind']=='web':
                if not QDesktopServices.openUrl(QUrl(item['path'])):raise OSError(self.t('launch_error'))
            elif not Path(item['path']).exists():raise OSError(self.t('missing'))
            elif sys.platform=='win32':os.startfile(item['path'])
            elif not QDesktopServices.openUrl(QUrl.fromLocalFile(item['path'])):raise OSError(self.t('launch_error'))
        except Exception as e:QMessageBox.warning(self,self.t('error'),str(e))
    def export(self):
        path,_=QFileDialog.getSaveFileName(self,self.t('export'),'DeskShelf-backup.json','JSON (*.json)')
        if path:
            try:Path(path).write_text(json.dumps(self.data,ensure_ascii=False,indent=2),'utf-8')
            except Exception as e:QMessageBox.critical(self,self.t('error'),str(e))
    def restore(self):
        path,_=QFileDialog.getOpenFileName(self,self.t('restore'),'','JSON (*.json)')
        if not path:return
        try:new=validate(json.loads(Path(path).read_text('utf-8')))
        except Exception as e:QMessageBox.warning(self,self.t('error'),str(e));return
        if self.question(self.t('restore'),self.t('restore_confirm'))==QMessageBox.Yes:
            self.data=new;self.undo_stack=[];self.save();self.build()
    def help(self):
        HelpDialog(self).exec()
    def settings(self):
        dialog=AppearanceDialog(self)
        if dialog.exec()==QDialog.Accepted:
            self.data['theme']=copy.deepcopy(dialog.draft);self.data['language']=dialog.language.currentData()
            self.data['order']=[dialog.order.item(i).data(Qt.UserRole) for i in range(dialog.order.count())]
            self.save();self.build()
    def closeEvent(self,event):
        self.data['widths']=self.splitter.sizes()
        if not self.save() and self.question(self.t('error'),self.t('close_unsaved'))!=QMessageBox.Yes:event.ignore();return
        self.timer.stop();self.pool.shutdown(wait=False,cancel_futures=True);event.accept()

def main():
    if sys.platform=='win32':
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('DeskShelf.Desktop')
    app=QApplication(sys.argv);app.setApplicationName('DeskShelf');app.setOrganizationName('DeskShelf');app.setStyle('Fusion');app.setWindowIcon(QIcon(logo()))
    # Use a stable light system palette; contrast is controlled explicitly for colored surfaces.
    palette=QPalette();palette.setColor(QPalette.Window,QColor('#F4F6FA'));palette.setColor(QPalette.WindowText,QColor('#172338'))
    palette.setColor(QPalette.Base,QColor('#FFFFFF'));palette.setColor(QPalette.Text,QColor('#172338'));palette.setColor(QPalette.ButtonText,QColor('#263D5C'));app.setPalette(palette)
    base=app_root()
    try:
        root=base/'data';root.mkdir(parents=True,exist_ok=True)
        lock=QLockFile(str(root/'DeskShelf.lock'))
        if not lock.tryLock(0):
            try:language=json.loads((root/'data.json').read_text('utf-8')).get('language','en')
            except (OSError,ValueError,AttributeError):language='en'
            QMessageBox.information(None,'DeskShelf',text('app_running',language));return 0
        store=Store(root)
    except Exception as e:QMessageBox.critical(None,'DeskShelf',text('startup_error','en')+'\n'+str(e));return 1
    window=Main(store);window.show();result=app.exec();lock.unlock();return result

if __name__=='__main__':sys.exit(main())
