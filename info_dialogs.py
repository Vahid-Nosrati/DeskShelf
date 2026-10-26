"""Searchable offline guide and public project information."""
import html
import sys
from pathlib import Path
import PySide6
from PySide6.QtCore import Qt,QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (QDialog,QVBoxLayout,QHBoxLayout,QTabWidget,QWidget,QLineEdit,
 QListWidget,QTextBrowser,QSplitter,QPushButton)
from i18n import guide,RESOURCE_ROOT
from app_meta import VERSION,app_info,app_root

def safe_link(url):
    u=QUrl(url)
    if u.scheme().lower() in ('https','http','mailto'):QDesktopServices.openUrl(u)

class HelpDialog(QDialog):
    def __init__(self,window):
        super().__init__(window);self.window=window;self.setWindowTitle('DeskShelf — '+window.t('help'))
        self.resize(940,700);self.setMinimumSize(660,440);self.setLayoutDirection(window.layoutDirection())
        layout=QVBoxLayout(self);tabs=QTabWidget();layout.addWidget(tabs)
        page=QWidget();v=QVBoxLayout(page);self.search=QLineEdit();self.search.setPlaceholderText(window.t('help_search'));v.addWidget(self.search)
        split=QSplitter(Qt.Horizontal);self.sections=QListWidget();self.sections.setMinimumWidth(190);self.sections.setMaximumWidth(290)
        self.browser=QTextBrowser();self.browser.setOpenExternalLinks(False);split.addWidget(self.sections);split.addWidget(self.browser);split.setSizes([240,660]);v.addWidget(split)
        tabs.addTab(page,window.t('help'));self.content=guide(window.data['language']);self.visible=[]
        self.sections.currentRowChanged.connect(self.render);self.search.textChanged.connect(self.filter);self.filter()
        about=QTextBrowser();about.setOpenExternalLinks(False);about.anchorClicked.connect(lambda u:safe_link(u.toString()))
        info=app_info();esc=html.escape
        about_html='<h1>DeskShelf</h1><p>'+esc(window.t('version'))+': '+VERSION+'</p><p>'+esc(window.t('author'))+': '+esc(info['author'])+'</p>'
        for key in ('github_profile','repository_url','public_contact'):
            value=info[key]
            if not value:continue
            u=QUrl(value);shown=esc(value)
            if u.scheme() in ('http','https','mailto'):shown='<a href="'+esc(value,quote=True)+'">'+shown+'</a>'
            about_html+='<p>'+esc(window.t(key))+': '+shown+'</p>'
        about_html+='<h2>'+esc(window.t('license'))+'</h2><p>MIT — Copyright (c) 2026 '+esc(info['author'])+'</p>'
        license_path=RESOURCE_ROOT/'LICENSE'
        if license_path.exists():about_html+='<pre style="white-space:pre-wrap">'+esc(license_path.read_text('utf-8'))+'</pre>'
        about_html+='<h2>'+esc(window.t('dependencies'))+'</h2><p>Python '+sys.version.split()[0]+' — PSF License<br>PySide6 / Qt '+PySide6.__version__+' — LGPLv3<br>Shiboken6 — LGPLv3<br>PyInstaller — GPL with bootloader exception (build tool)</p>'
        notice=RESOURCE_ROOT/'THIRD_PARTY_NOTICES.md'
        if notice.exists():about_html+='<pre style="white-space:pre-wrap">'+esc(notice.read_text('utf-8'))+'</pre>'
        about.setHtml(self.wrap(about_html));tabs.addTab(about,window.t('about'))
        row=QHBoxLayout();row.addStretch();close=QPushButton(window.t('close'));close.clicked.connect(self.accept);row.addWidget(close);layout.addLayout(row)
    def wrap(self,body):
        direction='rtl' if self.window.layoutDirection()==Qt.RightToLeft else 'ltr'
        return '<html><body dir="'+direction+'" style="font-size:11pt;color:#172338;background:white;padding:12px">'+body+'</body></html>'
    def filter(self,*args):
        query=self.search.text().strip().casefold();self.sections.blockSignals(True);self.sections.clear();self.visible=[]
        for section in self.content:
            if not query or query in (section['title']+' '+section['body']).casefold():
                self.visible.append(section);self.sections.addItem(section['title'])
        self.sections.blockSignals(False)
        if self.visible:self.sections.setCurrentRow(0);self.render(0)
        else:self.browser.setPlainText(self.window.t('no_results'))
    def render(self,row):
        if not 0<=row<len(self.visible):return
        s=self.visible[row];body='<h2>'+html.escape(s['title'])+'</h2>'
        for paragraph in s['body'].split('\n\n'):body+='<p>'+html.escape(paragraph).replace('\n','<br>')+'</p>'
        self.browser.setHtml(self.wrap(body))
