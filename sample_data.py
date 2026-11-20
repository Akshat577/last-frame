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
    return dict(result=result,decisions=decisions,raw_responses=[],
        audit=dict(kind='saved_50_episode_sample',complete=True,expected_episodes=total,
                   validated_decisions=total,origin='Saved Codex editorial review of the assignment pack; Python-validated cuts. Not a fresh API run.',
                   original_audit=audit))
