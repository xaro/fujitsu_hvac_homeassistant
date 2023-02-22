"""Client for communicating with Fujitsu API"""
from urllib.parse import urljoin
import datetime
import aiohttp
from .hvac_info import HvacInfo, Mode, FanSpeed
import logging
from aiohttp_retry import RetryClient, ExponentialRetry, ClientResponse

HEADERS = {
    "X-Requested-With": "XMLHttpRequest",
    "Content-Type": "application/x-www-form-urlencoded",
}

SESSION_ERROR = "-13"

_LOGGER: logging.Logger = logging.getLogger(__package__)


class FujitsuHvac:
    """Client for the Fujitsu HVAC API"""

    def __init__(self, base_url: str, username: str, password: str) -> None:
        self.base_url = base_url
        self.username = username
        self.password = password

    async def login(self, session: aiohttp.ClientSession):
        """Login to the API"""

        # Ensure that we are not logged in before, if not will get
        # error 4
        await self.logout(session)

        # TODO: Handle failures like bad user/pass
        payload = {
            "username": self.username,
            "password": self.password,
            "logintime": (datetime.datetime.now()).isoformat(),
        }

        async def evaluate_response(response: ClientResponse) -> bool:
            try:
                body = await response.text()

                if body == "4":
                    _LOGGER.info("Already logged in, logging out and back in")
                    await self.logout(session)
                    return False
                return True
            except Exception:
                return False

        client = RetryClient(
            raise_for_status=False,
            retry_options=ExponentialRetry(
                factor=2.0,
                max_timeout=10.0,
                attempts=10,
                evaluate_response_callback=evaluate_response,
            ),
            client_session=session,
        )

        async with client.post(
            self.url("login.cgi"), data=payload, headers=HEADERS
        ) as response:
            response_body = await response.text()
            if response_body == "4":
                _LOGGER.info("Already logged in, not retrying anymore")
                await self.logout(session)
                return
            if response_body != "0":
                raise Exception("Error response " + response_body)

    async def logout(self, session: aiohttp.ClientSession):
        """Logs out of the API"""

        async with session.post(self.url("logout.cgi")):
            session.cookie_jar.clear()

    async def get_all_info(self):
        """Returns the info of all devices from the API"""
        _LOGGER.info("Fujitsu: Gathering all data")

        async def evaluate_response(response: ClientResponse) -> bool:
            try:
                body = await response.text()

                if body == SESSION_ERROR:
                    _LOGGER.error("Fujitsu Session error, retrying")
                    return False
                return True
            except Exception:
                return False

        async with self.__new_session() as session:
            client = RetryClient(
                raise_for_status=False,
                retry_options=ExponentialRetry(
                    factor=2.0,
                    max_timeout=10.0,
                    attempts=10,
                    evaluate_response_callback=evaluate_response,
                ),
                client_session=session,
            )
            await self.login(session)

            async with client.post(
                self.url("getmondata.cgi"),
                data={"FunctionNo": 2, "Argument1": -1},
                headers=HEADERS,
            ) as response:
                body = await response.text()

                if body == SESSION_ERROR:
                    print("Session Error -13 found")

                    raise Exception("Session error found")

                _LOGGER.info("Fujitsu data gathered successfully")

                infos = []
                for info in body.split("\n"):
                    if len(info.strip()) == 0:
                        break
                    infos.append(HvacInfo.from_info(info.split(",")))
                return infos

    async def set_settings(
        self,
        circuit: int,
        sub_id: int,
        power_status: bool,
        mode: Mode,
        fan_speed: FanSpeed,
        temp: float,
        change_power_status: bool = False,
        change_mode: bool = False,
        change_fan_speed: bool = False,
        change_temp: bool = False,
    ):
        """Sets the settings that are specified"""

        async with self.__new_session() as session:
            await self.login(session)

            headers = {
                "X-Requested-With": "XMLHttpRequest",
                "Content-Type": "application/json",
                "X-CSRF-Token": "undefined",
            }

            cmd = self.to_command_str(
                circuit,
                sub_id,
                power_status,
                mode,
                fan_speed,
                temp,
                change_power_status,
                change_mode,
                change_fan_speed,
                change_temp,
            )
            _LOGGER.info("CMD: " + cmd)

            async with session.post(
                self.url("command.cgi"),
                data=r'{"arg1":"0","arg2":"' + cmd + r'"}"',
                headers=headers,
            ) as response:
                await self.logout(session)

                response_body = await response.text()
                if response_body != "0":
                    print("Error: " + response_body)
                    raise Exception("Error found")

    def url(self, path: str) -> str:
        """Returns the concatenated absolute URL"""
        return urljoin(self.base_url, path)

    def to_command_str(
        self,
        circuit: int,
        sub_id: int,
        power_status: bool,
        mode: Mode,
        fan_speed: FanSpeed,
        temp: float,
        change_power_status: bool = False,
        change_mode: bool = False,
        change_fan_speed: bool = False,
        change_temp: bool = False,
    ):
        """Encodes settings to a command that can be sent to the API"""
        cmd = [
            circuit + 1,
            sub_id + 1,
            self.__bool_to_command_str(change_power_status),
            self.__bool_to_command_str(power_status),
            self.__bool_to_command_str(change_mode),
            mode.cmd_value,
            self.__bool_to_command_str(change_fan_speed),
            1,
            self.__bool_to_command_str(change_temp),
            int(temp * 2),
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

    def __bool_to_command_str(self, changed_attr) -> int:
        return 1 if changed_attr else 0

    @staticmethod
    def __new_session() -> aiohttp.ClientSession:
        return aiohttp.ClientSession(
            cookie_jar=aiohttp.CookieJar(unsafe=True),
        )
