import asyncio
from collections.abc import Callable
from dataclasses import dataclass
import logging
from typing import Any

from fastcs.attributes import AttrR, AttrW, AttrRW, AttributeIO, AttributeIORef
from fastcs.controllers import Controller
from fastcs.datatypes import Bool, Float, Int, String
from fastcs.methods import command

from rtc6_fastcs.controller.rtc_connection import RtcConnection
from rtc6_fastcs.bindings import rtc6_bindings as rtc6

import numpy as np

LOGGER = logging.getLogger(__name__)


class ConnectedSubController(Controller):
    def __init__(self, conn: RtcConnection, **kwargs) -> None:
        super().__init__(**kwargs)
        self._conn = conn


class RtcInfoController(ConnectedSubController):
    firmware_version = AttrR(Int(), group="Information")
    serial_number = AttrR(Int(), group="Information")
    ip_address = AttrR(String(), group="Information")
    is_acquired = AttrR(Bool(), group="Information")

    async def proc_cardinfo(self) -> None:
        info = self._conn.get_card_info()
        await asyncio.gather(
            self.firmware_version.update(info.firmware_version),
            self.serial_number.update(info.serial_number),
            self.ip_address.update(info.ip_address),
            self.is_acquired.update(info.is_acquired),
        )


@dataclass
class ControlSettingsIORef(AttributeIORef):
    cmd: Callable


class ControlSettingsIO(AttributeIO[Any, ControlSettingsIORef]):
    async def send(self, attr: AttrW[Any, ControlSettingsIORef], value: Any) -> None:
        attr.io_ref.cmd(value)


@dataclass
class DelaysIORef(AttributeIORef):
    pass


class DelaysIO(AttributeIO[int, DelaysIORef]):
    def __init__(self, controller: "RtcControlSettings"):
        super().__init__()
        self._controller = controller

    async def send(self, attr: AttrW[int, DelaysIORef], value: int) -> None:
        await attr.update(value)  # type: ignore[union-attr]
        rtc6.set_scanner_delays(
            self._controller.jump_delay.get(),
            self._controller.mark_delay.get(),
            self._controller.polygon_delay.get(),
        )


class RtcControlSettings(ConnectedSubController):
    # Page 645 of the manual
    laser_mode = AttrW(
        String(),
        group="LaserControl",
        io_ref=ControlSettingsIORef(cmd=rtc6.set_laser_mode),
    )
    laser_control = AttrW(
        Int(),
        group="LaserControl",
        io_ref=ControlSettingsIORef(cmd=rtc6.set_laser_control),
    )
    mark_speed = AttrW(
        Float(),
        group="LaserControl",
        io_ref=ControlSettingsIORef(cmd=rtc6.set_mark_speed_ctrl),
    )
    jump_speed = AttrW(
        Float(),
        group="LaserControl",
        io_ref=ControlSettingsIORef(cmd=rtc6.set_jump_speed_ctrl),
    )
    # set_scanner_delays(jump, mark, polygon) in 10us increments
    # need to all be set at once - special handler
    jump_delay = AttrRW(
        Int(),
        group="LaserControl",
        io_ref=DelaysIORef(),
    )
    mark_delay = AttrRW(
        Int(),
        group="LaserControl",
        io_ref=DelaysIORef(),
    )
    polygon_delay = AttrRW(
        Int(),
        group="LaserControl",
        io_ref=DelaysIORef(),
    )
    sky_writing_mode = AttrW(
        Int(),
        group="LaserControl",
        io_ref=ControlSettingsIORef(cmd=rtc6.set_sky_writing_mode),
    )

    def __init__(self, conn: RtcConnection) -> None:
        super().__init__(conn, ios=[ControlSettingsIO(), DelaysIO(self)])


