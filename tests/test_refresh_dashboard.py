import json
import os
from pathlib import Path
import subprocess
import sys

import pytest
import requests
import yaml

from scripts.refresh_dashboard import refresh, PUBLIC_URL


@pytest.mark.parametrize('status', ['current', 'degraded', 'blocked'])
def test_workflow_passes_validated_snapshot_to_dashboard(tmp_path, status):
    """A merge must preserve the producer output through the deploy job."""
    workflow = yaml.safe_load((Path(__file__).resolve().parents[1] /
                               '.github/workflows/daily.yml').read_text())
    producer = workflow['jobs']['run']
    deploy = workflow['jobs']['deploy']
    health_step = next(step for step in producer['steps'] if step.get('id') == 'health')
    script = health_step['run']
    emitter = script.split("python - <<'PYCODE'\n", 1)[1].split('\nPYCODE', 1)[0]
    (tmp_path / 'health.json').write_text(json.dumps({'status': status, 'snapshot_id': 'verified-123'}))
    output = tmp_path / 'github-output'
    subprocess.run([sys.executable, '-c', emitter], cwd=tmp_path, check=True,
                   env={**os.environ, 'GITHUB_OUTPUT': str(output)})
    values = dict(line.split('=', 1) for line in output.read_text().splitlines())
    assert values == {'status': status, 'snapshot_id': 'verified-123'}
    assert script.index('prepare_publication.py --verify') < script.index("python - <<'PYCODE'")
    assert producer['outputs']['snapshot_id'] == '${{ steps.health.outputs.snapshot_id }}'
    assert producer['outputs']['data_status'] == '${{ steps.health.outputs.status }}'
    assert producer['timeout-minutes'] == 90
    assert deploy['needs'] == 'run'
    assert deploy['if'] == "github.ref == 'refs/heads/main'"
    refresh_step = next(step for step in deploy['steps']
                        if 'scripts/refresh_dashboard.py' in step.get('run', ''))
    assert refresh_step['env']['PRODUCER_SNAPSHOT_ID'] == '${{ needs.run.outputs.snapshot_id }}'
    assert '--snapshot-id "$PRODUCER_SNAPSHOT_ID"' in refresh_step['run']


class Response:
    def __init__(self, code=200, health=None, text=''):
        self.status_code, self.health, self.text = code, health, text
    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(str(self.status_code))
    def json(self):
        return self.health


class Session:
    def __init__(self, responses=(), code=204):
        self.responses, self.code, self.posts, self.gets = iter(responses), code, [], []
    def post(self, url, **kwargs):
        self.posts.append((url, kwargs))
        return Response(self.code)
    def get(self, url, **kwargs):
        self.gets.append((url, kwargs))
        return next(self.responses)


class Clock:
    def __init__(self): self.value = 0
    def __call__(self): return self.value
    def sleep(self, seconds): self.value += seconds


def test_missing_token_cannot_report_success():
    session = Session()
    with pytest.raises(ValueError, match='NOT verified'):
        refresh('new', '', session=session)
    assert not session.posts


def test_missing_snapshot_refuses_dispatch():
    with pytest.raises(ValueError, match='snapshot ID'):
        refresh('', 'secret', session=Session())


@pytest.mark.parametrize('code', [200, 302, 401, 403, 404, 422, 500])
def test_non_204_dispatch_does_not_poll_or_leak_token(code):
    session = Session(code=code)
    with pytest.raises(RuntimeError, match=f'HTTP {code}') as exc:
        refresh('new', 'sensitive-token', session=session)
    assert 'sensitive-token' not in str(exc.value)
    assert not session.gets


@pytest.mark.parametrize('status', ['current', 'degraded', 'blocked'])
def test_waits_for_matching_health_and_page_without_sending_credential_to_pages(status):
    health = {'snapshot_id': 'new', 'status': status}
    session = Session([Response(health={'snapshot_id': 'old'}), Response(health=health),
                       Response(text='new verifyObservationHealth')])
    clock = Clock()
    assert refresh('new', 'secret', session=session, clock=clock, sleep=clock.sleep) == health
    assert clock.value == 15
    assert len(session.posts) == 1
    assert session.posts[0][1]['json']['inputs'] == {'snapshot_id': 'new'}
    assert session.posts[0][1]['allow_redirects'] is False
    assert all('Authorization' not in call[1]['headers'] for call in session.gets)
    assert all(call[0].startswith(PUBLIC_URL) for call in session.gets)


@pytest.mark.parametrize('response', [Response(health=None), Response(health={'snapshot_id': 'old'}),
                                     Response(health={'snapshot_id': 'new', 'status': 'unknown'}), Response(code=503)])
def test_dispatch_acceptance_is_not_publication_success(response):
    clock = Clock()
    with pytest.raises(RuntimeError, match='not verified before timeout'):
        refresh('new', 'secret', session=Session([response]), timeout=1, clock=clock, sleep=clock.sleep)


def test_matching_health_but_old_page_never_passes():
    clock = Clock()
    session = Session([Response(health={'snapshot_id': 'new', 'status': 'current'}), Response(text='old verifyObservationHealth')])
    with pytest.raises(RuntimeError, match='page does not match'):
        refresh('new', 'secret', session=session, timeout=1, clock=clock, sleep=clock.sleep)


@pytest.mark.parametrize('status,exit_code', [('current', 0), ('degraded', 0), ('blocked', 1)])
def test_cli_fails_for_blocked_dashboard_even_when_delivery_matches(monkeypatch, status, exit_code):
    import scripts.refresh_dashboard as module
    monkeypatch.setattr(module, 'refresh', lambda *args: {'snapshot_id': 'new', 'status': status})
    assert module.main(['--snapshot-id', 'new']) == exit_code


def test_late_success_does_not_escape_deadline():
    clock = Clock()
    class SlowSession(Session):
        def get(self, url, **kwargs):
            assert kwargs['timeout'] <= 3 - clock.value
            response = super().get(url, **kwargs)
            clock.value += 2
            return response
    session = SlowSession([Response(health={'snapshot_id': 'new', 'status': 'current'}),
                           Response(text='new verifyObservationHealth')])
    with pytest.raises(RuntimeError, match='deadline reached'):
        refresh('new', 'secret', session=session, timeout=3, clock=clock, sleep=clock.sleep)
