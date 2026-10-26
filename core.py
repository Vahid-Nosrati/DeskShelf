"""Portable data model, validation and atomic persistence. No GUI dependencies."""
import copy
import json
import os
from pathlib import Path

KINDS = ('web', 'folders', 'files', 'apps')

def theme_defaults():
    return {'style':'flat', 'density':'comfortable', 'palette':'pastel',
            'colors': {'canvas':'#E8EDF5', 'web':'#D9E8FC', 'folders':'#DDF2E7',
                       'files':'#FBEACF', 'apps':'#EBE0FA', 'item':'#8395AE', 'category':'#728CAB'},
            'opacity': {'canvas':65, 'web':58, 'folders':58, 'files':58,
                        'apps':58, 'item':65, 'category':85}}

def initial():
    return {'version':2, 'language':'en', 'order':list(KINDS), 'widths':[], 'collapsed':{},
            'theme':theme_defaults(), 'categories':{k:[{'id':'general','name':''}] for k in KINDS}, 'items':[]}

def validate(data):
    if not isinstance(data,dict) or data.get('version') not in (1,2):
        raise ValueError('Unsupported data format')
    d=copy.deepcopy(data)
    if d.get('language') not in ('en','fa','ar','es','fr','de','pt_BR','ru','zh_CN','ja','tr','hi') or not isinstance(d.get('order'),list) or sorted(d['order'])!=sorted(KINDS):
        raise ValueError('Invalid language or column order')
    cats=d.get('categories')
    if not isinstance(cats,dict): raise ValueError('Invalid categories')
    for k in KINDS:
        values=cats.get(k)
        if not isinstance(values,list) or not values or values[0]!={'id':'general','name':''}:
            raise ValueError('Missing General category')
        ids=[]
        for c in values:
            if not isinstance(c,dict) or any(not isinstance(c.get(f),str) for f in ('id','name')) or not c['id']:
                raise ValueError('Invalid category')
            ids.append(c['id'])
        if len(ids)!=len(set(ids)): raise ValueError('Duplicate category')
    ids=set()
    if not isinstance(d.get('items'),list): raise ValueError('Invalid items')
    for i in d['items']:
        if not isinstance(i,dict) or any(not isinstance(i.get(f),str) for f in ('id','kind','category','title','path','note')):
            raise ValueError('Invalid item')
        if not i['id'] or i['id'] in ids or i['kind'] not in KINDS or not i['path'].strip():
            raise ValueError('Invalid item identifier or path')
        ids.add(i['id'])
        if i['category'] not in [c['id'] for c in cats[i['kind']]]: raise ValueError('Unknown category')
    if not isinstance(d.get('collapsed',{}),dict) or any(not isinstance(v,bool) for v in d.get('collapsed',{}).values()):
        raise ValueError('Invalid collapsed state')
    d.setdefault('collapsed',{})
    widths=d.get('widths',[])
    if not isinstance(widths,list) or (widths and (len(widths)!=4 or any(type(w)!=int or w<0 for w in widths))):
        raise ValueError('Invalid widths')
    d['widths']=widths
    if d['version']==1: d['theme']=theme_defaults()
    theme=d.get('theme')
    if not isinstance(theme,dict) or theme.get('style') not in ('flat','raised') or theme.get('density') not in ('comfortable','compact') or theme.get('palette') not in ('pastel','normal'):
        raise ValueError('Invalid appearance')
    import re
    for key in theme_defaults()['colors']:
        color=theme.get('colors',{}).get(key)
        alpha=theme.get('opacity',{}).get(key)
        if not isinstance(color,str) or not re.fullmatch(r'#[0-9a-fA-F]{6}',color) or type(alpha)!=int or not 0<=alpha<=100:
            raise ValueError('Invalid color or opacity')
    d['version']=2
    return d

class Store:
    def __init__(self,root):
        self.root=Path(root); self.root.mkdir(parents=True,exist_ok=True)
        self.path=self.root/'data.json'
        self.data=validate(json.loads(self.path.read_text('utf-8'))) if self.path.exists() else initial()
    def save(self):
        data=validate(self.data)
        raw=json.dumps(data,ensure_ascii=False,indent=2)
        if self.path.exists():
            previous=self.root/'previous.tmp'
            previous.write_bytes(self.path.read_bytes())
            os.replace(previous,self.root/'previous.json')
        tmp=self.root/'data.tmp'
        with tmp.open('w',encoding='utf-8') as f:
            f.write(raw);f.flush();os.fsync(f.fileno())
        os.replace(tmp,self.path)
