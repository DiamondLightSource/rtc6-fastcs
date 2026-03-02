import asyncio
import re
from dataclasses import dataclass
from pathlib import Path

import bluesky.plan_stubs as bps
import bluesky.preprocessors as bpp
import numpy as np
from bluesky.run_engine import RunEngine

from rtc6_fastcs.device import Rtc6Eth
from rtc6_fastcs.plan_stubs import (
    draw_polygon,
    draw_polygon_with_arcs,
    go_to_home,
    go_to_home_inner,
)


@dataclass
class ExecutionListConfig:
    """Configuration extracted from vendor execution list header"""

    calibration_factor: float = 27168.0
    angle: float = 90.0
    mark_speed: float = 271.68
    jump_speed: float = 815.04
    scanahead_autodelays: int = 1
    scanahead_laser_shifts: tuple[int, int] = (0, 0)
    scanahead_line_params: tuple[int, int, int] = (0, 100, 100)
    firstpulse_killer: int = 6400
    laser_pulses: tuple[int, int] = (3200, 640)
    wobbel_mode: tuple[int, int, float, int] = (0, 0, 0.0, 0)
    sky_writing_para: tuple[float, int, int, int] = (0.0, 0, 0, 0)


@dataclass
class PathCommand:
    """A single path command (jump, line, or arc)"""

    cmd_type: str  # "jump", "line", "arc"
    x: int
    y: int
    angle: float | None = None  # Only for arcs


def parse_execution_list(
    filepath: str | Path,
) -> tuple[ExecutionListConfig, list[PathCommand]]:
    """
    Parse a vendor execution list file and extract config and path commands.

    Args:
        filepath: Path to the RTCExecutionlist_*.txt file

    Returns:
        Tuple of (config, list of path commands)
    """
    config = ExecutionListConfig()
    commands: list[PathCommand] = []

    with open(filepath) as f:
        content = f.read()

    # Extract calibration factor
    cal_match = re.search(r"Calibration Factor:\s*([\d.]+)", content)
    if cal_match:
        config.calibration_factor = float(cal_match.group(1))

    # Parse each line for commands
    for line in content.split("\n"):
        line = line.strip()

        # Configuration commands
        if "n_set_angle_list" in line:
            match = re.search(r"n_set_angle_list\(\d+,\s*\d+,\s*([\d.-]+)", line)
            if match:
                config.angle = float(match.group(1))

        elif "n_set_mark_speed" in line:
            match = re.search(r"n_set_mark_speed\(\d+,\s*([\d.]+)", line)
            if match:
                config.mark_speed = float(match.group(1))

        elif "n_set_jump_speed" in line:
            match = re.search(r"n_set_jump_speed\(\d+,\s*([\d.]+)", line)
            if match:
                config.jump_speed = float(match.group(1))

        elif "n_activate_scanahead_autodelays_list" in line:
            match = re.search(
                r"n_activate_scanahead_autodelays_list\(\d+,\s*(\d+)", line
            )
            if match:
                config.scanahead_autodelays = int(match.group(1))

        elif "n_set_scanahead_laser_shifts_list" in line:
            match = re.search(
                r"n_set_scanahead_laser_shifts_list\(\d+,\s*(\d+),\s*(\d+)", line
            )
            if match:
                config.scanahead_laser_shifts = (
                    int(match.group(1)),
                    int(match.group(2)),
                )

        elif "n_set_scanahead_line_params_list" in line:
            match = re.search(
                r"n_set_scanahead_line_params_list\(\d+,\s*(\d+),\s*(\d+),\s*(\d+)",
                line,
            )
            if match:
                config.scanahead_line_params = (
                    int(match.group(1)),
                    int(match.group(2)),
                    int(match.group(3)),
                )

        elif "n_set_firstpulse_killer_list" in line:
            match = re.search(r"n_set_firstpulse_killer_list\(\d+,\s*(\d+)", line)
            if match:
                config.firstpulse_killer = int(match.group(1))

        elif "n_set_laser_pulses" in line:
            match = re.search(r"n_set_laser_pulses\(\d+,\s*(\d+),\s*(\d+)", line)
            if match:
                config.laser_pulses = (int(match.group(1)), int(match.group(2)))

        elif "n_set_wobbel_mode" in line:
            match = re.search(
                r"n_set_wobbel_mode\(\d+,\s*(\d+),\s*(\d+),\s*([\d.]+),\s*(\d+)", line
            )
            if match:
                config.wobbel_mode = (
                    int(match.group(1)),
                    int(match.group(2)),
                    float(match.group(3)),
                    int(match.group(4)),
                )

        elif "n_set_sky_writing_para_list" in line:
            match = re.search(
                r"n_set_sky_writing_para_list\(\d+,\s*([\d.]+),\s*(\d+),\s*(\d+),\s*(\d+)",
                line,
            )
            if match:
                config.sky_writing_para = (
                    float(match.group(1)),
                    int(match.group(2)),
                    int(match.group(3)),
                    int(match.group(4)),
                )

        # Path commands
        elif "n_jump_abs" in line:
            match = re.search(r"n_jump_abs\(\d+,\s*(-?\d+),\s*(-?\d+)", line)
            if match:
                commands.append(
                    PathCommand("jump", int(match.group(1)), int(match.group(2)))
                )

        elif "n_mark_abs" in line:
            match = re.search(r"n_mark_abs\(\d+,\s*(-?\d+),\s*(-?\d+)", line)
            if match:
                commands.append(
                    PathCommand("line", int(match.group(1)), int(match.group(2)))
                )

        elif "n_arc_abs" in line:
            match = re.search(
                r"n_arc_abs\(\d+,\s*(-?\d+),\s*(-?\d+),\s*(-?[\d.]+)", line
            )
            if match:
                commands.append(
                    PathCommand(
                        "arc",
                        int(match.group(1)),
                        int(match.group(2)),
                        float(match.group(3)),
                    )
                )

    return config, commands


