"""UI checks for the saved sample and independent new-analysis workspace."""
import copy,importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

@unittest.skipUnless(importlib.util.find_spec('streamlit'),'Install requirements.txt for UI tests')
class AppTests(unittest.TestCase):
    def app(self):
        from streamlit.testing.v1 import AppTest
        app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=45).run()
        self.assertFalse(app.exception)
        return app
    def new(self):
        app=self.app();app.radio(key='workspace').set_value('New analysis').run()
        self.assertFalse(app.exception);return app
    def live(self):
        from test_ai_engine import episode,row,settings,response
        import ai_engine
        app=self.new();ep=episode()
        app.session_state['episodes']=[ep];app.session_state['input_id']='test-input'
        app.session_state['run']=ai_engine.analyse([ep],settings(),transport=lambda *_:response(row(ep)))
        app.run();self.assertFalse(app.exception);return app
    def test_sample_is_default_with_fifty_decisions_and_no_key(self):
        import json
        with open(ROOT/'raw_outputs/promos.json') as f:
            expected_promos=str(len(json.load(f)['promos']))
        with patch('ai_engine.analyse') as call:
            app=self.app()
        self.assertEqual(app.radio(key='workspace').value,'Sample results · 50 episodes')
        self.assertEqual(app.metric[0].value,'50/50')
        self.assertEqual(app.metric[1].value,expected_promos)
        self.assertFalse(any(t.label=='API key' for t in app.text_input))
        self.assertFalse(any(b.label.startswith('Find promos') for b in app.button))
        self.assertEqual(call.call_count,0)
    def test_new_analysis_starts_independently_without_sample_results(self):
        app=self.new()
        self.assertTrue(any('Upload scripts to start' in i.value for i in app.info))
        self.assertNotIn('run',app.session_state)
        self.assertEqual(len(app.metric),0)
    def test_switching_sample_does_not_overwrite_new_results(self):
        app=self.live();before=copy.deepcopy(app.session_state['run'])
        app.radio(key='workspace').set_value('Sample results · 50 episodes').run()
        self.assertEqual(app.metric[0].value,'50/50')
        self.assertEqual(app.session_state['run'],before)
        app.radio(key='workspace').set_value('New analysis').run()
        self.assertEqual(app.metric[0].value,'1/1')
        self.assertEqual(app.session_state['run'],before)
    def test_key_enables_fresh_analysis_action(self):
        app=self.live()
        next(t for t in app.text_input if t.label=='API key').set_value('test-key').run()
        run=copy.deepcopy(app.session_state['run'])
        with patch('ai_engine.analyse',return_value=run) as call:
            next(b for b in app.button if b.label.startswith('Find promos')).click().run()
        self.assertFalse(app.exception);self.assertEqual(call.call_count,1)
    def test_explain_chat_uses_new_uploaded_episode(self):
        app=self.live()
        next(t for t in app.text_input if t.label=='API key').set_value('test-key').run()
        with patch('ai_engine.explain',return_value='Check E101B001 at 00:00.00.') as call:
            app.chat_input[0].set_value('Why this hook?').run()
        self.assertFalse(app.exception);self.assertEqual(call.call_args.args[0]['episode'],101)
    def test_refine_applies_only_to_new_analysis(self):
        app=self.live()
        next(t for t in app.text_input if t.label=='API key').set_value('test-key').run()
        next(r for r in app.radio if r.label=='Editor action').set_value('Refine cut').run()
        row=copy.deepcopy(app.session_state['run']['decisions'][0]);row['reason']='Reconsidered the identity hook.'
        with patch('ai_engine.decision_for',return_value=(row,[])):
            app.chat_input[0].set_value('Find a clear identity hook.').run()
        self.assertFalse(app.exception);self.assertEqual(app.session_state['run']['decisions'][0]['reason'],row['reason'])
    def test_clear_session_returns_to_fixed_sample_without_key(self):
        app=self.live()
        next(t for t in app.text_input if t.label=='API key').set_value('test-key').run()
        next(b for b in app.button if b.label=='Clear session and key').click().run()
        self.assertFalse(app.exception);self.assertNotIn('run',app.session_state)
        self.assertEqual(app.radio(key='workspace').value,'Sample results · 50 episodes')
    def test_missing_private_sample_fails_clearly_without_synthetic_substitution(self):
        with patch('sample_data.load_sample',return_value=None):app=self.app()
        self.assertTrue(any('private submission bundle' in x.value for x in app.warning))
        self.assertEqual(len(app.metric),0)

if __name__=='__main__':unittest.main()
