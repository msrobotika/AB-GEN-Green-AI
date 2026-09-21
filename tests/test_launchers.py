from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


def _assert_trusted_runtime_contract(script: str):
    assert "artifacts\\abgen_bundle.pkl" in script
    assert "artifacts\\sample_data.pkl" in script
    assert "artifacts\\training_module.py" in script
    assert "artifacts\\runtime-manifest.json" in script
    assert "ABGEN_REQUIRE_MANIFEST=1" in script
    assert (
        "Do not search parent folders" in script
        or "AB-GEN evidence/release package" in script
    )


def test_demo_launcher_requires_complete_trusted_runtime_set():
    script = _read("run_demo.bat")

    _assert_trusted_runtime_contract(script)
    assert "export_bundle.py" not in script
    assert "python app.py" in script
    assert "exit /b 2" in script
    assert "exit /b 3" in script


def test_production_launcher_requires_complete_trusted_runtime_set():
    script = _read("run_production.bat")

    _assert_trusted_runtime_contract(script)
    assert "requirements_prod.txt" in script
    assert "python serve.py" in script
    assert "exit /b 2" in script
    assert "exit /b 3" in script