def execution_list_to_plan(
    rtc: Rtc6Eth, config: ExecutionListConfig, commands: list[PathCommand]
):
    """
    Convert parsed execution list to a Bluesky plan.

    This is a generator function that yields Bluesky messages.
    """
    # Apply configuration settings
    yield from bps.abs_set(
        rtc.control_settings.angle_list,
        f"1,{config.angle},0",
        wait=True,
    )
    yield from bps.abs_set(
        rtc.control_settings.mark_speed, config.mark_speed, wait=True
    )
    yield from bps.abs_set(
        rtc.control_settings.jump_speed, config.jump_speed, wait=True
    )
    yield from bps.abs_set(
        rtc.control_settings.scanahead_autodelays,
        config.scanahead_autodelays,
        wait=True,
    )
    yield from bps.abs_set(
        rtc.control_settings.scanahead_laser_shifts,
        f"{config.scanahead_laser_shifts[0]},{config.scanahead_laser_shifts[1]}",
        wait=True,
    )
    yield from bps.abs_set(
        rtc.control_settings.scanahead_line_params,
        f"{config.scanahead_line_params[0]},{config.scanahead_line_params[1]},{config.scanahead_line_params[2]}",
        wait=True,
    )
    yield from bps.abs_set(
        rtc.control_settings.firstpulse_killer,
        config.firstpulse_killer,
        wait=True,
    )
    yield from bps.abs_set(
        rtc.control_settings.laser_pulses,
        f"{config.laser_pulses[0]},{config.laser_pulses[1]}",
        wait=True,
    )
    yield from bps.abs_set(
        rtc.control_settings.wobbel_mode,
        f"{config.wobbel_mode[0]},{config.wobbel_mode[1]},{config.wobbel_mode[2]},{config.wobbel_mode[3]}",
        wait=True,
    )
    yield from bps.abs_set(
        rtc.control_settings.sky_writing_para,
        f"{config.sky_writing_para[0]},{config.sky_writing_para[1]},{config.sky_writing_para[2]},{config.sky_writing_para[3]}",
        wait=True,
    )

    # Execute path commands (coordinates are already in bits from the file)
    for cmd in commands:
        if cmd.cmd_type == "jump":
            yield from bps.abs_set(rtc.list.add_jump.x, cmd.x, wait=True)
            yield from bps.abs_set(rtc.list.add_jump.y, cmd.y, wait=True)
            yield from bps.trigger(rtc.list.add_jump.proc, wait=True)
        elif cmd.cmd_type == "line":
            yield from bps.abs_set(rtc.list.add_line.x, cmd.x, wait=True)
            yield from bps.abs_set(rtc.list.add_line.y, cmd.y, wait=True)
            yield from bps.trigger(rtc.list.add_line.proc, wait=True)
        elif cmd.cmd_type == "arc":
            yield from bps.abs_set(rtc.list.add_arc.x, cmd.x, wait=True)
            yield from bps.abs_set(rtc.list.add_arc.y, cmd.y, wait=True)
            yield from bps.abs_set(rtc.list.add_arc.angle_deg, cmd.angle, wait=True)
            yield from bps.trigger(rtc.list.add_arc.proc, wait=True)


