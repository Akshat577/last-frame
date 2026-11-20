import copy, importlib.util, io, json, tempfile, unittest, zipfile
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import promo

SAMPLE='''EPISODE NUMBER: Episode 1
--- SCRIPT START ---
**CAMERA:**
Start: (00:00.00) | End: (00:30.00)
A courtroom.

**JUDGE:**
Start: (00:00.00) | End: (00:04.00)
"Your husband will die unless you confess."

**CAMERA:**
Start: (00:02.00) | End: (00:20.00)
Her reaction.

**WOMAN:**
Start: (00:20.00) | End: (00:25.00)
"Tell me what I have to do."

**JUDGE:**
Start: (00:25.00) | End: (00:28.00)
"Sign the confession."
--- SCRIPT END ---
'''
class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.pack=self.root/'input';self.pack.mkdir();(self.pack/'one.txt').write_text(SAMPLE)
        e=promo.read_pack(self.pack)[0]
        self.row=dict(episode=1,source_sha256=e['sha256'],status='select',reason='Threat plus an unresolved choice.',segments=[dict(start='00:00.00',end='00:25.00')],hook_id='E001B002',cliff_id='E001B004',ratings=dict(hook=5,cliff=4,context=4),open_question='Will she confess?',flags=[])
    def tearDown(self):self.tmp.cleanup()
    def run_rows(self,rows):
        f=self.root/'decisions.json';f.write_text(json.dumps(rows))
        with redirect_stdout(io.StringIO()):return promo.finish(self.pack,f,self.root/'result')
    def test_interval_duration_not_sum_of_overlapping_cues(self):
        r=self.run_rows([self.row]);self.assertEqual(r['promos'][0]['duration_seconds'],25)
    def test_dialogue_split_rejected_even_at_camera_boundary(self):
        row=copy.deepcopy(self.row);row['segments'][0]['start']='00:02.00'
        with self.assertRaisesRegex(ValueError,'splits dialogue'):self.run_rows([row])
    def test_missing_coverage_rejected(self):
        with self.assertRaisesRegex(ValueError,'Missing episode'):self.run_rows([])
    def test_stale_source_rejected(self):
        self.row['source_sha256']='bad'
        with self.assertRaisesRegex(ValueError,'Stale source'):self.run_rows([self.row])
    def test_wrong_evidence_rejected(self):
        self.row['cliff_id']='E001B005'
        with self.assertRaisesRegex(ValueError,'outside'):self.run_rows([self.row])
    def test_overlength_rejected(self):
        path=self.pack/'one.txt';path.write_text(SAMPLE.replace('00:25.00','01:05.00').replace('00:28.00','01:08.00'))
        self.row['source_sha256']=promo.read_pack(self.pack)[0]['sha256']
        self.row['segments'][0]['end']='01:05.00'
        with self.assertRaisesRegex(ValueError,'outside 20-60'):self.run_rows([self.row])
    def test_zip_and_directory_match(self):
        z=self.root/'input.zip'
        with zipfile.ZipFile(z,'w') as f:f.writestr('folder/one.txt',SAMPLE)
        self.assertEqual(promo.read_pack(z),promo.read_pack(self.pack))
    def test_resolved_answer_is_semantic_blind_spot(self):
        row=copy.deepcopy(self.row);row['segments'][0]['end']='00:28.00';row['cliff_id']='E001B005'
        # Structural validity does not prove a cliffhanger; deliberately keep this known limitation visible.
        self.assertEqual(len(self.run_rows([row])['promos']),1)
    def test_compatible_api_adapter_with_mock_not_live(self):
        raw={'choices':[{'message':{'content':json.dumps(self.row)}}]}
        class Response(io.BytesIO):
            def __enter__(self):return self
            def __exit__(self,*args):self.close()
        with patch.dict('os.environ',{'PROMO_API_URL':'http://localhost/mock','PROMO_MODEL':'test'}),patch('urllib.request.urlopen',return_value=Response(json.dumps(raw).encode())),redirect_stdout(io.StringIO()):
            promo.judge(self.pack,self.root/'model')
        self.assertEqual(json.loads((self.root/'model/ai_decisions.json').read_text())[0],self.row)
if __name__=='__main__':unittest.main()
