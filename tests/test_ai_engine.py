import copy, io, json, sys, unittest, zipfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import ai_engine as ai

SAMPLE=(Path(__file__).resolve().parents[1]/'examples/synthetic_episode.txt').read_bytes()
def episode(n=101):
    return ai.uploaded_episodes([(f'{n}.txt',SAMPLE.replace(b'Episode 101',f'Episode {n}'.encode()))])[0]
def row(e):
    n=e['episode']
    return dict(episode=n,source_sha256=e['sha256'],status='select',reason='Unresolved identity.',segments=[dict(start='00:00.00',end='00:24.50')],hook_id=f'E{n:03d}B001',cliff_id=f'E{n:03d}B007',ratings=dict(hook=5,cliff=4,context=5),open_question='Who is the bride?',flags=[])
def response(obj):
    return dict(choices=[dict(finish_reason='stop',message=dict(content=json.dumps(obj)))],usage=dict(prompt_tokens=100,completion_tokens=50))
def settings(**kw):
    values=dict(provider='OpenAI',model='test-model',key='test-secret-never-export',brief='Prefer mystery')
    values.update(kw);return ai.Settings(**values)

class EngineTests(unittest.TestCase):
    def test_fresh_unseen_episodes_generalize_and_rank(self):
        eps=[episode(7),episode(88)]
        def model(s,messages):return response(row(json.loads(messages[1]['content'])['screenplay']))
        run=ai.analyse(eps,settings(),transport=model)
        self.assertTrue(run['result']['complete']);self.assertEqual([p['episode'] for p in run['result']['promos']],[7,88])
    def test_invalid_cut_gets_one_repair(self):
        e=episode();bad=row(e);bad['segments'][0]['end']='00:24.00'
        calls=[]
        def model(s,m):
            calls.append(copy.deepcopy(m));return response(bad if len(calls)==1 else row(e))
        r,traces=ai.decision_for(e,settings(),transport=model)
        self.assertEqual(len(calls),2);self.assertIn('Validation error',calls[1][-1]['content']);self.assertEqual(len(traces),2)
    def test_persistently_bad_cut_is_failure_not_pass(self):
        e=episode();bad=row(e);bad['source_sha256']='fake'
        run=ai.analyse([e],settings(),transport=lambda *_:response(bad))
        self.assertFalse(run['result']['complete']);self.assertEqual(run['decisions'],[]);self.assertEqual(len(run['result']['errors']),1)
    def test_auth_failure_stops_batch_and_is_explicit(self):
        calls=[]
        def fail(*a):calls.append(1);raise ai.ModelError('Key rejected',401)
        run=ai.analyse([episode(1),episode(2)],settings(),transport=fail)
        self.assertEqual(len(calls),1);self.assertEqual(len(run['result']['errors']),2)
    def test_session_cache_avoids_repeat_calls_and_brief_change_invalidates(self):
        e=episode();cache={};calls=[]
        def model(*a):calls.append(1);return response(row(e))
        ai.analyse([e],settings(),cache=cache,transport=model)
        second=ai.analyse([e],settings(),cache=cache,transport=model)
        ai.analyse([e],settings(brief='Less violence'),cache=cache,transport=model)
        self.assertEqual(len(calls),2);self.assertEqual(second['audit']['cache_hits'],1)
    def test_refine_contains_source_and_editor_feedback(self):
        e=episode();seen=[]
        def model(s,m):seen.extend(m);return response(row(e))
        ai.decision_for(e,settings(),transport=model,feedback='Prefer clear identity',previous=row(e))
        data=json.loads(seen[1]['content']);self.assertEqual(data['editor_feedback'],'Prefer clear identity');self.assertEqual(data['screenplay']['sha256'],e['sha256'])
    def test_explanation_uses_only_focused_episode(self):
        seen=[]
        def model(s,m):seen.extend(m);return response(dict(answer='See E101B001 at 00:00.00.'))
        answer=ai.explain(episode(),row(episode()),'Why this opening?',settings(),transport=model)
        self.assertIn('E101B001',answer);self.assertIn('ONLY',seen[0]['content'])
    def test_export_does_not_contain_key_and_records_api_provenance(self):
        run=ai.analyse([episode()],settings(),transport=lambda *_:response(row(episode())))
        with zipfile.ZipFile(io.BytesIO(ai.export_zip(run))) as z:
            text=''.join(z.read(n).decode() for n in z.namelist())
            self.assertNotIn(settings().key,text);self.assertIn('fresh_api_analysis',text)
            self.assertEqual(len(json.loads(z.read('ai_decisions.json'))),1)
        self.assertNotIn(settings().key,repr(settings()))
    def test_corrupt_zip_is_actionable(self):
        with self.assertRaisesRegex(ValueError,'corrupt'):ai.uploaded_episodes([('bad.zip',b'not a zip')])
    def test_zip_duplicate_episode_numbers_rejected(self):
        buf=io.BytesIO()
        with zipfile.ZipFile(buf,'w') as z:
            z.writestr('a.txt',SAMPLE);z.writestr('b.txt',SAMPLE)
        with self.assertRaisesRegex(ValueError,'duplicate'):ai.uploaded_episodes([('input.zip',buf.getvalue())])
    def test_unknown_txt_format_rejected(self):
        with self.assertRaisesRegex(ValueError,'header'):ai.uploaded_episodes([('script.txt',b'Once upon a time')])
    def test_provider_http_error_body_not_echoed(self):
        import urllib.error
        err=urllib.error.HTTPError('https://example.invalid',401,'leaked-secret',None,io.BytesIO(b'leaked-secret'))
        with patch('ai_engine.open_request',side_effect=err):
            with self.assertRaises(ai.ModelError) as cm:ai.completion(settings(),[])
        self.assertNotIn('leaked',str(cm.exception));self.assertEqual(cm.exception.status,401)
    def test_requested_duration_is_enforced(self):
        with self.assertRaisesRegex(ValueError,'requested'):ai.validate_decision(episode(),row(episode()),settings(min_seconds=30))
    def test_http_payload_uses_selected_provider_without_global_env(self):
        class Response(io.BytesIO):
            def __enter__(self):return self
            def __exit__(self,*a):self.close()
        seen=[]
        def send(req,timeout):
            seen.append(req);return Response(json.dumps(response(row(episode()))).encode())
        with patch('ai_engine.open_request',side_effect=send):ai.completion(settings(),[dict(role='user',content='JSON')])
        self.assertEqual(json.loads(seen[0].data)['model'],'test-model')
        self.assertTrue(seen[0].full_url.startswith('https://api.openai.com/'))
    def test_comparative_ranking_resolves_ties_and_computes_stability(self):
        p1 = dict(episode=33, duration_seconds=30.0, score=96, hook=dict(text='Hook 1'), cliffhanger=dict(text='Cliff 1'), open_question='Q1', evidence=[])
        p2 = dict(episode=46, duration_seconds=32.0, score=96, hook=dict(text='Hook 2'), cliffhanger=dict(text='Cliff 2'), open_question='Q2', evidence=[])
        def mock_rank(s, messages):
            user_text = messages[1]['content']
            # Return forced ranking based on episodes
            return response(dict(ranking=[
                dict(rank=1, episode=33, reason='Stronger hook'),
                dict(rank=2, episode=46, reason='Good cliffhanger')
            ]))
        ranked, rho, audit = ai.rank_comparative([p1, p2], settings(), transport=mock_rank)
        self.assertEqual(len(ranked), 2)
        self.assertEqual(ranked[0]['comparative_rank'], 1)
        self.assertEqual(ranked[0]['episode'], 33)
        self.assertEqual(ranked[1]['comparative_rank'], 2)
        self.assertEqual(ranked[1]['episode'], 46)
        self.assertEqual(rho, 1.0)
        self.assertTrue(audit['comparative'])
    def test_comparative_ranking_single_or_empty_returns_cleanly(self):
        ranked, rho, audit = ai.rank_comparative([], settings())
        self.assertEqual(ranked, [])
        self.assertEqual(rho, 1.0)
        single = [dict(episode=10, duration_seconds=25.0, score=90, why='test')]
        ranked, rho, audit = ai.rank_comparative(single, settings())
        self.assertEqual(len(ranked), 1)
        self.assertEqual(ranked[0]['comparative_rank'], 1)
    def test_analyse_executes_comparative_ranking_pass(self):
        eps = [episode(7), episode(88)]
        def smart_model(s, messages):
            content = messages[1]['content']
            if 'Candidate Episode' in content:
                return response(dict(ranking=[
                    dict(rank=1, episode=88, reason='Superior narrative urgency'),
                    dict(rank=2, episode=7, reason='Slightly slower hook')
                ]))
            data = json.loads(content)
            return response(row(data['screenplay']))
        run = ai.analyse(eps, settings(), transport=smart_model)
        self.assertTrue(run['result']['complete'])
        promos = run['result']['promos']
        self.assertEqual(len(promos), 2)
        self.assertEqual(promos[0]['episode'], 88)
        self.assertEqual(promos[0]['rank'], 1)
        self.assertEqual(promos[0]['comparative_rank'], 1)
        self.assertEqual(promos[1]['episode'], 7)
        self.assertEqual(promos[1]['rank'], 2)
        self.assertIn('comparative_ranking', run['audit'])
        self.assertTrue(run['audit']['comparative_ranking']['comparative'])
        self.assertTrue(any(t.get('stage') == 'comparative_ranking_pass_a' for t in run['raw_responses']))
    def test_promo_validate_preserves_and_sorts_by_comparative_rank(self):
        import promo
        e1 = episode(1); e2 = episode(2)
        r1 = row(e1); r2 = row(e2)
        r1['ratings'] = dict(hook=5, cliff=5, context=5)
        r2['ratings'] = dict(hook=5, cliff=5, context=5)
        r2['comparative_rank'] = 1
        r2['comparative_reason'] = 'Tighter hook'
        r1['comparative_rank'] = 2
        r1['comparative_reason'] = 'Slightly slower'
        res = promo.validate([e1, e2], [r1, r2])
        self.assertEqual(res['promos'][0]['episode'], 2)
        self.assertEqual(res['promos'][0]['rank'], 1)
        self.assertEqual(res['promos'][0]['comparative_rank'], 1)
        self.assertEqual(res['promos'][1]['episode'], 1)
        self.assertEqual(res['promos'][1]['rank'], 2)

if __name__=='__main__':unittest.main()
