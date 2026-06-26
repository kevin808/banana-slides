from models import Page, Project, Task


def _create_project_with_page(db_session):
    project = Project(
        creation_type='idea',
        idea_prompt='test project',
        template_style='simple clean style',
        status='DESCRIPTIONS_GENERATED',
    )
    db_session.add(project)
    db_session.commit()

    page = Page(
        project_id=project.id,
        order_index=0,
        status='DESCRIPTION_GENERATED',
    )
    page.set_outline_content({'title': '封面', 'points': ['要点1']})
    page.set_description_content({'text': '一页测试描述'})
    db_session.add(page)
    db_session.commit()
    return project, page


def _create_completed_image_task(db_session, project_id, completed_count=1, task_type='GENERATE_IMAGES'):
    task = Task(
        project_id=project_id,
        task_type=task_type,
        status='COMPLETED',
    )
    task.set_progress({
        'total': completed_count,
        'completed': completed_count,
        'failed': 0,
    })
    db_session.add(task)
    db_session.commit()
    return task


def test_batch_generate_images_rejected_when_quota_exceeded(app, db_session):
    app.config['MAX_FREE_GENERATED_IMAGES'] = 1
    project, _ = _create_project_with_page(db_session)
    _create_completed_image_task(db_session, project.id, completed_count=1)

    with app.test_client() as client:
        response = client.post(
            f'/api/projects/{project.id}/generate/images',
            json={},
        )

    assert response.status_code == 429
    data = response.get_json()
    assert data['error']['code'] == 'RATE_LIMIT_EXCEEDED'
    assert '最多 1 张' in data['error']['message']


def test_material_generate_rejected_when_quota_exceeded(app, db_session):
    app.config['MAX_FREE_GENERATED_IMAGES'] = 1
    project, _ = _create_project_with_page(db_session)
    _create_completed_image_task(db_session, project.id, completed_count=1, task_type='GENERATE_MATERIAL')

    with app.test_client() as client:
        response = client.post(
            f'/api/projects/{project.id}/materials/generate',
            json={'prompt': '生成一张示意图'},
        )

    assert response.status_code == 429
    data = response.get_json()
    assert data['error']['code'] == 'RATE_LIMIT_EXCEEDED'
    assert '不足以继续生成 1 张图片' in data['error']['message']


def test_material_process_rejected_when_quota_exceeded(app, db_session):
    app.config['MAX_FREE_GENERATED_IMAGES'] = 1
    project, _ = _create_project_with_page(db_session)
    _create_completed_image_task(db_session, project.id, completed_count=1, task_type='PROCESS_MATERIAL')

    with app.test_client() as client:
        response = client.post(
            f'/api/projects/{project.id}/materials/process',
            data={
                'operation': 'generate',
                'prompt': '生成一张示意图',
            },
        )

    assert response.status_code == 429
    data = response.get_json()
    assert data['error']['code'] == 'RATE_LIMIT_EXCEEDED'
    assert '不足以继续生成 1 张图片' in data['error']['message']
