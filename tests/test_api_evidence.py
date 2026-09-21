import app as app_module


def _mark_runtime_ready(monkeypatch, labels=(0, 1, 2)):
    monkeypatch.setattr(app_module, "sample_data", {"y": list(labels)})
    monkeypatch.setattr(app_module, "engine", object())


def test_status_exposes_separate_reported_and_recovered_evidence(monkeypatch):
    _mark_runtime_ready(monkeypatch)

    client = app_module.app.test_client()
    response = client.get("/api/status")

    assert response.status_code == 200
    data = response.get_json()

    assert data["model"] == "AB-GEN Research Demo"
    assert data["dataset"] == "CIFAR-10"

    reported = data["evidence"]["historical_reported"]
    assert reported["version"] == "V24 Slow Burn"
    assert reported["accuracy_pct"] == 80.14
    assert reported["status"] == "reported_historical_not_reproduced"

    recovered = data["evidence"]["recovered"]
    assert recovered["elite_slow_burn_cache_accuracy_pct"] == 80.17
    assert recovered["m5_master_reconstructed_accuracy_pct"] == 79.55
    assert recovered["m4_cache_accuracy_pct"] == 78.05
    assert recovered["status"] == "recovered_or_reconstructed_not_clean_reproduction"

    assert data["input_mode"] == "cached_pca_vectors"
    assert data["score_metric_status"] == "normalized_decision_scores_uncalibrated"
    assert data["energy_metric_status"] == "unavailable_pending_controlled_measurement"
    assert data["inference_path_status"] == "recovered_historical_path_not_clean_baseline"
    assert data["batch_invariance_status"] == "known_failure_in_targeted_audit"
    assert data["samples"] == 3
    assert data["ready"] is True


def test_status_reports_not_ready_without_loaded_resources(monkeypatch):
    monkeypatch.setattr(app_module, "sample_data", None)
    monkeypatch.setattr(app_module, "engine", None)

    data = app_module.app.test_client().get("/api/status").get_json()
    assert data["samples"] == 0
    assert data["ready"] is False


def test_analyze_refuses_uninitialized_runtime(monkeypatch):
    monkeypatch.setattr(app_module, "sample_data", None)
    monkeypatch.setattr(app_module, "engine", None)

    response = app_module.app.test_client().post("/api/analyze")
    assert response.status_code == 503
    assert response.get_json()["ready"] is False


def test_status_does_not_expose_ambiguous_accuracy_or_energy_aliases(monkeypatch):
    _mark_runtime_ready(monkeypatch, labels=(0,))
    data = app_module.app.test_client().get("/api/status").get_json()

    assert "accuracy" not in data
    assert "reported_accuracy" not in data
    assert "energy_uj" not in data
    assert "saving_pct" not in data
    assert "confidence" not in data


def test_evidence_constants_are_not_named_as_validated_measurements():
    assert app_module.EVIDENCE_STATUS != "validated"
    assert "unavailable" in app_module.ENERGY_METRIC_STATUS
    assert "uncalibrated" in app_module.SCORE_METRIC_STATUS
    assert "known_failure" in app_module.BATCH_INVARIANCE_STATUS
