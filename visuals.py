"""Code-native vector icons and a rounded, accessible tree-card delegate."""
from PySide6.QtCore import Qt, QRectF, QSize, QPointF
from PySide6.QtGui import QColor, QPainter, QPen, QIcon, QPixmap, QFont, QLinearGradient, QTextOption, QPolygonF
from PySide6.QtWidgets import QStyledItemDelegate, QStyle

PASTELS=['#D9E8FC','#DDF2E7','#FBEACF','#EBE0FA','#F7DDE6','#D7EFF2','#E5E7EB','#FFFFFF']
NORMAL=['#2563EB','#059669','#D97706','#7C3AED','#DC2626','#0891B2','#475569','#111827']

def blend(fg,bg,opacity):
    a=opacity/100;f=QColor(fg);b=QColor(bg)
    return QColor(round(f.red()*a+b.red()*(1-a)),round(f.green()*a+b.green()*(1-a)),round(f.blue()*a+b.blue()*(1-a)))

def ink(bg):
    c=QColor(bg)
    channels=[c.redF(),c.greenF(),c.blueF()]
    vals=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in channels]
    lum=sum(x*w for x,w in zip(vals,[.2126,.7152,.0722]))
    dark_lum=0.0167
    if (lum+.05)/(dark_lum+.05)>=4.5:return QColor('#172338')
    if 1.05/(lum+.05)>=4.5:return QColor('#FFFFFF')
    return QColor('#000000')

def logo(size=256):
    pix=QPixmap(size,size);pix.fill(Qt.transparent);p=QPainter(pix);p.setRenderHint(QPainter.Antialiasing)
    p.scale(size/256,size/256);p.setPen(Qt.NoPen);p.setBrush(QColor('#263957'));p.drawRoundedRect(QRectF(4,4,248,248),54,54)
    for x,y,color in [(39,40,'#AED1FA'),(137,40,'#BCE7CF'),(39,137,'#F5D3A1'),(137,137,'#D7C0F2')]:
        p.setBrush(QColor(color));p.drawRoundedRect(QRectF(x,y,80,80),17,17)
        p.setPen(QPen(QColor('#FFFFFF'),6,Qt.SolidLine,Qt.RoundCap));p.drawLine(QPointF(x+19,y+28),QPointF(x+60,y+28));p.drawLine(QPointF(x+19,y+47),QPointF(x+47,y+47));p.setPen(Qt.NoPen)
    p.end();return pix

def icon(name,color='#344660',size=24):
    pix=QPixmap(size,size);pix.fill(Qt.transparent);p=QPainter(pix);p.setRenderHint(QPainter.Antialiasing);p.scale(size/24,size/24)
    p.setPen(QPen(QColor(color),1.8,Qt.SolidLine,Qt.RoundCap,Qt.RoundJoin));p.setBrush(Qt.NoBrush)
    def line(x,y,X,Y):p.drawLine(QPointF(x,y),QPointF(X,Y))
    if name in ('up','down'):
        # Short shaft and a filled triangular head.
        if name=='up':
            line(12,11,12,19)
            points=[QPointF(12,4),QPointF(6,11),QPointF(18,11)]
        else:
            line(12,5,12,13)
            points=[QPointF(12,20),QPointF(6,13),QPointF(18,13)]
        p.setPen(Qt.NoPen);p.setBrush(QColor(color));p.drawPolygon(QPolygonF(points))
    elif name in ('help','about'):
        p.drawEllipse(QRectF(3,3,18,18))
        if name=='help':
            p.drawArc(QRectF(8,6,8,7),-20*16,220*16);line(12,13,12,15);p.drawPoint(QPointF(12,18))
        else:line(12,11,12,18);p.drawPoint(QPointF(12,7))
    elif name=='add':line(12,5,12,19);line(5,12,19,12)
    elif name=='category':
        p.drawRoundedRect(QRectF(3,7,18,14),2,2);line(3,7,3,4);line(3,4,10,4);line(10,4,13,7);line(12,11,12,17);line(9,14,15,14)
    elif name=='edit':
        line(5,15,16,4);line(16,4,20,8);line(20,8,9,19);line(9,19,4,20);line(4,20,5,15);line(13,7,17,11)
    elif name=='delete':
        line(4,6,20,6);line(9,3,15,3);line(6,6,7,21);line(7,21,17,21);line(17,21,18,6);line(10,10,10,17);line(14,10,14,17)
    elif name=='copy':p.drawRoundedRect(QRectF(8,7,12,14),2,2);line(15,4,4,4);line(4,4,4,17)
    elif name=='search':p.drawEllipse(QRectF(4,3,12,12));line(14,14,21,21)
    elif name=='settings':
        for y,x in [(6,9),(12,16),(18,7)]:line(3,y,21,y);p.setBrush(QColor('#FFFFFF'));p.drawEllipse(QPointF(x,y),2.4,2.4);p.setBrush(Qt.NoBrush)
    elif name=='undo':line(9,5,4,10);line(4,10,9,15);line(4,10,14,10);p.drawArc(QRectF(9,10,11,10),-100*16,190*16)
    elif name in ['export','restore']:
        p.drawRoundedRect(QRectF(4,14,16,7),2,2);line(12,3,12,14)
        if name=='export':line(8,7,12,3);line(12,3,16,7)
        else:line(8,10,12,14);line(12,14,16,10)
    elif name=='web':
        p.drawEllipse(QRectF(3,3,18,18));p.drawEllipse(QRectF(8,3,8,18));line(3,12,21,12)
    elif name in ['folders','folder']:
        p.drawRoundedRect(QRectF(3,7,18,14),2,2);line(3,7,3,4);line(3,4,10,4);line(10,4,13,7)
    elif name=='files':
        p.drawRoundedRect(QRectF(5,3,14,18),2,2);line(9,9,15,9);line(9,13,15,13);line(9,17,13,17)
    elif name=='apps':
        p.drawRoundedRect(QRectF(3,4,18,16),2,2);line(3,9,21,9);p.drawEllipse(QPointF(6,6.5),.4,.4);p.drawEllipse(QPointF(9,6.5),.4,.4)
    elif name=='note':
        p.drawRoundedRect(QRectF(5,4,14,17),2,2);line(8,9,16,9);line(8,13,16,13);line(8,17,13,17)
    p.end();return QIcon(pix)

