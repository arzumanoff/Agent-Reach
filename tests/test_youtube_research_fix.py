from agent_reach.channels.youtube import _has_js_runtime_config


def test_youtube_runtime_config_ignores_commented_flag(tmp_path):
    config = tmp_path / "config"
    config.write_text("# --js-runtimes node\n--no-mtime\n", encoding="utf-8")
    assert _has_js_runtime_config(config) is False


def test_youtube_runtime_config_accepts_real_flag(tmp_path):
    config = tmp_path / "config"
    config.write_text("--js-runtimes node # enabled\n", encoding="utf-8")
    assert _has_js_runtime_config(config) is True
