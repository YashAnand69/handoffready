"""Stage3 command boundary: explicit opt-in, immutable requests, no approvals."""
import json
import subprocess
import sys

import pytest
from test_delivery_tools import tools, backend as backend, private_config, TEST_TOKEN, SCRIPT, frame, initialized_server


def configured(tmp_path, origin, version=3):
    root = (tmp_path / 'incoming').resolve()
    root.mkdir(exist_ok=True)
    path = private_config(tmp_path, origin, schema_version=version, attachment_root=str(root))
    return path, tools.Config.from_private_file(str(path))


def question(**changes):
    return dict(job_id='job', operation_key='question-1', expected_revision=2,
                input_hash='a'*64, expected_context_epoch=0, requirement_id='r1',
                file_ids=['f1'], question='Which campaign is this for?', source_ref='synthetic:question', **changes)


def reply():
    return dict(job_id='job', question_id='q1', operation_key='reply-1', question_input_hash='a'*64,
                source_ref='synthetic:reply', reported_speaker='Synthetic tester', text='Use the winter campaign.\nCheck the original conversation.')


def test_explicit_v3_inventory_and_real_subprocess_request(backend, tmp_path):
    config, state = backend
    path, config = configured(tmp_path, config.origin)
    listed = initialized_server(tools.DeliveryClient(config)).handle(frame('tools/list'))['tools']
    assert {t['name'] for t in listed} == {'delivery_status','delivery_check_preview','delivery_stage_receipt','delivery_propose_question','delivery_record_reply'}
    for name, args, suffix in [('delivery_propose_question',question(),'questions'), ('delivery_record_reply',reply(),'questions/q1/replies')]:
        result = subprocess.run([sys.executable,str(SCRIPT),'--config-file',str(path),'--call-tool',name], input=json.dumps(args),text=True,capture_output=True,timeout=5)
        assert result.returncode == 0 and not result.stderr
        assert TEST_TOKEN not in result.stdout
        request = state['calls'][-1]
        assert request['path'] == f'/api/v1/delivery/jobs/job/{suffix}'
        assert request['method'] == 'POST'
        assert request['body'] == {k:v for k,v in args.items() if k not in {'job_id','question_id'}}
        assert request['headers']['X-Delivery-Binding'] == config.binding
        assert request['headers']['X-Delivery-Token'] == TEST_TOKEN
    assert len(state['calls']) == 2


@pytest.mark.parametrize('version', [1,2])
def test_old_config_cannot_silently_gain_context_writes(backend,tmp_path,version):
    config,state=backend
    if version == 2:
        _,config=configured(tmp_path, config.origin,version)
    client=tools.DeliveryClient(config)
    assert len(client.tools) == version+1
    for name,args in [('delivery_propose_question',question()),('delivery_record_reply',reply())]:
        with pytest.raises(tools.RpcError): client.call(name,args)
    assert not state['calls']


@pytest.mark.parametrize('change', [
    {'job_id':'../other'}, {'requirement_id':'http://evil.example'}, {'file_ids':['f1','f1']},
    {'file_ids':[['nested']]}, {'expected_revision':True}, {'expected_context_epoch':False},
    {'expected_context_epoch':-1}, {'input_hash':'A'*64}, {'question':'x'*1001},
    {'operation_key':' '}, {'source_ref':'bad\nref'}, {'binding':'foreign'}, {'url':'https://evil.example'},
])
def test_question_input_refused_before_network(backend,tmp_path,change):
    config,state=backend
    _,config=configured(tmp_path,config.origin)
    args={**question(),**change}
    with pytest.raises(tools.RpcError):tools.DeliveryClient(config).call('delivery_propose_question',args)
    assert not state['calls']


@pytest.mark.parametrize('change', [
    {'question_id':'../other'}, {'question_input_hash':'bad'}, {'reported_speaker':'x'*121},
    {'text':'x'*2001}, {'source_ref':None}, {'resolve':True}, {'text':'bad\x00text'},
])
def test_reply_is_hash_bound_and_cannot_smuggle_resolution(backend,tmp_path,change):
    config,state=backend
    _,config=configured(tmp_path,config.origin)
    with pytest.raises(tools.RpcError):tools.DeliveryClient(config).call('delivery_record_reply',{**reply(),**change})
    assert not state['calls']


def test_exact_operation_retries_and_context_status_redaction(backend,tmp_path):
    config,state=backend
    _,config=configured(tmp_path,config.origin)
    client=tools.DeliveryClient(config)
    args=question()
    client.call('delivery_propose_question',args)
    client.call('delivery_propose_question',args)
    assert state['calls'][0]['body'] == state['calls'][1]['body']
    state['body']={'data':{'state':'clarification_pending','context_epoch':2,
        'questions':[{'question_id':'q1','requirement_id':'r1','state':'pending','input_hash':'a'*64,
                      'question':'PRIVATE QUESTION','replies':[{'text':'PRIVATE REPLY'}]}],
        'resolutions':['PRIVATE REASON'],'delivery_context_basis':['PRIVATE BASIS']}}
    status=client.call('delivery_status',{'job_id':'job'})
    assert 'PRIVATE' not in json.dumps(status)
    assert status['context_epoch'] == 2 and status['questions'][0]['question_id'] == 'q1'
    with pytest.raises(tools.RpcError):client.call('delivery_resolve',{})
