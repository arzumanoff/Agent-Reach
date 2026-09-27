from argparse import Namespace

import pytest

from agent_reach import cli


@pytest.mark.parametrize("key", ["exa-key", "google-key", "google-cx"])
def test_new_sensitive_keys_reject_positional_values(key, capsys):
    args = Namespace(key=key, value=["secret"], read_stdin=False)
    with pytest.raises(SystemExit) as exc:
        cli._read_configure_value(args)
    assert exc.value.code == 2
    captured = capsys.readouterr()
    assert "secret" not in captured.out
    assert "secret" not in captured.err
