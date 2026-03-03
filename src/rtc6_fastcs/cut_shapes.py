import re
from pathlib import Path

import bluesky.plan_stubs as bps
import bluesky.preprocessors as bpp

from rtc6_fastcs.device import Rtc6Eth
from rtc6_fastcs.plan_stubs import *
from bluesky.run_engine import RunEngine
import numpy as np
import asyncio


def parse_execution_list_file(filepath: str | Path) -> list[str]:
    """
    Parse a LaserDESK execution list file and return command strings
    ready for dispatch_list_command.

    Strips the n_ prefix and first argument (card number) from each command.
    Skips header lines and blank lines.
    """
    commands: list[str] = []
    in_command_section = False

    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if "Command List:" in line:
                in_command_section = True
                continue
            if not in_command_section:
                continue

            # Strip trailing semicolon
            line = line.rstrip(";")

            # Match pattern: n_command_name(card_no, arg1, arg2, ...)
            # or n_command_name(card_no)
            match = re.match(r"^n_(\w+)\((\d+)(?:,\s*(.*))?\)$", line)
            if match:
                func_name = match.group(1)
                remaining_args = match.group(3)  # may be None
                if remaining_args:
                    commands.append(f"{func_name}({remaining_args})")
                else:
                    commands.append(f"{func_name}()")

    return commands


def execution_list_plan(rtc: Rtc6Eth, commands: list[str]):
    """
    Bluesky plan that sends parsed commands to the RTC6 via
    the generic command dispatcher PV.
    """
    for cmd in commands:
        yield from bps.abs_set(rtc.list.command_string, cmd, wait=True)
        yield from bps.trigger(rtc.list.dispatch_command, wait=True)


@bpp.run_decorator()
def run_execution_list(rtc: Rtc6Eth, filepath: str | Path):
    """
    Run a LaserDESK execution list file as a Bluesky plan.

    Handles init_list, sends all commands (including set_end_of_list
    from the file), then executes.
    """
    commands = parse_execution_list_file(filepath)
    yield from bps.stage(rtc)
    yield from execution_list_plan(rtc, commands)
    yield from bps.trigger(rtc)


class CutShapes:
    def __init__(self):
        self.RE = RunEngine()
        self.RTC = Rtc6Eth()

    async def connect(self):
        await self.RTC.connect()

    def connect_to_rtc(self):
        asyncio.run(self.connect())
        print("Connected to RTC6")

    def cut_cylinder_200l_100w(self, passes: int):
        shape = [
            (-100, 100, False),
            (0, 50, True),
            (200, 50, True),
            (200, -50, True),
            (0, -50, True),
            (-100, -100, True),
        ] * passes
        self.RE(draw_polygon(self.RTC, shape))

    def cut_cylinder(self, width: int, length: int, passes: int):
        shape = [
            (-width, width, False),
            (0, (width / 2), True),
            (length, (width / 2), True),
            (length, (-width / 2), True),
            (0, (-width / 2), True),
            (-width, -width, True),
        ] * passes
        self.RE(draw_polygon(self.RTC, shape))

    def cut_omega(self, neck_width: int, sphere_radius: int, passes: int):
        """
        Neck is n1 to n2, tails are t1 to t2, sphere radius is r.
        n1 will be half of neck width in Y.
        arc centre (X, Y) is from a2+b2=c2, we know B and C. X = root(rsquared - (n1(Y)/2)squared)
        Will use cont of r for tail. Y = 0.75 x neck_width, X = -(a/2)
        Need to use theta = arcsin(n1(Y)/r) to get angle between horizontal and arc start.
        360 - 2(Theta) gives arc angle to reach equiv point.
        """
        n1 = (0, np.around((neck_width / 2), 0))
        n2 = (0, np.around(-(neck_width / 2), 0))

        arc_centre = (np.sqrt(sphere_radius**2 - (n1[1] / 2) ** 2), 0)
        t1 = (np.around(-neck_width, 0), (np.around(arc_centre[0], 0)))
        t2 = (np.around(-neck_width, 0), -(np.around(arc_centre[0], 0)))

        arc_theta = -(360 - (np.degrees(np.arcsin(n1[1] / sphere_radius)) * 2))

        shape = [
            (t1, False),
            (n1, True),
            (arc_centre, arc_theta),
            (n2, True),
            (t2, True),
        ] * passes
        shape = [
            (
                (x[0][0], x[0][1], x[1])
                if isinstance(x, tuple) and len(x) == 2
                else (x[0], x[1], x[1])
            )
            for x in shape
        ]
        self.RE(draw_polygon_with_arcs(self.RTC, shape))

    def cut_polygon_from_gui(self, shape):
        self.RE(draw_polygon(self.RTC, shape))

    def home_scanhead(self):
        self.RE(go_to_home(self.RTC))

    def run_vendor_execution_list(self, filepath: str | Path):
        """Run a vendor execution list file (any .txt from shape_protocols/)."""
        self.RE(run_execution_list(self.RTC, filepath))
