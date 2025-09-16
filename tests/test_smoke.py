import os


def test_project_structure_exists():
    # Minimal sanity: key directories are present in the repo
    for path in ["agents", "triad", "assets"]:
        assert os.path.isdir(path), f"Missing expected directory: {path}"
