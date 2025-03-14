from typing import Generator
import bluesky.plan_stubs as bps
import bluesky.preprocessors as bpp
from rtc6_fastcs.device import Rtc6Eth
#from blueapi.core import MsgGenerator
from dodal.common.beamlines.beamline_utils import device_factory
from bluesky.run_engine import call_in_bluesky_event_loop


def convert_um_to_bits(um_in: int) -> int:
    """RTC operates in bits. Convert um to bits for drawing"""
    bits_per_um = 33  # estimated
    return int(um_in * bits_per_um)


def line(rtc6: Rtc6Eth, x: int, y: int):
    """add an instruction to draw a line to x, y"""
    x = convert_um_to_bits(x)
    y = convert_um_to_bits(y)
    yield from bps.abs_set(rtc6.list.add_line.x, x, wait=True)
    yield from bps.abs_set(rtc6.list.add_line.y, y, wait=True)
    yield from bps.trigger(rtc6.list.add_line.proc, wait=True)


def jump(rtc6: Rtc6Eth, x: int, y: int):
    """add an instruction to jump to x, y"""
    x = convert_um_to_bits(x)
    y = convert_um_to_bits(y)
    yield from bps.abs_set(rtc6.list.add_jump.x, x, wait=True)
    yield from bps.abs_set(rtc6.list.add_jump.y, y, wait=True)
    yield from bps.trigger(rtc6.list.add_jump.proc, wait=True)


def arc(rtc6: Rtc6Eth, x: int, y: int, angle_deg: float):
    """add an instruction to jump to x, y"""
    x = convert_um_to_bits(x)
    y = convert_um_to_bits(y)
    yield from bps.abs_set(rtc6.list.add_arc.x, x, wait=True)
    yield from bps.abs_set(rtc6.list.add_arc.y, y, wait=True)
    yield from bps.abs_set(rtc6.list.add_arc.angle_deg, angle_deg, wait=True)
    yield from bps.trigger(rtc6.list.add_arc.proc, wait=True)


def rectangle(rtc6: Rtc6Eth, x: int, y: int, origin: tuple[int, int] = (0, 0)):
    """add instructions to draw a rectangle with dimensions x, y and lower left corner at origin"""
    yield from jump(rtc6, *origin)
    yield from line(rtc6, x, origin[1])
    yield from line(rtc6, x, y)
    yield from line(rtc6, origin[0], y)
    yield from line(rtc6, *origin)


JumpOrLineInput = tuple[int, int, bool]  # x, y, laser_on
ArcInput = tuple[int, int, float]


@bpp.run_decorator()
def draw_square(rtc6: Rtc6Eth, size: int):
    yield from bps.stage(rtc6)
    yield from rectangle(rtc6, size, size)
    yield from bps.trigger(rtc6)
    go_to_home(rtc6)


@bpp.run_decorator()
def draw_polygon(rtc6: Rtc6Eth, points: list[JumpOrLineInput]):
    yield from bps.stage(rtc6)
    yield from jump(rtc6, *points[0][:-1])
    for point in points[1:]:
        if point[2]:
            yield from line(rtc6, *point[:-1])
        else:
            yield from jump(rtc6, *point[:-1])
    yield from bps.trigger(rtc6)
    go_to_home(rtc6)


@bpp.run_decorator()
def draw_polygon_with_arcs(rtc6: Rtc6Eth, points: list[JumpOrLineInput | ArcInput]):
    yield from bps.stage(rtc6)
    yield from jump(rtc6, *points[0][:-1])
    for point in points[1:]:
        if isinstance(point[2], bool):
            if point[2]:
                yield from line(rtc6, *point[:-1])
            else:
                yield from jump(rtc6, *point[:-1])
        else:
            yield from arc(rtc6, *point)
    yield from bps.trigger(rtc6)
    go_to_home(rtc6)


@bpp.run_decorator()
def go_to_home(rtc6: Rtc6Eth):
    yield from bps.stage(rtc6)
    yield from jump(rtc6, 0, 0)
    yield from bps.trigger(rtc6)


@bpp.run_decorator()
def go_to_x_y(rtc6: Rtc6Eth, x: int, y: int):
    yield from bps.stage(rtc6)
    yield from jump(rtc6, x, y)
    yield from bps.trigger(rtc6)


# For BlueAPI


# @device_factory()
# def create_rtc_device() -> Rtc6Eth:
#     r = Rtc6Eth()
#     call_in_bluesky_event_loop(r.connect())
#     return r


# def polygon_with_arcs(points: list[JumpOrLineInput | ArcInput]) -> MsgGenerator:
#     rtc6 = create_rtc_device()
#     yield from draw_polygon_with_arcs(rtc6, points)
