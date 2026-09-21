from pathlib import Path


TEMPLATE = Path(__file__).resolve().parents[1] / "templates" / "index.html"
README = Path(__file__).resolve().parents[1] / "README.md"


def test_demo_uses_explicit_evidence_states():
    html = TEMPLATE.read_text(encoding="utf-8")

    assert "AB-GEN Research Demo" in html
    assert "80.14% remains historical/report-only" in html
    assert "80.17% recovered cache path" in html
    assert "No validated value" in html
    assert "Pending measurement" in html
    assert "Batch dependence known" in html
    assert "deterministic stored order" in html


def test_demo_does_not_present_historical_energy_as_a_result():
    html = TEMPLATE.read_text(encoding="utf-8")

    prohibited = [
        "92.6% less energy",
        "92.6% energy",
        "0.31 mJ / inference",
        "4.2 mJ / inference",
        "Energy Saved vs ResNet",
        "Historical Energy Estimate vs ResNet",
        "AB-GEN 80% Accuracy",
        "AB-GEN vs Industry Models",
    ]
    for phrase in prohibited:
        assert phrase not in html


def test_readme_keeps_historical_and_recovered_results_separate():
    text = README.read_text(encoding="utf-8")

    assert "80.14%" in text
    assert "REPORTED" in text
    assert "80.17%" in text
    assert "recovered" in text.lower()
    assert "factor-of-1,000 discrepancy" in text
