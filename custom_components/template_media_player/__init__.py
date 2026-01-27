"""The Template Media Player component."""
import logging

import voluptuous as vol

from homeassistant.const import CONF_FRIENDLY_NAME, CONF_UNIQUE_ID, CONF_PLATFORM
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_PLATFORM): DOMAIN,
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Template Media Player component."""
    return True


async def async_setup_entry(hass, config_entry):
    """Set up Template Media Player from a config entry."""
    return True
