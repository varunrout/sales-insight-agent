from pathlib import Path

import config


def test_config_paths_are_path_objects():
    path_settings = [
        config.DATA_PATH,
        config.DOCS_PATH,
        config.QUESTIONS_PATH,
        config.VECTOR_STORE_PATH,
        config.CHART_OUTPUT_PATH,
        config.MODEL_OUTPUT_PATH,
    ]

    assert all(isinstance(path, Path) for path in path_settings)


def test_config_source_paths_are_importable_and_existing():
    assert config.DATA_PATH.exists()
    assert config.DOCS_PATH.exists()
    assert config.QUESTIONS_PATH.exists()