class XYCorrectedConnectedSubController(ConnectedSubController):
    def __init__(
        self, conn: RtcConnection, coordinate_correction_matrix: np.ndarray, **kwargs
    ) -> None:
        super().__init__(conn, **kwargs)
        self.coordinate_correction_matrix = coordinate_correction_matrix

    def correct_xy(self, x: int, y: int) -> tuple[int, int]:
        """Correct for transformations in the laser / oav optics"""
        print(f"Correcting {(x, y)} by {self.coordinate_correction_matrix}")
        corrected = np.matmul(self.coordinate_correction_matrix, [x, y])
        as_ints = (int(corrected[0]), int(corrected[1]))
        print(f"Result: {corrected} => {as_ints}")
        return as_ints


class RtcListOperations(XYCorrectedConnectedSubController):
    list_pointer_position = AttrR(Int(), group="ListInfo")

    class AddJump(XYCorrectedConnectedSubController):
        x = AttrRW(Int(), group="ListOps")
        y = AttrRW(Int(), group="ListOps")

        @command(group="ListOps")
        async def proc(self):
            print("adding jump")
            bindings = self._conn.get_bindings()
            x, y = self.correct_xy(self.x.get(), self.y.get())
            bindings.add_jump_to(x, y)
            print("---")

    class AddArc(XYCorrectedConnectedSubController):
        x = AttrRW(Int(), group="ListOps")
        y = AttrRW(Int(), group="ListOps")
        angle = AttrRW(Float(), group="ListOps")

        @command()
        async def proc(self):
            print("adding arc")
            bindings = self._conn.get_bindings()
            x, y = self.correct_xy(self.x.get(), self.y.get())
            bindings.add_arc_to(x, y, self.angle.get())
            print("---")

    class AddLine(XYCorrectedConnectedSubController):
        x = AttrRW(Int(), group="ListOps")
        y = AttrRW(Int(), group="ListOps")

        @command()
        async def proc(self):
            print("adding line")
            bindings = self._conn.get_bindings()
            bindings.add_line_to(*self.correct_xy(self.x.get(), self.y.get()))
            print("---")

    @command()
    async def list_nop(self):
        rtc6 = self._conn.get_bindings()
        rtc6.list_nop()

    @command()
    async def init_list(self):
        rtc6 = self._conn.get_bindings()
        rtc6.config_list_memory(10000000, 1)  # Just put everything on list one
        rtc6.init_list_loading(1)

    @command()
    async def end_list(self):
        rtc6 = self._conn.get_bindings()
        rtc6.set_end_of_list()

    @command()
    async def execute_list(self):
        rtc6 = self._conn.get_bindings()
        rtc6.execute_list(1)


class RtcController(Controller):
    def __init__(
        self,
        box_ip: str,
        program_file_dir: str,
        correction_file: str,
        coordinate_system_correction_file: str = "",
        retry_connect: bool = False,
    ) -> None:
        super().__init__()
        try:
            self.coordinate_system_transform = np.loadtxt(
                coordinate_system_correction_file
            )
        except Exception:
            LOGGER.warning(
                "Failed to open coordinate system transformation file, defaulting to identity matrix."
            )
            self.coordinate_system_transform = np.array([[1, 0], [0, 1]])
        self._conn = RtcConnection(
            box_ip, program_file_dir, correction_file, retry_connect
        )

        info_controller = RtcInfoController(self._conn)
        self.add_sub_controller("INFO", info_controller)
        self.add_sub_controller("CONTROL", RtcControlSettings(self._conn))
        list_controller = RtcListOperations(
            self._conn, self.coordinate_system_transform
        )
        self.add_sub_controller("LIST", list_controller)
        list_controller.add_sub_controller(
            "ADDJUMP",
            list_controller.AddJump(self._conn, self.coordinate_system_transform),
        )
        list_controller.add_sub_controller(
            "ADDARC",
            list_controller.AddArc(self._conn, self.coordinate_system_transform),
        )
        list_controller.add_sub_controller(
            "ADDLINE",
            list_controller.AddLine(self._conn, self.coordinate_system_transform),
        )

    async def connect(self) -> None:
        await self._conn.connect()
        info = self.sub_controllers["INFO"]
        assert isinstance(info, RtcInfoController)
        await info.proc_cardinfo()

    async def disconnect(self) -> None:
        await self._conn.close()
