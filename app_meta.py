"""Public release metadata; optional links are maintained in app_info.json."""
import json
import sys
from pathlib import Path

VERSION='0.4.0'

def app_root():
    return Path(sys.executable).parent if getattr(sys,'frozen',False) else Path(__file__).resolve().parent

def app_info():
    info={'author':'Vahid Nosrati','github_profile':'','repository_url':'','public_contact':''}
    path=app_root()/'app_info.json'
    try:
        data=json.loads(path.read_text('utf-8'))
        if isinstance(data,dict):
            for key in info:
                if isinstance(data.get(key),str):info[key]=data[key].strip()
    except (OSError,ValueError):pass
    return info
