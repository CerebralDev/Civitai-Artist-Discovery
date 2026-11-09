"""Validated local collection subscriptions; URLs and HTML are never user supplied."""
import html

DEFAULT_COLLECTIONS = [
    {'collectionId': 17980935, 'name': 'Music Focus', 'icon': '🎸', 'comment': ''},
    {'collectionId': 18403457, 'name': 'H3 Movies Museum', 'icon': '🎬', 'comment': ''},
]


def normalize_collections(value):
    if not isinstance(value, list) or len(value) > 12:
        raise ValueError('Choose up to 12 collections')
    result, seen = [], set()
    for item in value:
        if not isinstance(item, dict):
            raise ValueError('Invalid collection')
        identifier = item.get('collectionId')
        if type(identifier) is not int or not 0 < identifier < 2**53:
            raise ValueError('Use a positive collection ID from its Civitai address')
        if identifier in seen:
            raise ValueError('Each collection can appear only once')
        seen.add(identifier)
        name, icon, comment = item.get('name', ''), item.get('icon', '♫'), item.get('comment', '')
        if not isinstance(name, str) or not 1 <= len(name.strip()) <= 80:
            raise ValueError('Give each collection a name of 1 to 80 characters')
        if not isinstance(icon, str) or len(icon) > 8 or not isinstance(comment, str) or len(comment) > 2000:
            raise ValueError('Keep icons short and comments under 2000 characters')
        result.append({'collectionId': identifier, 'name': name.strip(), 'icon': icon or '♫',
                       'comment': comment.strip()})
    return result


def catalog_collections(value):
    result = []
    for item in normalize_collections(value):
        identifier = item['collectionId']
        key = {17980935: 'music-focus', 18403457: 'h3-museum'}.get(identifier, f'collection-{identifier}')
        comment = item['comment']
        result.append({**item, 'key': key, 'url': f'https://civitai.red/collections/{identifier}',
                       'commentHtml': '<p>' + html.escape(comment).replace('\n', '<br>') + '</p>' if comment else ''})
    return result