class CardDelegate(QStyledItemDelegate):
    def __init__(self,window,tree):super().__init__(tree);self.window=window;self.tree=tree
    def sizeHint(self,option,index):
        group=index.data(Qt.UserRole)[0]=='category'
        compact=self.window.theme()['density']=='compact'
        return QSize(100,(38 if group else 40) if compact else (48 if group else 58))
    def paint(self,painter,option,index):
        painter.save();painter.setRenderHint(QPainter.Antialiasing)
        group,id=index.data(Qt.UserRole);is_group=group=='category';th=self.window.theme()
        bg=self.window.column_color(self.tree.kind)
        r=QRectF(option.rect).adjusted(5,3,-7,-9)
        selected=bool(option.state & QStyle.State_Selected);hover=bool(option.state & QStyle.State_MouseOver)
        key='category' if is_group else 'item'
        edge=QColor(th['colors'][key]);edge.setAlphaF(th['opacity'][key]/100)
        # Border opacity never changes text opacity. Readable card surfaces are intentional.
        surface=blend('#FFFFFF',bg,45 if is_group else 91)
        if hover:surface=blend('#D8E6FA',surface,35)
        if selected:surface=QColor('#E7F0FF')
        if th['style']=='raised':
            painter.setPen(Qt.NoPen)
            for offset,alpha in [(5,18),(3,28),(1,34)]:
                painter.setBrush(QColor(22,38,60,alpha));painter.drawRoundedRect(r.translated(0,offset),9,9)
        painter.setPen(QPen(QColor('#356BC3') if selected else edge,2 if selected else 1.3))
        if th['style']=='raised':
            gradient=QLinearGradient(r.topLeft(),r.bottomLeft());gradient.setColorAt(0,blend('#FFFFFF',surface,70));gradient.setColorAt(1,blend('#7E95B3',surface,13));painter.setBrush(gradient)
        else:painter.setBrush(surface)
        painter.drawRoundedRect(r,8,8)
        if th['style']=='raised':
            painter.setPen(QPen(QColor(255,255,255,170),1));painter.drawLine(QPointF(r.left()+10,r.top()+2),QPointF(r.right()-10,r.top()+2))
        rtl=self.window.layoutDirection()==Qt.RightToLeft
        painter.setLayoutDirection(self.window.layoutDirection())
        leading=r.right()-17 if rtl else r.left()+17
        if is_group:
            c=ink(surface);painter.setPen(QPen(c,1.8,Qt.SolidLine,Qt.RoundCap))
            y=r.center().y();expanded=self.tree.isExpanded(index)
            if expanded:
                painter.drawLine(QPointF(leading-4,y-2),QPointF(leading,y+2));painter.drawLine(QPointF(leading,y+2),QPointF(leading+4,y-2))
            else:
                delta=-1 if rtl else 1
                painter.drawLine(QPointF(leading-2*delta,y-4),QPointF(leading+2*delta,y));painter.drawLine(QPointF(leading+2*delta,y),QPointF(leading-2*delta,y+4))
        else:
            ic=icon(self.tree.kind,'#536C8A',20);ic.paint(painter,int(leading-10),int(r.center().y()-10),20,20)
        text_rect=r.adjusted(35 if not rtl else 12,0,-35 if rtl else -12,0)
        font=QFont(option.font);font.setBold(is_group);painter.setFont(font)
        painter.setPen(ink(surface));value=index.data(Qt.DisplayRole) or ''
        align=(Qt.AlignRight if rtl else Qt.AlignLeft)|Qt.AlignVCenter
        if not is_group:
            item=self.window.find(id)
            if item and not item['title']:
                align=Qt.AlignLeft|Qt.AlignVCenter
            if item and item['note']:
                hint_rect=QRectF(text_rect)
                if rtl:hint_rect.setRight(hint_rect.left()+16);text_rect.adjust(23,0,0,0)
                else:hint_rect.setLeft(hint_rect.right()-16);text_rect.adjust(0,0,-23,0)
                icon('note','#6B7E97',16).paint(painter,int(hint_rect.x()),int(hint_rect.center().y()-8),16,16)
        elided=painter.fontMetrics().elidedText(value,Qt.ElideRight,max(0,int(text_rect.width())))
        text_option=QTextOption(align|Qt.AlignAbsolute)
        text_option.setTextDirection(Qt.RightToLeft if rtl else Qt.LeftToRight)
        if not is_group and item and not item['title']:text_option.setTextDirection(Qt.LeftToRight)
        painter.drawText(text_rect,elided,text_option)
        if option.state & QStyle.State_HasFocus:
            pen=QPen(QColor('#356BC3'),1,Qt.DotLine);painter.setPen(pen);painter.setBrush(Qt.NoBrush);painter.drawRoundedRect(r.adjusted(3,3,-3,-3),5,5)
        painter.restore()
