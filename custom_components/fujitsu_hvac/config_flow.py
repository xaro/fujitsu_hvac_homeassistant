"""Adds config flow for Blueprint."""
from homeassistant import config_entries
from homeassistant.core import callback
import voluptuous as vol

from fujitsu import fujitsu

from .const import (
    CONF_URL,
    CONF_PASSWORD,
    CONF_USERNAME,
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
        self._errors = {}

        if user_input is not None:
            valid = await self._test_credentials(
                user_input[CONF_URL],
                user_input[CONF_USERNAME],
                user_input[CONF_PASSWORD],
            )
            if valid:
                return self.async_create_entry(
                    title="%s %s" % (user_input[CONF_URL], user_input[CONF_USERNAME]),
                    data=user_input,
                )
            else:
                self._errors["base"] = "auth"

            return await self._show_config_form(user_input)

        user_input = {}
        # Provide defaults for form
        user_input[CONF_URL] = ""
        user_input[CONF_USERNAME] = ""
        user_input[CONF_PASSWORD] = ""

        return await self._show_config_form(user_input)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return FujitsuHvacOptionsFlowHandler(config_entry)

    async def _show_config_form(self, user_input):  # pylint: disable=unused-argument
        """Show the configuration form to edit data."""
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_URL, default=user_input[CONF_URL]): str,
                    vol.Required(CONF_USERNAME, default=user_input[CONF_USERNAME]): str,
                    vol.Required(CONF_PASSWORD, default=user_input[CONF_PASSWORD]): str,
                }
            ),
            errors=self._errors,
        )

    async def _test_credentials(self, url, username, password):
        """Return true if credentials is valid."""
        try:
            client = fujitsu.FujitsuHvac(url, username, password)
            await client.login()
            return True
        except Exception:  # pylint: disable=broad-except
            pass
        return False


class FujitsuHvacOptionsFlowHandler(config_entries.OptionsFlow):
    """Fujitsu Hvac config flow options handler."""

    def __init__(self, config_entry):
        """Initialize HACS options flow."""
        self.config_entry = config_entry
        self.options = dict(config_entry.options)

    async def async_step_init(self, user_input=None):  # pylint: disable=unused-argument
        """Manage the options."""
        return await self.async_step_user()

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        if user_input is not None:
            self.options.update(user_input)
            return await self._update_options()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "climate", default=self.options.get("climate", True)
                    ): bool
                }
            ),
        )

    async def _update_options(self):
        """Update config entry options."""
        return self.async_create_entry(
            title="%s %s"
            % (self.config_entry[CONF_URL], self.config_entry[CONF_USERNAME]),
            data=self.options,
        )
