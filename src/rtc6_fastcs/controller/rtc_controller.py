import asyncio

from fastcs.attributes import AttrR, AttrW
from fastcs.controller import Controller, SubController
from fastcs.datatypes import Bool, Float, Int, String

from rtc6_fastcs.controller.rtc_connection import RtcConnection


class ConnectedSubController(SubController):
    def __init__(self, conn: RtcConnection) -> None:
        super().__init__()
        self._conn = conn


class RtcInfoController(ConnectedSubController):
    firmware_version = AttrR(Int(), group="Information")
    serial_number = AttrR(Int(), group="Information")
    ip_address = AttrR(String(), group="Information")
    is_acquired = AttrR(Bool(znam="False", onam="True"), group="Information")

    async def proc_cardinfo(self) -> None:
        info = self._conn.get_card_info()
        await asyncio.gather(
            self.firmware_version.set(info.firmware_version),
            self.serial_number.set(info.serial_number),
            self.ip_address.set(info.ip_address),
            self.is_acquired.set(info.is_acquired),
        )


class RtcControlSettings(ConnectedSubController):
    # laser_mode = AttrR(String(), group="LaserControl") should be an enum - do with allowed_values=
    jump_speed = AttrW(Float(), group="LaserControl")  # set_jump_speed_ctrl
    mark_speed = AttrW(Float(), group="LaserControl")  # set_mark_speed_ctrl
    # set_scanner_delays(jump, mark, polygon) in 10us increments
    jump_delay = AttrW(Int(), group="LaserControl")
    mark_delay = AttrW(Int(), group="LaserControl")
    polygon_delay = AttrW(Int(), group="LaserControl")
    sky_writing_mode = AttrW(Int(), group="LaserControl")  # set_sky_writing_mode


class RtcListOperations(ConnectedSubController):
    class AddJump(ConnectedSubController):
        x = AttrW(Int(), group="LaserControl")
        y = AttrW(Int(), group="LaserControl")

    class AddArc(ConnectedSubController):
        x = AttrW(Int(), group="LaserControl")
        y = AttrW(Int(), group="LaserControl")
        angle = AttrW(Float(), group="LaserControl")

    class AddLine(ConnectedSubController):
        x = AttrW(Int(), group="LaserControl")
        y = AttrW(Int(), group="LaserControl")

    def __init__(self, conn: RtcConnection) -> None:
        super().__init__(conn)


class RtcController(Controller):
    def __init__(
        self,
        box_ip: str,
        program_file_dir: str,
        correction_file: str,
        retry_connect: bool = False,
    ) -> None:
        super().__init__()
        self._conn = RtcConnection(
            box_ip, program_file_dir, correction_file, retry_connect
        )
        self._info_controller = RtcInfoController(self._conn)
        self.register_sub_controller("INFO", self._info_controller)
        self.register_sub_controller("CONTROL", RtcControlSettings(self._conn))
        list_controller = RtcListOperations(self._conn)
        self.register_sub_controller("LIST", list_controller)
        list_controller.register_sub_controller(
            "ADDJUMP", list_controller.AddJump(self._conn)
        )
        list_controller.register_sub_controller(
            "ADDARC", list_controller.AddArc(self._conn)
        )
        list_controller.register_sub_controller(
            "ADDLINE", list_controller.AddLine(self._conn)
        )

    async def connect(self) -> None:
        await self._conn.connect()
        await self._info_controller.proc_cardinfo()

    async def close(self) -> None:
        await self._conn.close()
