from healthcheck import classify, load_config, version_matches
 
 
def test_success_codes_are_up():
    assert classify(200) == "UP"
 
 
def test_not_found_is_an_error():
    assert classify(404) == "ERROR"
 
 
def test_no_response_is_down():
    assert classify(None) == "DOWN"
 
 
def test_matching_version_passes():
    assert version_matches("1.1.0", "1.1.0")
 
 
def test_different_version_fails():
    assert not version_matches("1.0.0", "1.1.0")
 
 
def test_load_config_reads_owner(tmp_path):
    settings = tmp_path / "config.yaml"
    settings.write_text("owner: jl123\ntimeout_seconds: 2\ntargets: []\n")
    assert load_config(settings)["owner"] == "jl123"
