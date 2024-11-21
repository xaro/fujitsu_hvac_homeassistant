"""Adds config flow for Blueprint."""
from homeassistant import config_entries
from homeassistant.core import callback
import voluptuous as vol
import aiohttp

from .fujitsu import FujitsuHvac

from .const import (
    CONF_URL,
    DOMAIN,
)


class FujitsuHvacFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Fujitsu HVAC."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    def __init__(self):
        """Initialize."""
        self._errors = {}

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""

        user_input = {}
        # Provide defaults for form
        user_input[CONF_URL] = ""

        return await self._show_config_form(user_input)
    
    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None):
        return await self._show_config_form(user_input)

    async def _show_config_form(self, user_input):
        """Show the configuration form to edit data."""
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_URL,
                        default=user_input[CONF_URL],
                        msg="URL",
                        description="URL",
                    ): str,
                }
            ),
            errors=self._errors,
        )
