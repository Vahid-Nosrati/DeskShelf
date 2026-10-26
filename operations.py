"""Scoped ordering and reversible batch removals; never modifies target files."""
import copy
from core import KINDS


def reference(data, kind, ref):
    if kind not in KINDS or not isinstance(ref, (tuple, list)) or len(ref) != 2:
        return None
    typ, identifier = ref
    if typ == 'category':
        return next((c for c in data['categories'][kind] if c['id'] == identifier), None)
    if typ == 'item':
        return next((i for i in data['items'] if i['id'] == identifier and i['kind'] == kind), None)
    return None


def siblings(data, kind, ref):
    obj = reference(data, kind, ref)
    if obj is None:
        return []
    if ref[0] == 'category':
        return data['categories'][kind][:]
    return [i for i in data['items'] if i['kind'] == kind and i['category'] == obj['category']]


def can_reorder(data, kind, source, target):
    a, b = reference(data, kind, source), reference(data, kind, target)
    return bool(a is not None and b is not None and source[0] == target[0]
                and source[1] != target[1]
                and (source[0] == 'category' or a['category'] == b['category']))


def reorder(data, kind, source, target, after=False):
    if not can_reorder(data, kind, source, target):
        return False
    values = siblings(data, kind, source)
    old_ids = [v['id'] for v in values]
    obj = next(v for v in values if v['id'] == source[1])
    values.remove(obj)
    index = next(n for n, v in enumerate(values) if v['id'] == target[1])
    values.insert(index + int(after), obj)
    if old_ids == [v['id'] for v in values]:
        return False
    if source[0] == 'category':
        data['categories'][kind] = values
    else:
        iterator = iter(values)
        cat = obj['category']
        data['items'] = [next(iterator) if i['kind'] == kind and i['category'] == cat else i
                         for i in data['items']]
    return True


def removal_summary(data, kind, typ, ids):
    if kind not in KINDS or typ not in ('item', 'category'):
        raise ValueError('Invalid removal scope')
    ids = set(ids)
    if not ids:
        return 0, 0
    allowed = {v['id'] for v in (data['categories'][kind] if typ == 'category' else data['items'])
               if typ == 'category' or v['kind'] == kind}
    if not ids <= allowed or (typ == 'category' and 'general' in ids):
        raise ValueError('Selection is outside the removable scope')
    count = sum(1 for i in data['items'] if i['kind'] == kind and
                (i['id'] in ids if typ == 'item' else i['category'] in ids))
    return (len(ids) if typ == 'category' else 0), count


def remove_batch(data, kind, typ, ids, mode='keep'):
    categories, items = removal_summary(data, kind, typ, ids)
    if not categories and not items:
        return None
    if mode not in ('keep', 'remove'):
        raise ValueError('Unknown removal mode')
    ids = set(ids)
    affected = {i['id'] for i in data['items'] if i['kind'] == kind and
                (i['id'] in ids if typ == 'item' else i['category'] in ids)}
    removed_cats = ids if typ == 'category' else set()
    record = {'kind': kind, 'categories': copy.deepcopy(data['categories'][kind]),
              'items': copy.deepcopy(data['items']), 'removed_categories': removed_cats,
              'removed_items': affected if typ == 'item' or mode == 'remove' else set(),
              'moved_items': affected if typ == 'category' and mode == 'keep' else set(),
              'collapsed': {k: v for k, v in data['collapsed'].items()
                            if k in {kind + ':' + c for c in removed_cats}}}
    if typ == 'category' and mode == 'keep':
        # Append moved entries to General in visible category order, then item order.
        moved = [i for c in data['categories'][kind] if c['id'] in ids
                 for i in data['items'] if i['kind'] == kind and i['category'] == c['id']]
        data['items'] = [i for i in data['items'] if i['id'] not in affected]
        for i in moved:
            i['category'] = 'general'
        data['items'].extend(moved)
    else:
        data['items'] = [i for i in data['items'] if i['id'] not in affected]
    if typ == 'category':
        data['categories'][kind] = [c for c in data['categories'][kind] if c['id'] not in ids]
        for c in ids:
            data['collapsed'].pop(kind + ':' + c, None)
    return record


def _insert_missing(current, original, restored):
    """Restore positions using surviving original neighbors; retain later additions."""
    result = current[:]
    original_ids = [v['id'] for v in original]
    for obj in original:
        identifier = obj['id']
        if identifier not in restored or any(v['id'] == identifier for v in result):
            continue
        at = original_ids.index(identifier)
        live_ids = [v['id'] for v in result]
        following = next((i for i in original_ids[at + 1:] if i in live_ids), None)
        previous = next((i for i in reversed(original_ids[:at]) if i in live_ids), None)
        pos = live_ids.index(following) if following else live_ids.index(previous) + 1 if previous else 0
        result.insert(pos, restored[identifier])
    return result


def undo_batch(data, record, recovered_label='restored'):
    kind = record['kind']
    cats = data['categories'][kind]
    live_cats = {c['id'] for c in cats}
    restore_cats = {}
    names = {c['name'].casefold() for c in cats}
    for c in record['categories']:
        if c['id'] in record['removed_categories'] and c['id'] not in live_cats:
            value = copy.deepcopy(c)
            original_name = value['name']
            n = 1
            while value['name'].casefold() in names:
                value['name'] = original_name + ' (' + recovered_label + ('' if n == 1 else ' ' + str(n)) + ')'
                n += 1
            names.add(value['name'].casefold())
            restore_cats[value['id']] = value
    data['categories'][kind] = _insert_missing(cats, record['categories'], restore_cats)
    for key, value in record['collapsed'].items():
        if key[len(kind) + 1:] in restore_cats:
            data['collapsed'][key] = value
    originals = {i['id']: i for i in record['items']}
    restore_items = {}
    for item in data['items']:
        if item['id'] in record['moved_items'] and item['kind'] == kind and item['category'] == 'general':
            restore_items[item['id']] = item
    data['items'] = [i for i in data['items'] if i['id'] not in restore_items]
    for identifier, item in restore_items.items():
        item['category'] = originals[identifier]['category']
    live_ids = {i['id'] for i in data['items']}
    for identifier in record['removed_items'] - live_ids:
        restore_items[identifier] = copy.deepcopy(originals[identifier])
    available_cats = {c['id'] for c in data['categories'][kind]}
    for item in restore_items.values():
        if item['category'] not in available_cats:
            item['category'] = 'general'
    data['items'] = _insert_missing(data['items'], record['items'], restore_items)
