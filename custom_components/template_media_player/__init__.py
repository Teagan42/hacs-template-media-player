"""The Template Media Player component."""

from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant import config as conf_util
from homeassistant.components.media_player.const import DOMAIN as MEDIA_PLAYER_DOMAIN
from homeassistant.const import SERVICE_RELOAD
from homeassistant.core import Event, HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import discovery
from homeassistant.helpers.reload import async_reload_integration_platforms
from homeassistant.helpers.service import async_register_admin_service
from homeassistant.helpers.typing import ConfigType
from homeassistant.loader import async_get_integration

from .const import (
    CONF_MEDIA_PLAYERS,
    DOMAIN,
    PLATFORM_CONFIG_SCHEMA,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [MEDIA_PLAYER_DOMAIN]

# Configuration schema (will be validated by media_player platform)
CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: vol.Schema({vol.Required(CONF_MEDIA_PLAYERS): PLATFORM_CONFIG_SCHEMA})},
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Template Media Player integration."""

    if DOMAIN in config:
        _LOGGER.debug("Processing template media player configuration")
        await _process_config(hass, config)

    async def _reload_config(call: Event | ServiceCall) -> None:
        """Reload the template media player configuration."""
        _LOGGER.debug("Reloading template media player configuration")
        try:
            unprocessed_conf = await conf_util.async_hass_config_yaml(hass)
        except HomeAssistantError as err:
            _LOGGER.error("Error reloading template media player config: %s", err)
            return

        # Process the configuration
        integration = await async_get_integration(hass, DOMAIN)
        conf = await conf_util.async_process_component_and_handle_errors(
            hass, unprocessed_conf, integration
        )

        if conf is None:
            return

        # Reload platform entities
        await async_reload_integration_platforms(hass, DOMAIN, PLATFORMS)

        # Process new configuration
        if DOMAIN in conf:
            await _process_config(hass, conf)

        hass.bus.async_fire(f"event_{DOMAIN}_reloaded", context=call.context)
        _LOGGER.debug("Reloaded template media player configuration")

    async_register_admin_service(hass, DOMAIN, SERVICE_RELOAD, _reload_config)

    return True


async def async_setup_entry(hass: HomeAssistant, entry) -> bool:
    """Set up Template Media Player from a config entry."""
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _process_config(hass: HomeAssistant, hass_config: ConfigType) -> None:
    """Process configuration."""
    # Load platform for media_player if configured
    if DOMAIN in hass_config and CONF_MEDIA_PLAYERS in hass_config[DOMAIN]:
        _LOGGER.debug("Loading template media player platform")
        hass.async_create_task(
            discovery.async_load_platform(
                hass,
                MEDIA_PLAYER_DOMAIN,
                DOMAIN,
                {CONF_MEDIA_PLAYERS: hass_config[DOMAIN][CONF_MEDIA_PLAYERS]},
                hass_config,
            ),
            eager_start=True,
        )
