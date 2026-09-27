from unittest.mock import patch

from agent_reach.backends.opencli import opencli_status
from agent_reach.probe import ProbeResult


def test_opencli_multi_profile_connected_counts_as_ready():
    daemon = {
        "ok": True,
        "extensionConnected": False,
        "profileRequired": True,
        "profiles": [
            {"contextId": "a", "extensionConnected": True},
            {"contextId": "b", "extensionConnected": True},
        ],
    }
    with patch(
        "agent_reach.backends.opencli.probe_command",
        return_value=ProbeResult("ok", output="1.8.7"),
    ), patch(
        "agent_reach.backends.opencli._fetch_daemon_status",
        return_value=daemon,
    ), patch(
        "agent_reach.backends.opencli._extension_installed_on_disk",
        return_value=False,
    ), patch(
        "agent_reach.backends.opencli._unpacked_extension_files_present",
        return_value=False,
    ):
        status = opencli_status()
    assert status.extension_connected is True
    assert status.ready is True
