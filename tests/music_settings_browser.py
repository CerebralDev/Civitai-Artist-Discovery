"""Collection editor, persistence, escaping and responsive layout with fake APIs."""
import test_safety
from functools import partial
from http.server import ThreadingHTTPServer
import json
from pathlib import Path
import threading
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright
from v2_visual_baseline import ROOT, StaticHandler, install_fixture
from discovery.musicscout import MusicScout
from discovery.music_settings import normalize_collections

settings = {'musicCollections': [], 'communityEnabled': False, 'registryEnabled': False,
            'browsingLevels': [1, 2], 'contentRating': 'Soft', 'mediaType': 'all'}
scout = MusicScout(None, collections=[])
httpd = ThreadingHTTPServer(('127.0.0.1', 0), partial(StaticHandler, directory=str(ROOT/'static')))
threading.Thread(target=httpd.serve_forever, daemon=True).start()
base = f'http://127.0.0.1:{httpd.server_port}'
saves = []

def route_music(route):
    path = urlparse(route.request.url).path
    if path == '/api/settings':
        if route.request.method == 'POST':
            body = json.loads(route.request.post_data)
            try:
                normalized = normalize_collections(body.get('musicCollections', settings['musicCollections']))
            except ValueError as error:
                route.fulfill(status=400, content_type='application/json', body=json.dumps({'error':str(error)})); return
            settings.update(body); settings['musicCollections'] = normalized
            scout.configure(normalized); saves.append(dict(body))
        data = settings
    elif path == '/api/music/queues': data = scout.catalog()
    elif path == '/api/music/queue': data = {'items': [], 'exhausted': True, 'total': 0}
    else: route.fallback(); return
    route.fulfill(content_type='application/json', body=json.dumps(data))

try:
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1440, 'height': 900})
        errors = []; page.on('pageerror', lambda error: errors.append(str(error)))
        install_fixture(page, base); page.route('**/*', route_music)
        page.goto(base, wait_until='networkidle'); page.locator('#tabMusicScout').click()
        page.locator('#musicSettingsOpen').click()
        page.locator('#musicCollectionAdd').click()
        row = page.locator('.music-collection-row').first
        row.locator('[data-field=collectionId]').fill('https://civitai.com/collections/12345')
        row.locator('[data-field=name]').fill('My music <test>')
        row.locator('[data-field=comment]').fill('<script>window.injected = true</script> Thanks!')
        page.locator('#musicSettingsSave').click(); page.wait_for_function("!document.querySelector('#musicSettings').open")
        assert saves[-1]['musicCollections'][0]['collectionId'] == 12345
        assert page.locator('[data-queue=collection-12345]').inner_text().startswith('My music <test>')
        assert page.locator('[data-queue=collection-12345-hub]').count() == 1
        assert page.evaluate('window.injected') is None
        page.reload(wait_until='networkidle'); page.locator('#tabMusicScout').click(); page.locator('#musicSettingsOpen').click()
        assert page.locator('[data-field=name]').input_value() == 'My music <test>'
        assert not page.locator('#musicCommunityEnabled').is_checked()
        page.locator('#musicCommunityEnabled').check(); page.locator('#musicRegistryEnabled').check()
        page.locator('#musicCommunityEnabled').uncheck(); assert not page.locator('#musicRegistryEnabled').is_checked()
        assert page.locator('#musicRegistryEnabled').is_disabled()
        # Each supported layout keeps the dialog within the viewport, scrollable and usable.
        for width, height in [(1440,900),(1024,768),(768,1024),(540,900),(390,844),(320,640)]:
            page.set_viewport_size({'width':width,'height':height})
            bounds = page.locator('#musicSettings').bounding_box()
            assert bounds['x'] >= -1 and bounds['x'] + bounds['width'] <= width + 1, (width,bounds)
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'), width
        page.locator('#musicCollectionAdd').click()
        duplicate = page.locator('.music-collection-row').last
        duplicate.locator('[data-field=collectionId]').fill('12345'); duplicate.locator('[data-field=name]').fill('Duplicate')
        page.locator('#musicSettingsSave').click()
        page.locator('#musicSettingsError').get_by_text('Each collection can appear only once').wait_for()
        duplicate.get_by_role('button', name='Remove feed').click()
        page.locator('.music-collection-row').get_by_role('button', name='Remove feed').click()
        page.locator('#musicSettingsSave').click(); page.wait_for_function("!document.querySelector('#musicSettings').open")
        assert settings['musicCollections'] == []
        assert page.locator('[data-queue=collection-12345]').count() == 0
        assert not errors, errors
        browser.close()
finally:
    httpd.shutdown(); httpd.server_close(); scout.close()
print('PASS: collection editor persistence, safe rendering, duplicate rejection, removal, privacy controls, six layouts')
