"""Client for communicating with Fujitsu API"""
from urllib.parse import urljoin
import datetime
import aiohttp
from .hvac_info import HvacInfo, Mode, FanSpeed
import logging

HEADERS = {
    "X-Requested-With": "XMLHttpRequest",
    "Content-Type": "application/x-www-form-urlencoded",
}

SESSION_ERROR = "-13"

_LOGGER: logging.Logger = logging.getLogger(__package__)


class FujitsuHvac:
    """Client for the Fujitsu HVAC API"""

    def __init__(self, base_url: str, username: str, password: str) -> None:
        self.session = aiohttp.ClientSession(
            cookie_jar=aiohttp.CookieJar(unsafe=True),
        )

        self.base_url = base_url
        self.username = username
        self.password = password

    async def login(self):
        """Login to the API"""

        # Ensure that we are not logged in before, if not will get
        # error 4
        await self.logout()

        # TODO: Handle failures like bad user/pass
        payload = {
            "username": self.username,
            "password": self.password,
            "logintime": (datetime.datetime.now()).isoformat(),
        }

        async with self.session.post(
            self.url("login.cgi"), data=payload, headers=HEADERS
        ) as response:
            response_body = await response.text()
            if response_body == "4":
                _LOGGER.info("Already logged in")
                return
            if response_body != "0":
                raise Exception("Error response " + response_body)

    async def logout(self):
        """Logs out of the API"""

        async with self.session.post(self.url("logout.cgi")):
            self.session.cookie_jar.clear()

    async def get_all_info(self):
        """Returns the info of all devices from the API"""

        async with self.session.post(
            self.url("getmondata.cgi"),
            data={"FunctionNo": 2, "Argument1": -1},
            headers=HEADERS,
        ) as response:
            body = await response.text()

            if body == SESSION_ERROR:
                print("Session Error -13 found")
                # self.cookies = None
                raise Exception("Session error found")

            infos = []
            for info in body.split("\n"):
                if len(info.strip()) == 0:
                    break
                infos.append(HvacInfo.from_info(info.split(",")))
            return infos

    # @retry_with_backoff(retries=3)
    async def set_settings(
        self,
        circuit: int,
        sub_id: int,
        new_power_status: bool = None,
        new_mode: Mode = None,
        new_fan_speed: FanSpeed = None,
        new_temp: float = None,
    ):
        """Sets the settings that are specified"""

        headers = {
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/json",
        }

        async with self.session.post(
            self.url("command.cgi"),
            data={
                "arg1": 0,
                "arg2": self.to_command_str(
                    circuit, sub_id, new_power_status, new_mode, new_fan_speed, new_temp
                ),
            },
            headers=headers,
        ) as response:
            await self.logout()

            response_body = response.text()
            if response_body != "0":
                self.logout()
                print("Error: " + response_body)
                raise Exception("Error found")

    def url(self, path: str) -> str:
        """Returns the concatenated absolute URL"""
        return urljoin(self.base_url, path)

    def to_command_str(
        self,
        circuit: int,
        sub_id: int,
        new_power_status: bool = None,
        new_mode: Mode = None,
        new_fan_speed: FanSpeed = None,
        new_temp: float = None,
    ):
        """Encodes settings to a command that can be sent to the API"""
        cmd = [
            circuit + 1,
            sub_id + 1,
            self.__to_change_str(new_power_status),
            0 if new_power_status else self.__bool_to_command_str(new_power_status),
            self.__to_change_str(new_mode),
            0 if new_mode is None else new_mode.cmd_value,
            self.__to_change_str(new_fan_speed),
            0 if new_fan_speed is None else new_fan_speed.value,
            self.__to_change_str(new_temp),
            0 if new_temp is None else int(new_temp * 2),
            0,  # Changed air vert?
            0,  # Air vert
            0,
            0,  # Changed air hrz
            0,  # Air hrz
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,  # Cold or hot tmp change
            0,  # Cold temp
            0,  # Hot temp
        ]
        return ",".join([r"\"" + str(val) + r"\"" for val in cmd]) + r"\r\n"

    def __to_change_str(self, changed_attr) -> int:
        return self.__bool_to_command_str(changed_attr is None)

    def __bool_to_command_str(self, changed_attr) -> int:
        return 1 if changed_attr else 0
