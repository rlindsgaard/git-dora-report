import pytest

from dora_report.main import main, parse_interval

def test_main(script_runner):
    script_runner.run("dora_report/main.py", check=True, shell=True)


@pytest.mark.parametrize(
    "interval_str, expected_output",
    [
        ("7d", 7.0),    # Valid days
        ("2w", 14.0),   # Valid weeks
        ("1m", 30.0),   # Valid months
    ]
)
def test_parse_interval_valid(interval_str, expected_output):
    assert parse_interval(interval_str) / 86400 == expected_output

@pytest.mark.parametrize(
    "interval_str, expected_exception_message",
    [
        ("10", "Invalid interval format. Use Nd, Nw, or Nm (e.g., 7d, 2w, 1m)"),  # Missing suffix
        ("5y", "Invalid interval format. Use Nd, Nw, or Nm (e.g., 7d, 2w, 1m)"),  # Unknown suffix
        ("", "Invalid interval format. Use Nd, Nw, or Nm (e.g., 7d, 2w, 1m)"),    # Empty string
    ]
)
def test_parse_interval_invalid(interval_str, expected_exception_message):
    with pytest.raises(ValueError) as exc_info:
        parse_interval(interval_str)
    assert str(exc_info.value) == expected_exception_message 