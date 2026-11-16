"""Dispatch the dashboard and verify its public snapshot, never just HTTP 204.

The cross-repository token is supplied only through the environment. It needs
Actions: write on oslo-screener-dashboard, not access to unrelated repositories.
"""
import argparse
import os
import time

import requests

DISPATCH_URL = 'https://api.github.com/repos/keresell-coder/oslo-screener-dashboard/actions/workflows/daily.yml/dispatches'
PUBLIC_URL = 'https://keresell-coder.github.io/oslo-screener-dashboard/'


def refresh(snapshot_id, token, *, timeout=900, interval=15, session=None,
            clock=time.monotonic, sleep=time.sleep):
    if timeout <= 0 or interval <= 0:
        raise ValueError('timeout and interval must be positive')
    if not snapshot_id:
        raise ValueError('Missing producer snapshot ID; refusing untraceable dispatch')
    if not token:
        raise ValueError('DASHBOARD_WORKFLOW_TOKEN is not configured. Producer publication is separate; dashboard refresh is NOT verified.')
    session = session or requests.Session()
    # Do not retry an ambiguous POST: a timeout may already have queued a run.
    response = session.post(
        DISPATCH_URL,
        headers={'Accept': 'application/vnd.github+json',
                 'Authorization': f'Bearer {token}',
                 'X-GitHub-Api-Version': '2022-11-28'},
        json={'ref': 'main', 'inputs': {'snapshot_id': snapshot_id}},
        timeout=30, allow_redirects=False,
    )
    if response.status_code != 204:
        raise RuntimeError(f'Dashboard dispatch was not accepted (HTTP {response.status_code}); check repository access and Actions: write permission')
    deadline = clock() + timeout
    last_error = 'dashboard has not published the requested snapshot'
    while clock() < deadline:
        try:
            # Public verification never receives the credential header.
            headers = {'Cache-Control': 'no-cache', 'User-Agent': 'oslo-screener-publication-check/1.0'}
            health_response = session.get(PUBLIC_URL + 'health.json', headers=headers, timeout=min(10, deadline - clock()))
            health_response.raise_for_status()
            health = health_response.json()
            if health.get('snapshot_id') != snapshot_id:
                raise ValueError('public dashboard still has a different snapshot')
            if health.get('status') not in {'current', 'degraded', 'blocked'}:
                raise ValueError('public dashboard health has an invalid status')
            remaining = deadline - clock()
            if remaining <= 0:
                raise ValueError('public verification deadline reached')
            page = session.get(PUBLIC_URL, headers=headers, timeout=min(10, remaining))
            page.raise_for_status()
            if snapshot_id not in page.text or 'verifyObservationHealth' not in page.text:
                raise ValueError('public dashboard page does not match its health manifest')
            if clock() > deadline:
                raise ValueError('public verification deadline reached')
            return health
        except (requests.RequestException, ValueError, TypeError, AttributeError) as exc:
            last_error = str(exc)
        remaining = deadline - clock()
        if remaining > 0:
            sleep(min(interval, remaining))
    raise RuntimeError(f'Dashboard dispatch accepted but public refresh not verified before timeout: {last_error}')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot-id', required=True)
    args = parser.parse_args(argv)
    health = refresh(args.snapshot_id, os.environ.get('DASHBOARD_WORKFLOW_TOKEN', ''))
    print(f"Verified public dashboard snapshot {health['snapshot_id']} (status={health['status']})")
    if health['status'] == 'blocked':
        print('Dashboard was published safely but remains blocked; refresh chain is not healthy.')
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