@bpp.run_decorator()
def run_execution_list(rtc: Rtc6Eth, filepath: str | Path):
    """
    Run a vendor execution list file as a Bluesky plan.

    Args:
        rtc: The RTC6 device
        filepath: Path to the RTCExecutionlist_*.txt file
    """
    config, commands = parse_execution_list(filepath)
    yield from bps.stage(rtc)
    yield from execution_list_to_plan(rtc, config, commands)
    yield from bps.trigger(rtc)
    yield from go_to_home_inner(rtc)


@bpp.run_decorator()
def run_execution_list_repeated(rtc: Rtc6Eth, filepath: str | Path, passes: int = 1):
    """
    Run a vendor execution list file multiple times as a single Bluesky plan.

    Args:
        rtc: The RTC6 device
        filepath: Path to the RTCExecutionlist_*.txt file
        passes: Number of times to repeat the cut
    """
    config, commands = parse_execution_list(filepath)
    yield from bps.stage(rtc)
    yield from execution_list_to_plan(rtc, config, commands * passes)
    yield from bps.trigger(rtc)
    yield from go_to_home_inner(rtc)


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
        arc centre (X, Y) is from a2+b2=c2, we know B and C.
        X = root(rsquared - (n1(Y)/2)squared)
        Will use cont of r for tail. Y = 0.75 x neck_width, X = -(a/2)
        Need to use theta = arcsin(n1(Y)/r) to get angle between
        horizontal and arc start.
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
        """
        Run a vendor execution list file (RTCExecutionlist_*.txt).

        Args:
            filepath: Path to the execution list file
        """
        self.RE(run_execution_list(self.RTC, filepath))

    def cut_100um_sphere(self, passes: int = 1):
        """Run the 100um sphere cut from vendor execution list"""
        self.RE(
            run_execution_list_repeated(
                self.RTC, "shape_protocols/RTCExecutionlist_100umSphere.txt", passes
            )
        )

    def cut_150um_sphere(self, passes: int = 1):
        """Run the 150um sphere cut from vendor execution list"""
        self.RE(
            run_execution_list_repeated(
                self.RTC, "shape_protocols/RTCExecutionlist_150umSphere.txt", passes
            )
        )

    def cut_orientation_triangle(self, passes: int = 1):
        """Run the orientation triangle cut from vendor execution list"""
        self.RE(
            run_execution_list_repeated(
                self.RTC,
                "shape_protocols/RTCExecutionlist_OrientationTriangle.txt",
                passes,
            )
        )
