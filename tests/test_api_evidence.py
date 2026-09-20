import app as app_module


def test_status_exposes_reported_result_and_metric_semantics(monkeypatch):
    monkeypatch.setattr(app_module, "sample_data", {"y": [0, 1, 2]})

    client = app_module.app.test_client()
    response = client.get("/api/status")

    assert response.status_code == 200
    data = response.get_json()

    assert data["model"] == "AB-GEN Research Demo"
    assert data["reported_version"] == "V24 Slow Burn"
    assert data["reported_accuracy"] == 80.14
    assert data["accuracy"] == 80.14  # compatibility alias
    assert data["accuracy_status"] == "reported_pending_reproduction"
    assert data["input_mode"] == "cached_pca_vectors"
    assert data["score_metric_status"] == "normalized_decision_scores_uncalibrated"
    assert data["energy_metric_status"] == "historical_reference_not_live_measurement"
    assert data["samples"] == 3
    assert data["ready"] is True


def test_evidence_constants_are_not_named_as_validated_measurements():
    assert app_module.EVIDENCE_STATUS != "validated"
    assert "not_live_measurement" in app_module.ENERGY_METRIC_STATUS
    assert "uncalibrated" in app_module.SCORE_METRIC_STATUS
