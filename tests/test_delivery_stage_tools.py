"""Configured attachment-root confinement with real files and loopback HTTP."""
import base64
import json
import os
import subprocess
import sys

import pytest
from test_delivery_tools import tools, backend as backend, private_config, TEST_TOKEN, SCRIPT, frame, initialized_server


def configured(tmp_path,origin):
    root=(tmp_path/'attachments').resolve();root.mkdir()
    path=private_config(tmp_path,origin)
    value=json.loads(path.read_text());value.update(schema_version=2,attachment_root=str(root));path.write_text(json.dumps(value))
    return path,root,tools.Config.from_private_file(str(path))


def args(root,**changes):
    return {"job_id":"job","operation_key":"stage1","source_id":"discord-source1","filename":"guide.txt","file_path":str(root/'guide.txt'),**changes}


def test_v2_stage_subprocess_uses_actual_bytes_no_commit(backend,tmp_path):
    config,state=backend
    path,root,config=configured(tmp_path,config.origin)
    content=b"Actual synthetic attachment."
    (root/'guide.txt').write_bytes(content)
    result=subprocess.run([sys.executable,str(SCRIPT),'--config-file',str(path),'--call-tool','delivery_stage_receipt'],input=json.dumps(args(root)),text=True,capture_output=True,timeout=5)
    assert result.returncode == 0 and not result.stderr
    assert TEST_TOKEN not in result.stdout
    assert len(state['calls']) == 1
    request=state['calls'][0]
    assert request['path'] == '/api/v1/delivery/jobs/job/receipts' and request['method'] == 'POST'
    assert base64.b64decode(request['body']['content_base64']) == content
    assert set(request['body']) == {'operation_key','source_id','filename','content_base64'}
    listed=initialized_server(tools.DeliveryClient(config)).handle(frame('tools/list'))['tools']
    assert {tool['name'] for tool in listed} == {'delivery_status','delivery_check_preview','delivery_stage_receipt'}


@pytest.mark.parametrize('kind',['outside','file_link','dir_link','hardlink','fifo','large','empty','traversal','directory'])
def test_attachment_escape_and_nonregular_refused_without_network(backend,tmp_path,kind):
    config,state=backend
    _,root,config=configured(tmp_path,config.origin)
    outside=tmp_path/'outside.txt';outside.write_bytes(b'PRIVATE OUTSIDE FILE')
    target=root/'guide.txt'
    if kind == 'outside':target=outside
    elif kind == 'file_link':target.symlink_to(outside)
    elif kind == 'dir_link':
        (root/'linked').symlink_to(tmp_path,target_is_directory=True);target=root/'linked/outside.txt'
    elif kind == 'hardlink':os.link(outside,target)
    elif kind == 'fifo':os.mkfifo(target)
    elif kind == 'large':
        with target.open('wb') as file:file.truncate(tools.FILE_BYTES+1)
    elif kind == 'empty':target.write_bytes(b'')
    elif kind == 'traversal':target=root/'..'/'outside.txt'
    elif kind == 'directory':target.mkdir()
    result=tools.DeliveryClient(config).call('delivery_stage_receipt',args(root,file_path=str(target)))
    assert result['error']['code'] == 'attachment_refused'
    assert not state['calls']
    assert str(target) not in json.dumps(result) and 'PRIVATE' not in json.dumps(result)


@pytest.mark.parametrize('changes',[{'url':'https://private.example'},{'filename':'../escape.txt'},{'source_id':'bad\nsource'},{'job_id':'../job'},{'operation_key':False}])
def test_stage_arguments_strict_before_reading_or_http(backend,tmp_path,changes):
    config,state=backend
    _,root,config=configured(tmp_path,config.origin)
    with pytest.raises(tools.RpcError):tools.DeliveryClient(config).call('delivery_stage_receipt',args(root,**changes))
    assert not state['calls']


def test_readonly_v1_cannot_stage_and_root_symlink_refused(backend,tmp_path):
    config,state=backend
    with pytest.raises(tools.RpcError):tools.DeliveryClient(config).call('delivery_stage_receipt',{})
    path,root,_=configured(tmp_path,config.origin)
    linked=tmp_path/'linkedroot';linked.symlink_to(root,target_is_directory=True)
    value=json.loads(path.read_text());value['attachment_root']=str(linked);path.write_text(json.dumps(value))
    with pytest.raises(tools.ConfigurationError):tools.Config.from_private_file(str(path))
    assert not state['calls']


def test_backend_compatible_printable_token_and_schema_revision_bound():
    config=tools.Config.from_env({'HANDOFFREADY_DELIVERY_ORIGIN':'http://127.0.0.1:8877','HANDOFFREADY_DELIVERY_BINDING':'test','HANDOFFREADY_DELIVERY_TOKEN':'synthetic+/=token.for-tests'})
    assert config.token == 'synthetic+/=token.for-tests'
    assert tools.TOOLS[1]['inputSchema']['properties']['expected_revision']['maximum'] == 2**53-1


def test_unclosed_command_pipe_has_time_budget_and_no_network(backend,tmp_path,monkeypatch):
    import io
    import time
    config,state=backend
    reader,writer=os.pipe()
    try:
        os.write(writer,b'{"job_id":"job"}')
        with os.fdopen(reader,'rb',closefd=False) as source:
            monkeypatch.setattr(tools,'INPUT_TIMEOUT',0.03)
            output=io.BytesIO();started=time.monotonic()
            assert tools.call_once(config,'delivery_status',source,output) == 2
            assert time.monotonic()-started < 1
            assert json.loads(output.getvalue())['error']['code'] == 'input_timeout'
        assert not state['calls']
    finally:
        os.close(reader);os.close(writer)


def test_optional_first_page_cursor_and_invalid_argument_protocol_error(backend):
    config,_=backend
    server=initialized_server(tools.DeliveryClient(config))
    assert len(server.handle(frame('tools/list',params={'cursor':None}))['tools']) == 2
    assert len(server.handle(frame('tools/list',params={'cursor':''}))['tools']) == 2
    with pytest.raises(tools.RpcError):server.handle(frame('tools/list',params={'cursor':'not-issued'}))
    with pytest.raises(tools.RpcError) as error:server.handle(frame('tools/call',params={'name':'delivery_status','arguments':{'job_id':'../invalid'}}))
    assert error.value.code == -32602
