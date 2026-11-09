"""2.2.1 direct-IP LAN behavior with Host/Origin and Civitai boundaries intact."""
import test_safety
import http.client,json,os,tempfile,threading
from unittest.mock import patch,Mock
with tempfile.TemporaryDirectory(prefix='cad3-direct-lan-') as temporary:
 os.environ['CIVITAI_HISTORY_DATA_DIR']=temporary
 import server
 server.SETTINGS.update(auto_capture_value=False)
 class PeerHandler(server.Handler):
  def setup(self):
   super().setup();self.client_address=('192.168.10.3',self.client_address[1])
  def log_message(self,*args):pass
 listener=server.ThreadingHTTPServer(('127.0.0.1',0),PeerHandler);port=listener.server_address[1]
 worker=threading.Thread(target=listener.serve_forever,daemon=True);worker.start()
 host=f'192.168.10.2:{port}'
 def request(path,body=None,headers=None):
  connection=http.client.HTTPConnection('127.0.0.1',port,timeout=5)
  supplied={'Host':host,**(headers or {})}
  if body is not None:supplied['Content-Type']='application/json'
  connection.request('POST' if body is not None else 'GET',path,None if body is None else json.dumps(body),supplied)
  response=connection.getresponse();data=response.read();cookie=response.getheader('Set-Cookie');connection.close()
  return response.status,data,cookie
 try:
  with patch.object(server,'lan_addresses',return_value=['192.168.10.2']):
   assert request('/')[0]==403
   assert request('/api/settings')[0]==403
   assert request('/api/settings',{'dimSeenCards':False},headers={'Origin':'http://'+host})[0]==403
   assert request('/api/community/recommend',{'artwork':123},headers={'Origin':'http://'+host})[0]==403
   assert not server.is_own_app_url('http://'+host)
 finally:listener.shutdown();listener.server_close();worker.join(timeout=5);server.MUSIC_SCOUT.close()
print('PASS: remote peer and LAN host are refused; loopback-only fork')
