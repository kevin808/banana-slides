from models.project import Project


def test_project_to_dict_defaults_icon_subject_extraction_to_false():
    project = Project(creation_type='idea', idea_prompt='test')
    project.enable_icon_subject_extraction = None

    data = project.to_dict()

    assert data['enable_icon_subject_extraction'] is False


def test_project_to_dict_preserves_explicit_icon_subject_extraction_flag():
    project = Project(creation_type='idea', idea_prompt='test')
    project.enable_icon_subject_extraction = True

    data = project.to_dict()

    assert data['enable_icon_subject_extraction'] is True
