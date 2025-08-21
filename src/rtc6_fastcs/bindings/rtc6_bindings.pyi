"""
bindings for the scanlab rtc6 ethernet laser controller
"""

from __future__ import annotations
import typing

__all__: list[str] = [
    "CardInfo",
    "LaserMode",
    "ListStatus",
    "RtcConnectionError",
    "RtcError",
    "RtcListError",
    "add_arc_to",
    "add_jump_to",
    "add_laser_on",
    "add_line_to",
    "check_connection",
    "clear_errors",
    "close",
    "config_list_memory",
    "connect",
    "execute_list",
    "get_card_info",
    "get_config_list",
    "get_error",
    "get_error_string",
    "get_input_pointer",
    "get_io_status",
    "get_last_error",
    "get_list_space",
    "get_list_statuses",
    "get_rtc_mode",
    "get_temperature",
    "init_list_loading",
    "load_list",
    "set_end_of_list",
    "list_nop",
    "set_jump_speed_ctrl",
    "set_laser_control",
    "set_laser_delays",
    "set_laser_mode",
    "set_mark_speed_ctrl",
    "set_scanner_delays",
    "set_sky_writing_mode",
]

class CardInfo:
    @property
    def firmware_version(self) -> int: ...
    @property
    def ip_address(self) -> str: ...
    @property
    def is_acquired(self) -> bool: ...
    @property
    def serial_number(self) -> int: ...

class LaserMode:
    """
    Members:

      CO2

      YAG1

      YAG2

      YAG3

      LASER4

      YAG5

      LASER6
    """

    CO2: typing.ClassVar[LaserMode]  # value = <LaserMode.CO2: 0>
    LASER4: typing.ClassVar[LaserMode]  # value = <LaserMode.LASER4: 4>
    LASER6: typing.ClassVar[LaserMode]  # value = <LaserMode.LASER6: 6>
    YAG1: typing.ClassVar[LaserMode]  # value = <LaserMode.YAG1: 1>
    YAG2: typing.ClassVar[LaserMode]  # value = <LaserMode.YAG2: 2>
    YAG3: typing.ClassVar[LaserMode]  # value = <LaserMode.YAG3: 3>
    YAG5: typing.ClassVar[LaserMode]  # value = <LaserMode.YAG5: 5>
    __members__: typing.ClassVar[
        dict[str, LaserMode]
    ]  # value = {'CO2': <LaserMode.CO2: 0>, 'YAG1': <LaserMode.YAG1: 1>, 'YAG2': <LaserMode.YAG2: 2>, 'YAG3': <LaserMode.YAG3: 3>, 'LASER4': <LaserMode.LASER4: 4>, 'YAG5': <LaserMode.YAG5: 5>, 'LASER6': <LaserMode.LASER6: 6>}
    def __eq__(self, other: typing.Any) -> bool: ...
    def __getstate__(self) -> int: ...
    def __hash__(self) -> int: ...
    def __index__(self) -> int: ...
    def __init__(self, value: typing.SupportsInt) -> None: ...
    def __int__(self) -> int: ...
    def __ne__(self, other: typing.Any) -> bool: ...
    def __repr__(self) -> str: ...
    def __setstate__(self, state: typing.SupportsInt) -> None: ...
    def __str__(self) -> str: ...
    @property
    def name(self) -> str: ...
    @property
    def value(self) -> int: ...

class ListStatus:
    """
    Members:

      LOAD1

      LOAD2

      READY1

      READY2

      BUSY1

      BUSY2

      USED1

      USED2
    """

    BUSY1: typing.ClassVar[ListStatus]  # value = <ListStatus.BUSY1: 4>
    BUSY2: typing.ClassVar[ListStatus]  # value = <ListStatus.BUSY2: 5>
    LOAD1: typing.ClassVar[ListStatus]  # value = <ListStatus.LOAD1: 0>
    LOAD2: typing.ClassVar[ListStatus]  # value = <ListStatus.LOAD2: 1>
    READY1: typing.ClassVar[ListStatus]  # value = <ListStatus.READY1: 2>
    READY2: typing.ClassVar[ListStatus]  # value = <ListStatus.READY2: 3>
    USED1: typing.ClassVar[ListStatus]  # value = <ListStatus.USED1: 6>
    USED2: typing.ClassVar[ListStatus]  # value = <ListStatus.USED2: 7>
    __members__: typing.ClassVar[
        dict[str, ListStatus]
    ]  # value = {'LOAD1': <ListStatus.LOAD1: 0>, 'LOAD2': <ListStatus.LOAD2: 1>, 'READY1': <ListStatus.READY1: 2>, 'READY2': <ListStatus.READY2: 3>, 'BUSY1': <ListStatus.BUSY1: 4>, 'BUSY2': <ListStatus.BUSY2: 5>, 'USED1': <ListStatus.USED1: 6>, 'USED2': <ListStatus.USED2: 7>}
    def __eq__(self, other: typing.Any) -> bool: ...
    def __getstate__(self) -> int: ...
    def __hash__(self) -> int: ...
    def __index__(self) -> int: ...
    def __init__(self, value: typing.SupportsInt) -> None: ...
    def __int__(self) -> int: ...
    def __ne__(self, other: typing.Any) -> bool: ...
    def __repr__(self) -> str: ...
    def __setstate__(self, state: typing.SupportsInt) -> None: ...
    def __str__(self) -> str: ...
    @property
    def name(self) -> str: ...
    @property
    def value(self) -> int: ...

