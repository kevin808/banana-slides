import importlib
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
BACKEND_ROOT = PROJECT_ROOT / "backend"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


def _create_isolated_app(monkeypatch, tmp_path):
    db_path = tmp_path / "task-recovery.db"
    db_uri = f"sqlite:///{db_path}"

    monkeypatch.setenv("DATABASE_URL", db_uri)
    monkeypatch.setenv("TESTING", "true")
    monkeypatch.setenv("USE_MOCK_AI", "true")
    monkeypatch.setenv("FLASK_ENV", "testing")

    config_module = importlib.import_module("config")
    importlib.reload(config_module)
    app_module = importlib.import_module("app")
    app_module = importlib.reload(app_module)

    flask_app = app_module.create_app()
    flask_app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI=db_uri,
        UPLOAD_FOLDER=str(tmp_path),
    )

    from models import db

    with flask_app.app_context():
        db.create_all()

    return flask_app


def test_recover_orphaned_editable_export_with_existing_file(monkeypatch, tmp_path):
    flask_app = _create_isolated_app(monkeypatch, tmp_path)

    from models import db, Project, Task
    from services.task_manager import recover_orphaned_tasks

    created_at = datetime.utcnow() - timedelta(minutes=30)

    with flask_app.app_context():
        project = Project(id="proj-recover", creation_type="descriptions", status="DRAFT")
        task = Task(
            id="task-recover",
            project_id=project.id,
            task_type="EXPORT_EDITABLE_PPTX",
            status="PENDING",
            created_at=created_at,
        )
        task.set_progress({
            "total": 100,
            "completed": 5,
            "failed": 0,
            "current_step": "开始分析 3 张图片（并发数: 4）...",
            "percent": 5,
            "messages": ["🚀 开始导出可编辑PPTX..."],
        })
        db.session.add(project)
        db.session.add(task)
        db.session.commit()

        exports_dir = tmp_path / project.id / "exports"
        exports_dir.mkdir(parents=True, exist_ok=True)
        output_file = exports_dir / f"presentation_{project.id}.pptx"
        output_file.write_bytes(b"fake-pptx")

        summary = recover_orphaned_tasks(str(tmp_path), stale_after_seconds=60)
        db.session.refresh(task)
        progress = task.get_progress()

        assert summary == {"recovered": 1, "failed": 0}
        assert task.status == "COMPLETED"
        assert task.completed_at is not None
        assert progress["percent"] == 100
        assert progress["download_url"] == f"/files/{project.id}/exports/{output_file.name}"
        assert progress["filename"] == output_file.name
        assert progress["recovered_after_restart"] is True


def test_recover_orphaned_task_marks_failed_when_no_output_exists(monkeypatch, tmp_path):
    flask_app = _create_isolated_app(monkeypatch, tmp_path)

    from models import db, Project, Task
    from services.task_manager import recover_orphaned_tasks

    created_at = datetime.utcnow() - timedelta(minutes=30)

    with flask_app.app_context():
        project = Project(id="proj-fail", creation_type="descriptions", status="DRAFT")
        task = Task(
            id="task-fail",
            project_id=project.id,
            task_type="EXPORT_EDITABLE_PPTX",
            status="RUNNING",
            created_at=created_at,
        )
        task.set_progress({
            "total": 100,
            "completed": 5,
            "failed": 0,
            "current_step": "开始分析 3 张图片（并发数: 4）...",
            "percent": 5,
            "messages": ["🚀 开始导出可编辑PPTX..."],
        })
        db.session.add(project)
        db.session.add(task)
        db.session.commit()

        summary = recover_orphaned_tasks(str(tmp_path), stale_after_seconds=60)
        db.session.refresh(task)
        progress = task.get_progress()

        assert summary == {"recovered": 0, "failed": 1}
        assert task.status == "FAILED"
        assert task.completed_at is not None
        assert "backend restart" in task.error_message.lower()
        assert progress["current_step"] == "任务中断"
        assert progress["recovered_after_restart"] is True
