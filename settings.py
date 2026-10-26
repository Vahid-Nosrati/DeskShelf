import copy
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QDialog,QVBoxLayout,QHBoxLayout,QFormLayout,QLabel,QComboBox,QPushButton,
    QDialogButtonBox,QListWidget,QTabWidget,QWidget,QScrollArea,QSlider,QSpinBox,QColorDialog,QFrame)
from core import theme_defaults
from i18n import LANGUAGES
from visuals import PASTELS,NORMAL,ink

class AppearanceDialog(QDialog):
    def __init__(self,window):
        super().__init__(window);self.window=window;self.draft=copy.deepcopy(window.data['theme']);self.loading=False
        self.setWindowTitle(window.t('settings'));self.resize(760,760);self.setMinimumWidth(620)
        self.setLayoutDirection(window.layoutDirection());layout=QVBoxLayout(self);tabs=QTabWidget();layout.addWidget(tabs)
        general=QWidget();g=QVBoxLayout(general);form=QFormLayout();g.addLayout(form)
        self.language=QComboBox()
        for code,name in LANGUAGES.items():self.language.addItem(name,code)
        self.language.setCurrentIndex(self.language.findData(window.data['language']))
        form.addRow(window.t('language'),self.language)
        g.addWidget(QLabel(window.t('order')));self.order=QListWidget()
        for k in window.data['order']:
            self.order.addItem(window.t(k));self.order.item(self.order.count()-1).setData(Qt.UserRole,k)
        g.addWidget(self.order);self.order.setCurrentRow(0)
        row=QHBoxLayout()
        for key,offset in [('up',-1),('down',1)]:
            b=QPushButton(window.t(key));b.clicked.connect(lambda checked=False,o=offset:self.move(o));row.addWidget(b)
        g.addLayout(row);g.addStretch();tabs.addTab(general,window.t('general_settings'))
        scroll=QScrollArea();scroll.setWidgetResizable(True);appearance=QWidget();v=QVBoxLayout(appearance);scroll.setWidget(appearance)
        notice=QLabel(window.t('preview'));notice.setWordWrap(True);v.addWidget(notice)
        form=QFormLayout();v.addLayout(form);self.controls={}
        for key,values in [('style',['flat','raised']),('density',['comfortable','compact']),('palette',['pastel','normal'])]:
            combo=QComboBox()
            for val in values:combo.addItem(window.t(val),val)
            combo.setCurrentIndex(combo.findData(self.draft[key]));combo.currentIndexChanged.connect(lambda n,k=key,c=combo:self.option(k,c.currentData()))
            self.controls[key]=combo;form.addRow(window.t(key),combo)
        presets=QHBoxLayout()
        for key in ['soft','blue','neutral']:
            b=QPushButton(window.t(key));b.clicked.connect(lambda checked=False,k=key:self.preset(k));presets.addWidget(b)
        form.addRow(window.t('presets'),presets)
        note=QLabel(window.t('opacity'));note.setWordWrap(True);v.addWidget(note)
        self.rows={}
        for key in ['canvas','web','folders','files','apps','item','category']:
            frame=QFrame();frame.setObjectName('colorRow');box=QVBoxLayout(frame);top=QHBoxLayout()
            label=window.t('category_border' if key=='category' else key);top.addWidget(QLabel(label),1)
            custom=QPushButton();custom.clicked.connect(lambda checked=False,k=key:self.custom(k));top.addWidget(custom);box.addLayout(top)
            swatches=QHBoxLayout();buttons=[]
            for i in range(8):
                b=QPushButton();b.setFixedSize(29,25);b.clicked.connect(lambda checked=False,k=key,n=i:self.choose(k,n));swatches.addWidget(b);buttons.append(b)
            swatches.addStretch();box.addLayout(swatches)
            r=QHBoxLayout();slider=QSlider(Qt.Horizontal);slider.setRange(0,100);spin=QSpinBox();spin.setRange(0,100);spin.setSuffix('%')
            slider.valueChanged.connect(spin.setValue);spin.valueChanged.connect(slider.setValue)
            spin.valueChanged.connect(lambda val,k=key:self.alpha(k,val));r.addWidget(slider,1);r.addWidget(spin);box.addLayout(r)
            self.rows[key]=(custom,buttons,slider,spin);v.addWidget(frame)
        default=QPushButton(window.t('defaults'));default.clicked.connect(self.defaults);v.addWidget(default);v.addStretch()
        tabs.addTab(scroll,window.t('appearance'))
        buttons=QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText(window.t('ok'));buttons.button(QDialogButtonBox.Cancel).setText(window.t('cancel'))
        buttons.accepted.connect(self.accept);buttons.rejected.connect(self.reject);layout.addWidget(buttons)
        self.sync()
    def move(self,offset):
        n=self.order.currentRow();dest=n+offset
        if 0<=n and 0<=dest<self.order.count():item=self.order.takeItem(n);self.order.insertItem(dest,item);self.order.setCurrentRow(dest)
    def option(self,key,value):
        if self.loading:return
        self.draft[key]=value;self.sync();self.preview()
    def choose(self,key,n):
        palette=PASTELS if self.draft['palette']=='pastel' else NORMAL
        self.draft['colors'][key]=palette[n];self.sync();self.preview()
    def alpha(self,key,value):
        if self.loading:return
        self.draft['opacity'][key]=value;self.preview()
    def custom(self,key):
        c=QColorDialog.getColor(QColor(self.draft['colors'][key]),self,self.window.t('custom'))
        if c.isValid():self.draft['colors'][key]=c.name();self.sync();self.preview()
    def defaults(self):self.draft=theme_defaults();self.sync();self.preview()
    def preset(self,key):
        self.draft=theme_defaults()
        if key=='blue':
            self.draft['colors'].update(canvas='#E4EDF9',web='#C9DDF7',folders='#D6E6F8',files='#DCE9FA',apps='#D5DEF6',item='#6D92C0',category='#557AA9')
        elif key=='neutral':
            self.draft['colors'].update(canvas='#E5E7EB',web='#E2E8F0',folders='#E2E8F0',files='#E2E8F0',apps='#E2E8F0',item='#8591A1',category='#66758A')
        self.sync();self.preview()
    def sync(self):
        self.loading=True
        for k,c in self.controls.items():c.setCurrentIndex(c.findData(self.draft[k]))
        palette=PASTELS if self.draft['palette']=='pastel' else NORMAL
        for key,(custom,buttons,slider,spin) in self.rows.items():
            color=self.draft['colors'][key];custom.setText(color.upper());custom.setToolTip(self.window.t('custom'))
            custom.setStyleSheet(f'background:{color};color:{ink(color).name()};border:1px solid #8290A3;border-radius:5px;padding:5px;')
            for b,value in zip(buttons,palette):
                b.setToolTip(value);b.setAccessibleName(value)
                b.setStyleSheet(f'QPushButton{{background:{value};border:{"2px solid #356BC3" if value.lower()==color.lower() else "1px solid #A0ABBA"};border-radius:5px;}} QPushButton:hover{{border:2px solid #356BC3;}} QPushButton:pressed{{border:3px solid #172338;}}')
            slider.setValue(self.draft['opacity'][key]);spin.setValue(self.draft['opacity'][key])
        self.loading=False
    def preview(self):
        self.window.preview_theme=copy.deepcopy(self.draft);self.window.apply_theme()
    def done(self,result):
        self.window.preview_theme=None;self.window.apply_theme();super().done(result)