class RtcConnectionError(Exception):
    pass

class RtcError(Exception):
    pass

class RtcListError(Exception):
    pass

def add_arc_to(
    x: typing.SupportsInt, y: typing.SupportsInt, angle: typing.SupportsFloat
) -> None: ...
def add_jump_to(x: typing.SupportsInt, y: typing.SupportsInt) -> None: ...
def add_laser_on(time_10us: typing.SupportsInt) -> None:
    """
    turn the laser on for n bits of time, see page 450
    """

def add_line_to(x: typing.SupportsInt, y: typing.SupportsInt) -> None: ...
def check_connection() -> None:
    """
    check the active connection to the eth box: throws RtcConnectionError on failure, otherwise does nothing. If it fails, errors must be cleared afterwards.
    """

def clear_errors() -> None:
    """
    clear errors in the RTC6 library
    """

def close(arg0: typing.SupportsInt) -> None:
    """
    close the open connection, if any
    """

def config_list_memory(
    list_1_mem: typing.SupportsInt, list_2_mem: typing.SupportsInt
) -> None:
    """
    set the memory for each position list, see p330
    """

def connect(ip_string: str, program_file_path: str, correction_file_path: str) -> int:
    """
    connect to the eth-box at the given IP
    """

def execute_list(arg0: typing.SupportsInt) -> None:
    """
    execute the current list
    """

def get_card_info() -> CardInfo:
    """
    get info for the connected card; throws RtcConnectionError on failure
    """

def get_config_list() -> None:
    """
    ---
    """

def get_error() -> int:
    """
    get the current error code. 0 is no error. table of errors is on p387, get_error_string() can be called for a human-readable version.
    """

def get_error_string() -> str:
    """
    get human-readable error info
    """

def get_input_pointer() -> int:
    """
    get the pointer of list input
    """

def get_io_status() -> int:
    """
    ---
    """

def get_last_error() -> int:
    """
    get the last error for an ethernet command
    """

def get_list_space() -> int:
    """
    ---
    """

def get_list_statuses() -> list:
    """
    get the statuses of the command lists
    """

def get_rtc_mode() -> int:
    """
    ---
    """

def get_temperature() -> float:
    """
    ---
    """

def init_list_loading(arg0: typing.SupportsInt) -> None:
    """
    initialise the given list (1 or 2)
    """

def load_list(list_no: typing.SupportsInt, position: typing.SupportsInt) -> int:
    """
    set the pointer to load at position of list_no, see p330
    """

def set_end_of_list() -> None:
    """
    set the end of the list to be at the current pointer position
    """

def list_nop() -> None:
    """
    insert a null operation into the RTC6 list memory. 
    Same as long_delay. Switcheds off signals for laser active operation after a laser off delay. 
    10us used regardless of delay. 
    Following short list command, ensures subsequent list command only executes in the next 10us clock cycle.
    """

def set_jump_speed_ctrl(speed: typing.SupportsFloat) -> None:
    """
    set the speed for jumps
    """

def set_laser_control(settings: typing.SupportsInt) -> None:
    """
    set the control settings of the laser, see p641
    """

def set_laser_delays(
    laser_on_delay: typing.SupportsInt, laser_off_delay: typing.SupportsInt
) -> None:
    """
    set the delays for the laser, see p136
    """

def set_laser_mode(mode: str) -> None:
    """
    set the mode of the laser, see p645
    """

def set_mark_speed_ctrl(speed: typing.SupportsFloat) -> None:
    """
    set the speed for marks
    """

def set_scanner_delays(
    jump: typing.SupportsInt, mark: typing.SupportsInt, polygon: typing.SupportsInt
) -> None:
    """
    set the scanner delays, in 10us increments
    """

def set_sky_writing_mode(speed: typing.SupportsInt) -> None:
    """
    set the skywriting mode
    """
