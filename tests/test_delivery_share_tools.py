"""Command artifact confinement and consumed-permission failures; fake transport only."""
import base64
import hashlib
import json
import os
import socket
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer

import pytest
from test_delivery_tools import tools,private_config,TEST_TOKEN,SCRIPT,initialized_server,frame

RAW=b'Synthetic approved public record. No private source text.\n'
NAME='handoff-'+('a'*32)+'.md'

@pytest.fixture
def transport():
    state={'issued':False,'issue_calls':0,'get_calls':0,'lose_reply':False,'material':{'intent_id':'intent-1','filename':NAME,'artifact_sha256':hashlib.sha256(RAW).hexdigest(),'artifact_size':len(RAW),'content_base64':base64.b64encode(RAW).decode()}}
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_GET(self):
            state['get_calls']+=1
            if state['issued']:self.send_response(409);self.end_headers();return
            self.answer(state['material'])
        def do_POST(self):
            state['issue_calls']+=1
            value=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            assert set(value)=={'operation_key','artifact_sha256'}
            first=not state['issued'];state['issued']=True
            if state['lose_reply']:self.connection.shutdown(socket.SHUT_RDWR);self.connection.close();return
            self.answer({'state':'succeeded','result':{'intent_id':'intent-1','attempt_id':'b'*32,'artifact_sha256':hashlib.sha256(RAW).hexdigest(),'send_permitted':first,'state':'issued_unverified','switch_send_arguments':{'room_id':'bound-room','caption':'Frozen reviewed record.'} if first else None}})
        def answer(self,body):
            self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(json.dumps({'data':body}).encode())
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:yield f'http://127.0.0.1:{server.server_port}',state
    finally:server.shutdown();server.server_close();thread.join(2)


def config(tmp_path,origin):
    incoming=tmp_path/'incoming';incoming.mkdir();outgoing=tmp_path/'outgoing';outgoing.mkdir(mode=0o700)
    path=private_config(tmp_path,origin,schema_version=4,attachment_root=str(incoming),outgoing_root=str(outgoing))
    return path,outgoing,tools.Config.from_private_file(str(path))


def args(**changes):return {'job_id':'job','intent_id':'intent-1','operation_key':'return-once',**changes}


def test_real_command_prepares_exact_private_file_and_consumes_one_permission(transport,tmp_path):
    origin,state=transport;path,outgoing,cfg=config(tmp_path,origin)
    listed=initialized_server(tools.DeliveryClient(cfg)).handle(frame('tools/list'))['tools']
    assert len(listed)==6 and listed[-1]['name']=='delivery_take_share'
    result=subprocess.run([sys.executable,str(SCRIPT),'--config-file',str(path),'--call-tool','delivery_take_share'],input=json.dumps(args()),text=True,capture_output=True,timeout=10)
    assert result.returncode==0 and not result.stderr and TEST_TOKEN not in result.stdout
    value=json.loads(result.stdout)['result'];assert value['send_permitted'] is True
    assert value['switch_send_arguments']=={'room_id':'bound-room','caption':'Frozen reviewed record.','path':str(outgoing/NAME)}
    assert (outgoing/NAME).read_bytes()==RAW and (outgoing/NAME).stat().st_mode & 0o777==0o600
    retry=tools.DeliveryClient(cfg).call('delivery_take_share',args())
    assert retry['send_permitted'] is False and state['issue_calls']==1


def test_lost_issue_reply_stops_and_does_not_issue_again(transport,tmp_path):
    origin,state=transport;_,outgoing,cfg=config(tmp_path,origin);state['lose_reply']=True
    client=tools.DeliveryClient(cfg);result=client.call('delivery_take_share',args())
    assert result['send_permitted'] is False and state['issued']
    assert (outgoing/NAME).read_bytes()==RAW
    retry=client.call('delivery_take_share',args())
    assert retry['send_permitted'] is False and state['issue_calls']==1


@pytest.mark.parametrize('kind',['symlink','hardlink','fifo','different','public_file'])
def test_refuses_unsafe_or_conflicting_output_without_issue(transport,tmp_path,kind):
    origin,state=transport;_,outgoing,cfg=config(tmp_path,origin);target=outgoing/NAME;outside=tmp_path/'outside';outside.write_bytes(RAW)
    if kind=='symlink':target.symlink_to(outside)
    elif kind=='hardlink':os.link(outside,target)
    elif kind=='fifo':os.mkfifo(target)
    else:target.write_bytes(b'Different' if kind=='different' else RAW);target.chmod(0o644 if kind=='public_file' else 0o600)
    result=tools.DeliveryClient(cfg).call('delivery_take_share',args())
    assert result['send_permitted'] is False and state['issue_calls']==0
    assert outside.read_bytes()==RAW


@pytest.mark.parametrize('change',[{'filename':'../private.md'},{'intent_id':'foreign'},{'artifact_size':True},{'artifact_size':tools.SHARE_BYTES+1},{'artifact_sha256':'f'*64},{'content_base64':'bad!!'}])
def test_refuses_wrong_material_identity_before_file_or_issue(transport,tmp_path,change):
    origin,state=transport;_,outgoing,cfg=config(tmp_path,origin);state['material'].update(change)
    result=tools.DeliveryClient(cfg).call('delivery_take_share',args())
    assert result['send_permitted'] is False and not list(outgoing.iterdir()) and state['issue_calls']==0


def test_owner_private_root_and_explicit_version_are_required(tmp_path):
    path,outgoing,cfg=config(tmp_path,'http://127.0.0.1:8877');outgoing.chmod(0o755)
    with pytest.raises(tools.ConfigurationError):tools.Config.from_private_file(str(path))
    outgoing.chmod(0o700)
    link=tmp_path/'linked';link.symlink_to(outgoing,target_is_directory=True)
    data=json.loads(path.read_text());data['outgoing_root']=str(link);path.write_text(json.dumps(data))
    with pytest.raises(tools.ConfigurationError):tools.Config.from_private_file(str(path))
    old=tools.Config.from_env({'HANDOFFREADY_DELIVERY_ORIGIN':'http://127.0.0.1:8877','HANDOFFREADY_DELIVERY_BINDING':'test','HANDOFFREADY_DELIVERY_TOKEN':TEST_TOKEN})
    with pytest.raises(tools.RpcError):tools.DeliveryClient(old).call('delivery_take_share',args())


@pytest.mark.parametrize('change',[{'job_id':'../escape'},{'intent_id':'https://evil.example'},{'destination':'other'},{'file_path':'/private'},{'operation_key':True}])
def test_args_cannot_choose_path_or_destination_before_network(transport,tmp_path,change):
    origin,state=transport;_,_,cfg=config(tmp_path,origin)
    with pytest.raises(tools.RpcError):tools.DeliveryClient(cfg).call('delivery_take_share',args(**change))
    assert state['get_calls']==0 and state['issue_calls']==0
