import os


def test_normal_host_still_requires_access_code(client):
    os.environ['ACCESS_CODE'] = 'kevin'
    os.environ['ACCESS_CODE_BYPASS_HOSTS'] = 'openclaw-nopass.pptmagic.tech'

    try:
        response = client.get('/api/access-code/check', headers={'Host': 'pptmagic.tech'})
        assert response.status_code == 200
        assert response.get_json()['data']['enabled'] is True

        protected = client.post(
            '/api/projects',
            headers={'Host': 'pptmagic.tech'},
            json={'creation_type': 'idea', 'idea_prompt': 'test'},
        )
        assert protected.status_code == 403
    finally:
        os.environ.pop('ACCESS_CODE', None)
        os.environ.pop('ACCESS_CODE_BYPASS_HOSTS', None)


def test_bypass_host_skips_access_code_and_check_endpoint(client):
    os.environ['ACCESS_CODE'] = 'kevin'
    os.environ['ACCESS_CODE_BYPASS_HOSTS'] = 'openclaw-nopass.pptmagic.tech'

    try:
        response = client.get(
            '/api/access-code/check',
            headers={'Host': 'openclaw-nopass.pptmagic.tech'},
        )
        assert response.status_code == 200
        assert response.get_json()['data']['enabled'] is False

        verify = client.post(
            '/api/access-code/verify',
            headers={'Host': 'openclaw-nopass.pptmagic.tech'},
            json={'code': 'wrong-code'},
        )
        assert verify.status_code == 200
        assert verify.get_json()['data']['valid'] is True

        allowed = client.post(
            '/api/projects',
            headers={'Host': 'openclaw-nopass.pptmagic.tech'},
            json={'creation_type': 'idea', 'idea_prompt': 'test'},
        )
        assert allowed.status_code == 201
    finally:
        os.environ.pop('ACCESS_CODE', None)
        os.environ.pop('ACCESS_CODE_BYPASS_HOSTS', None)


def test_wildcard_bypass_host_is_supported(client):
    os.environ['ACCESS_CODE'] = 'kevin'
    os.environ['ACCESS_CODE_BYPASS_HOSTS'] = '*.nopass.pptmagic.tech'

    try:
        response = client.get(
            '/api/access-code/check',
            headers={'Host': 'openclaw.nopass.pptmagic.tech'},
        )
        assert response.status_code == 200
        assert response.get_json()['data']['enabled'] is False
    finally:
        os.environ.pop('ACCESS_CODE', None)
        os.environ.pop('ACCESS_CODE_BYPASS_HOSTS', None)
