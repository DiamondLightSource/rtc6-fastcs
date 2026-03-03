import textwrap
from pathlib import Path

import pytest

from rtc6_fastcs.execution_list_parser import parse_execution_list_file


@pytest.fixture
def sample_execution_list(tmp_path: Path) -> Path:
    """Create a sample LaserDESK execution list file."""
    content = textwrap.dedent("""\
        LaserDESK Version 1.6.23.0
         Selectd RTC board: RTC6eth, Serial Number 20258562
         Laser Type: PORTO_150922
         Job Name: test.sld
         Calibration Factor: 27168.00

         Command List:
        n_set_laser_power(1, 0, 4095);
        n_list_nop(1);
        n_set_mark_speed(1, 271.68);
        n_jump_abs(1, 2173, 2173);
        n_mark_abs(1, 408, 543);
        n_arc_abs(1, -1311, 0, -314.984081458052);
        n_set_trigger8(1, 1, 1, 2, 255, 255, 4, 9, 9, 0);
        n_set_end_of_list(1);
    """)
    filepath = tmp_path / "test_list.txt"
    filepath.write_text(content)
    return filepath


def test_parse_skips_header(sample_execution_list: Path):
    commands = parse_execution_list_file(sample_execution_list)
    assert not any("LaserDESK" in cmd for cmd in commands)
    assert not any("Calibration" in cmd for cmd in commands)


def test_parse_strips_n_prefix_and_card_number(sample_execution_list: Path):
    commands = parse_execution_list_file(sample_execution_list)
    assert commands[0] == "set_laser_power(0, 4095)"
    assert commands[1] == "list_nop()"
    assert commands[2] == "set_mark_speed(271.68)"


def test_parse_handles_signed_coordinates(sample_execution_list: Path):
    commands = parse_execution_list_file(sample_execution_list)
    assert commands[3] == "jump_abs(2173, 2173)"
    assert commands[4] == "mark_abs(408, 543)"
    assert commands[5] == "arc_abs(-1311, 0, -314.984081458052)"


def test_parse_handles_many_arguments(sample_execution_list: Path):
    commands = parse_execution_list_file(sample_execution_list)
    assert commands[6] == "set_trigger8(1, 1, 2, 255, 255, 4, 9, 9, 0)"


def test_parse_returns_correct_count(sample_execution_list: Path):
    commands = parse_execution_list_file(sample_execution_list)
    assert len(commands) == 8


def test_parse_real_file():
    """Test against an actual shape protocol file if it exists."""
    filepath = Path("shape_protocols/Newlist.txt")
    if not filepath.exists():
        pytest.skip("shape_protocols/Newlist.txt not found")
    commands = parse_execution_list_file(filepath)
    assert len(commands) > 0
    # First command should be set_laser_power with card number stripped
    assert commands[0] == "set_laser_power(0, 4095)"
    # Last command should be set_end_of_list
    assert commands[-1] == "set_end_of_list()"
