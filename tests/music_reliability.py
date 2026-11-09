"""Personal music fork boundaries: fake-only regression coverage."""
import test_safety
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from email.message import Message
from email.utils import format_datetime
import io
import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import Mock, patch
import urllib.error
import urllib.request

from discovery.write_guard import WriteGuard, WriteBlocked
from discovery.collectalytics import Collectalytics, CommentedNotAccepted
from discovery.music_settings import normalize_collections, catalog_collections
from discovery.settings import AppSettings
from discovery.musicscout import MusicScout
from discovery.civitai import API_LANE, RequestLane
from discovery.social import SocialClient, CivitaiHTTPError
from discovery.history import HistoryArchive
from discovery import diagnostics, oauth, privacy, community
from discovery.registry import RegistryClient


class MusicReliability(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='cad3-music-fix-', ignore_cleanup_errors=True)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.env = patch.dict(os.environ, CIVITAI_HISTORY_DATA_DIR=str(self.root))
        self.env.start(); self.addCleanup(self.env.stop)
        API_LANE.not_before = 0
        self.addCleanup(setattr, API_LANE, 'not_before', 0)

    def service(self, client, path=None):
        service = Collectalytics(lambda: client, WriteGuard(path))
        service.review_queue = lambda *a, **kw: {'collection': {'id': 12, 'name': 'Fixture'},
            'items': [{'collectionItemId': 7, 'kind': 'image', 'itemId': 8}]}
        return service

    def test_partial_accept_survives_restart(self):
        path = self.root/'outcomes.sqlite3'
        client = Mock(); client.comment_on_image.return_value = {'id': 20}
        client.set_collection_items_status.side_effect = TimeoutError()
        with self.assertRaises(CommentedNotAccepted): self.service(client, path).accept(1, 12, 7, 'Thanks')
        with self.assertRaises(WriteBlocked): self.service(client, path).accept(1, 12, 7, 'Thanks')
        self.assertEqual(client.comment_on_image.call_count, 1)
        self.assertNotIn(b'Thanks', path.read_bytes())

    def test_lost_comment_response_never_replayed(self):
        client = Mock(); client.comment_on_image.side_effect = TimeoutError('synthetic')
        service = self.service(client)
        for _ in range(2):
            with self.assertRaises(WriteBlocked): service.accept(1, 12, 7, 'Thanks')
        self.assertEqual(client.comment_on_image.call_count, 1)
        client.set_collection_items_status.assert_not_called()

    def test_simultaneous_intents_across_instances(self):
        path = self.root/'guard.sqlite3'; guards = [WriteGuard(path), WriteGuard(path)]
        key = guards[0].key(1, 'accept', 12, 7)
        def attempt(guard):
            try: guard.begin(key); return True
            except WriteBlocked: return False
        with ThreadPoolExecutor(2) as executor: results = list(executor.map(attempt, guards))
        self.assertEqual(sum(results), 1)
        guards[0].begin(guards[0].key(2, 'accept', 12, 7))

    def test_missing_comment_identifier_is_uncertain(self):
        client = SocialClient()
        for response in ({}, {'id': True}, {'id': 0}, []):
            with patch.object(client, 'mutate', return_value=response):
                with self.assertRaises(RuntimeError): client.comment_on_image(1, 'Thanks')

    def test_config_roundtrip_and_validation(self):
        settings = AppSettings(self.root/'settings.json')
        values = [{'collectionId': 123, 'name': '<Example>', 'comment': '<script>alert(1)</script>'}]
        settings.update(music_collections_value=values)
        settings.update(dim_seen_cards_value=False)
        self.assertEqual(settings.load()['musicCollections'][0]['collectionId'], 123)
        self.assertFalse(settings.load()['dimSeenCards'])
        html = catalog_collections(values)[0]['commentHtml']
        self.assertNotIn('<script>', html); self.assertIn('&lt;script&gt;', html)
        for values in ([{'collectionId': True, 'name': 'x'}], [{'collectionId': 1, 'name': 'x'}]*2,
                       [{'collectionId': 1, 'name': 'x'}]*13):
            with self.assertRaises(ValueError): normalize_collections(values)

    def test_config_changes_invalidate_queues(self):
        archive = Mock(); archive._request.return_value = ({'items': [], 'metadata': {}}, 2)
        scout = MusicScout(archive, collections=[]); self.addCleanup(scout.close)
        self.assertEqual(len(scout.catalog()['queues']), 3)
        scout.configure([{'collectionId': 123, 'name': 'Example'}])
        self.assertEqual(len(scout.catalog()['queues']), 5)
        scout.configure([])
        with self.assertRaises(ValueError): scout.page('collection-123')

    def test_late_queue_response_cannot_cross_configuration(self):
        entered, release = threading.Event(), threading.Event()
        def read(*a, **kw):
            entered.set(); release.wait(5); return {'items': [], 'metadata': {}}, 2
        archive = Mock(); archive._request.side_effect = read
        scout = MusicScout(archive, collections=[]); self.addCleanup(scout.close)
        with ThreadPoolExecutor(1) as executor:
            future = executor.submit(scout.page, 'latest')
            self.assertTrue(entered.wait(5)); scout.configure([{'collectionId': 3, 'name': 'New'}]); release.set()
            with self.assertRaises(ValueError): future.result()

    def test_retry_after_date_and_long_wait_retained(self):
        lane = RequestLane()
        lane.observe_http(429, format_datetime(datetime.now(timezone.utc)+timedelta(seconds=120), usegmt=True))
        self.assertGreater(lane.cooldown(), 118)
        lane.observe_http(503, '3600'); self.assertGreater(lane.cooldown(), 3598)

    def test_html_error_shares_cooldown_before_parsing(self):
        for code in (429, 503):
            API_LANE.not_before = 0
            headers = Message(); headers['Retry-After'] = '120'
            error = urllib.error.HTTPError('https://example.invalid', code, 'fixture', headers, io.BytesIO(b'<html>fixture</html>'))
            with patch('urllib.request.urlopen', side_effect=error):
                with self.assertRaises(CivitaiHTTPError): SocialClient._send(urllib.request.Request('https://example.invalid'))
            self.assertGreater(API_LANE.cooldown(), 119)
            client = SocialClient()
            with patch.object(client, '_send') as send:
                with self.assertRaises(CivitaiHTTPError): client._request(urllib.request.Request('https://example.invalid', data=b'{}'))
                send.assert_not_called()

    def test_fallback_429_deadline(self):
        lane = RequestLane(); lane.observe_http(429, 'invalid')
        self.assertGreater(lane.cooldown(), 59)

    def test_private_diagnostics(self):
        diagnostics.append_log(self.root, 'secret-username prompt https://example.invalid/token')
        diagnostics.log_browser_events(self.root, [{'event':'video_failed','username':'secret-username','imageId':987,'url':'https://example.invalid'}])
        archive = HistoryArchive(self.root/'history')
        archive._record_api_failure({'cursor':'secret-username'}, 'http', status=429, body=b'secret-username prompt')
        records = (self.root/'error.log').read_text() + archive.api_failure_log.read_text()
        for forbidden in ('secret-username', 'prompt', 'example.invalid', '987'): self.assertNotIn(forbidden, records)
        self.assertIn('429', records); self.assertIn('video_failed', records)

    def test_cloud_opt_in_and_immediate_opt_out(self):
        self.assertFalse(privacy.enabled('communityEnabled'))
        with patch('urllib.request.build_opener') as opener:
            with self.assertRaises(community.CommunityError): community.bounded_json('https://example.supabase.co/functions/v1/community-v1')
            opener.assert_not_called()
        settings = AppSettings(self.root/'settings.json')
        settings.update(community_enabled_value=True, registry_enabled_value=False)
        self.assertTrue(privacy.enabled('communityEnabled')); self.assertFalse(privacy.enabled('registryEnabled'))
        self.assertFalse(RegistryClient('fixture').authenticated({'id': 1}, Mock()))
        settings.update(community_enabled_value=False)
        self.assertFalse(privacy.enabled('communityEnabled'))

    def test_login_without_cloud_identity(self):
        with patch.object(oauth, '_authorize_tokens', return_value={'access_token':'fixture'}), \
             patch.object(oauth, '_userinfo', return_value={'id':1,'username':'fixture'}), \
             patch.object(oauth, '_save_rotated'), patch('discovery.cloud_identity.challenge') as challenge:
            self.assertEqual(oauth.login()['id'], 1)
            challenge.assert_not_called()

    def test_legacy_lan_setting_cannot_open_listener(self):
        path = self.root/'settings.json'; path.write_text('{"allowLanAccess":true}')
        settings = AppSettings(path)
        self.assertFalse(settings.load()['allowLanAccess'])
        with self.assertRaises(ValueError): settings.update(allow_lan_access_value=True)

    def test_image_mime_rejected_before_decoder(self):
        from discovery.cache import ThumbnailCache
        from PIL import Image
        response = Mock(); response.headers = Message(); response.headers['Content-Type'] = 'text/plain'
        response.__enter__ = Mock(return_value=response); response.__exit__ = Mock(return_value=False)
        opener = Mock(); opener.open.return_value = response
        with patch('urllib.request.build_opener', return_value=opener), patch.object(Image, 'open') as decode:
            with self.assertRaises(ValueError): ThumbnailCache._fetch('https://image.civitai.com/fixture', allow_downscale=True)
            decode.assert_not_called(); response.read.assert_not_called()

    def test_mime_spoof_cannot_select_other_decoders(self):
        from discovery.cache import ThumbnailCache
        from PIL import Image, UnidentifiedImageError
        buffer = io.BytesIO(); Image.new('RGB', (2, 2)).save(buffer, 'GIF')
        response = Mock(); response.headers = Message(); response.headers['Content-Type'] = 'image/jpeg'
        response.read = io.BytesIO(buffer.getvalue()).read
        response.__enter__ = Mock(return_value=response); response.__exit__ = Mock(return_value=False)
        opener = Mock(); opener.open.return_value = response
        with patch('urllib.request.build_opener', return_value=opener):
            with self.assertRaises(UnidentifiedImageError): ThumbnailCache._fetch('https://image.civitai.com/fixture', allow_downscale=True)

    def test_write_cannot_switch_account(self):
        client = SocialClient(); client.expected_account = 1
        with patch('discovery.social.get_access_token', return_value='fixture'), \
             patch.object(oauth, '_load', return_value={'access_token':'fixture','identity':{'id':2}}), \
             patch.object(client, '_send') as send:
            with self.assertRaises(PermissionError): client._request(urllib.request.Request('https://example.invalid', data=b'{}'))
            send.assert_not_called()

    def test_account_switch_clears_private_collection_cache(self):
        scout = MusicScout(Mock()); self.addCleanup(scout.close)
        scout.bind_account(1); scout.members[123] = (0, {9}, {'private': 'Private'})
        scout.served[9] = {'id': 9}; scout.bind_account(2)
        self.assertFalse(scout.members); self.assertFalse(scout.served)


if __name__ == '__main__': unittest.main()
