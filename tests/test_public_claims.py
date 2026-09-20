from pathlib import Path


TEMPLATE = Path(__file__).resolve().parents[1] / "templates" / "index.html"


def test_demo_distinguishes_live_metrics_from_reported_references():
    html = TEMPLATE.read_text(encoding="utf-8")

    assert "AB-GEN Research Demo" in html
    assert "80.14% reported" in html
    assert "V24 reproduction pending" in html
    assert "Historical Energy Estimate vs ResNet" in html
    assert "not live power measurement" in html
    assert "Evidence Status" in html
    assert "Current demo metric" not in html  # avoid accidental stale wording variant


def test_demo_does_not_present_historical_energy_as_live_saving_claim():
    html = TEMPLATE.read_text(encoding="utf-8")

    assert "Energy Saved vs ResNet" not in html
    assert '<span id="stat-saving">92</span>' not in html
    assert "AB-GEN 80% Accuracy" not in html
    assert "AB-GEN vs Industry Models" not in html
