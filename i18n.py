"""Locale resources shared by the interface, settings and offline guide."""
import json
from functools import lru_cache
from pathlib import Path

LANGUAGES={'en':'English','fa':'فارسی','ar':'العربية','es':'Español','fr':'Français','de':'Deutsch',
           'pt_BR':'Português (Brasil)','ru':'Русский','zh_CN':'简体中文','ja':'日本語','tr':'Türkçe','hi':'हिन्दी'}
RTL_LANGUAGES={'fa','ar'}
RESOURCE_ROOT=Path(__file__).resolve().parent

@lru_cache(maxsize=None)
def catalog(language):
    if language not in LANGUAGES:language='en'
    return json.loads((RESOURCE_ROOT/'locales'/f'{language}.json').read_text('utf-8'))

def text(key,language):
    return catalog(language).get(key,catalog('en').get(key,key))

def guide(language):
    if language not in LANGUAGES:language='en'
    return json.loads((RESOURCE_ROOT/'help'/f'{language}.json').read_text('utf-8'))
