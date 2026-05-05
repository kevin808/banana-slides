from models import AccessCode, Page, Project, db
from services.access_code_service import hash_code


def _reset_database():
    for table in reversed(db.metadata.sorted_tables):
        db.session.execute(table.delete())
    db.session.commit()


def _create_project_with_page():
    project = Project(
        creation_type='idea',
        idea_prompt='test project',
        template_style='simple clean style',
        status='DESCRIPTIONS_GENERATED',
    )
    db.session.add(project)
    db.session.commit()

    page = Page(
        project_id=project.id,
        order_index=0,
        status='DESCRIPTION_GENERATED',
    )
    page.set_outline_content({'title': '封面', 'points': ['要点1']})
    page.set_description_content({'text': '一页测试描述'})
    db.session.add(page)
    db.session.commit()
    return project, page


def test_check_and_verify_member_access_code(app):
    try:
        with app.app_context():
            _reset_database()
            member_code = AccessCode(
                code_hash=hash_code('vip-001'),
                plan_name='monthly',
                max_generate_requests=3,
                max_export_requests=1,
                used_generate_requests=1,
            )
            db.session.add(member_code)
            db.session.commit()

        with app.test_client() as client:
            check_response = client.get('/api/access-code/check')
            assert check_response.status_code == 200
            assert check_response.get_json()['data']['enabled'] is True

            verify_response = client.post('/api/access-code/verify', json={'code': 'vip-001'})
            assert verify_response.status_code == 200
            assert verify_response.get_json()['data'] == {
                'valid': True,
                'plan_name': 'monthly',
                'remaining': {'generate': 2, 'export': 1},
            }
    finally:
        with app.app_context():
            _reset_database()


def test_generate_request_is_blocked_when_member_quota_is_exhausted(app):
    try:
        with app.app_context():
            _reset_database()
            project, _ = _create_project_with_page()
            project_id = project.id
            member_code = AccessCode(
                code_hash=hash_code('vip-limit'),
                plan_name='trial',
                max_generate_requests=1,
                used_generate_requests=1,
            )
            db.session.add(member_code)
            db.session.commit()

        with app.test_client() as client:
            response = client.post(
                f'/api/projects/{project_id}/generate/images',
                headers={'X-Access-Code': 'vip-limit'},
                json={},
            )

            assert response.status_code == 429
            assert response.get_json() == {
                'error': 'Quota exceeded',
                'data': {'bucket': 'generate'},
            }
    finally:
        with app.app_context():
            _reset_database()


def test_material_process_request_is_blocked_when_member_quota_is_exhausted(app):
    try:
        with app.app_context():
            _reset_database()
            project, _ = _create_project_with_page()
            project_id = project.id
            member_code = AccessCode(
                code_hash=hash_code('vip-process'),
                plan_name='trial',
                max_generate_requests=1,
                used_generate_requests=1,
            )
            db.session.add(member_code)
            db.session.commit()

        with app.test_client() as client:
            response = client.post(
                f'/api/projects/{project_id}/materials/process',
                headers={'X-Access-Code': 'vip-process'},
                data={
                    'operation': 'generate',
                    'prompt': '生成一张示意图',
                },
            )

            assert response.status_code == 429
            assert response.get_json() == {
                'error': 'Quota exceeded',
                'data': {'bucket': 'generate'},
            }
    finally:
        with app.app_context():
            _reset_database()
