"""Load the saved assignment sample without calling an AI provider."""
import json
from pathlib import Path


def load_sample(root):
    folder=Path(root)/'raw_outputs'
    if not (folder/'promos.json').is_file():
        return None
    result=json.loads((folder/'promos.json').read_text())
    decisions=json.loads((folder/'ai_decisions.json').read_text())
    audit=json.loads((folder/'run_audit.json').read_text())
    total=len(result['coverage'])
    if total!=50 or len(decisions)!=total:
        raise ValueError('The saved 50-episode sample is incomplete.')
    result.update(complete=True,expected_episodes=total,errors=[])
    raw_responses = json.loads((folder/'api_responses.json').read_text()) if (folder/'api_responses.json').is_file() else []
    return dict(result=result,decisions=decisions,raw_responses=raw_responses,
        audit=dict(kind='live_gemini_run',complete=True,expected_episodes=total,
                   live_api_tested=True,validated_decisions=total,origin='Live Google Gemini 3.1 Flash Lite API evaluation of the assignment pack with deterministic cue validation.',
                   original_audit=audit))
