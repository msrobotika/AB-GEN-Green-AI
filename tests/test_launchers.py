from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


def test_demo_launcher_requires_runtime_artifacts_without_parent_export_guessing():
    script = _read("run_demo.bat")

    assert 'if not exist "abgen_bundle.pkl" goto :missing_artifacts' in script
    assert 'if not exist "sample_data.pkl" goto :missing_artifacts' in script
    assert "export_bundle.py" not in script
    assert "assumed parent folder" in script
    assert "exit /b 2" in script


def test_production_launcher_requires_runtime_artifacts():
    script = _read("run_production.bat")

    assert 'if not exist "abgen_bundle.pkl" goto :missing_artifacts' in script
    assert 'if not exist "sample_data.pkl" goto :missing_artifacts' in script
    assert "validated AB-GEN release process" in script
    assert "exit /b 2" in script
