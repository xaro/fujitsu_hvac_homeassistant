"""Constants for fujitsu_hvac."""
# Base component constants
NAME = "Fujitsu HVAC"
DOMAIN = "fujitsu_hvac"
DOMAIN_DATA = f"{DOMAIN}_data"
VERSION = "0.0.8"
ATTRIBUTION = ""
ISSUE_URL = ""

# Icons
ICON = "mdi:format-quote-close"

# Configuration and options
CONF_ENABLED = "enabled"
CONF_URL = "url"

# Defaults
DEFAULT_NAME = DOMAIN


STARTUP_MESSAGE = f"""
-------------------------------------------------------------------
{NAME}
Version: {VERSION}
This is a custom integration for Fujitsu HVACs!
If you have any issues with this you need to open an issue here:
{ISSUE_URL}
-------------------------------------------------------------------
"""
