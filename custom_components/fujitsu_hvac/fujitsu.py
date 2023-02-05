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

        async with session.post(
            self.url("login.cgi"), data=payload, headers=HEADERS
        ) as response:
            response_body = await response.text()
            if response_body == "4":
                _LOGGER.info("Already logged in, logging out and back in")
                await self.logout(session)
                await self.login(session)
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

        async with self.__new_session() as session:
            await self.login(session)

            headers = {
                "X-Requested-With": "XMLHttpRequest",
                "Content-Type": "application/json",
            }

            async with session.post(
                self.url("command.cgi"),
                data={
                    "arg1": 0,
                    "arg2": self.to_command_str(
                        circuit,
                        sub_id,
                        new_power_status,
                        new_mode,
                        new_fan_speed,
                        new_temp,
                    ),
                },
                headers=headers,
            ) as response:
                await self.logout(session)

                response_body = response.text()
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

    @staticmethod
    def __new_session() -> aiohttp.ClientSession:
        return aiohttp.ClientSession(
            cookie_jar=aiohttp.CookieJar(unsafe=True),
        )
