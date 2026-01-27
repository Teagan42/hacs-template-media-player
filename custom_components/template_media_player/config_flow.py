"""Config flow for Template Media Player."""

from __future__ import annotations

from collections.abc import Mapping
from functools import partial
from typing import Any, cast

import voluptuous as vol

from homeassistant.components.media_player.const import DOMAIN as MEDIA_PLAYER_DOMAIN
from homeassistant.const import (
    CONF_DEVICE_CLASS,
    CONF_ICON,
    CONF_NAME,
    CONF_UNIQUE_ID,
)
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.helpers.schema_config_entry_flow import (
    SchemaConfigFlowHandler,
    SchemaFlowFormStep,
)

from .const import (
    CONF_ATTRIBUTES,
    CONF_AVAILABILITY,
    CONF_BASE_MEDIA_PLAYER_ENTITY_ID,
    CONF_BROWSE_MEDIA_ENTITY_ID,
    CONF_DEFAULT_ENTITY_ID,
    CONF_PICTURE,
    CONF_SEARCH_MEDIA_ENTITY_ID,
    CONF_SERVICE_SCRIPTS,
    CONF_SOUND_MODE_SCRIPTS,
    CONF_SOURCE_SCRIPTS,
    CONF_STATE,
    CONF_TRIGGERS,
    CONF_VARIABLES,
    DOMAIN,
)


def generate_schema(flow_type: str) -> vol.Schema:
    """Generate schema for config/options flow."""
    schema: dict[vol.Marker, Any] = {}

    if flow_type == "config":
        schema |= {
            vol.Required(CONF_NAME): selector.TextSelector(),
            vol.Optional(CONF_UNIQUE_ID): selector.TextSelector(),
        }

    entity_selector = selector.EntitySelector(
        selector.EntitySelectorConfig(domain=MEDIA_PLAYER_DOMAIN)
    )

    schema |= {
        vol.Optional(CONF_ICON): selector.TemplateSelector(),
        vol.Optional(CONF_PICTURE): selector.TemplateSelector(),
        vol.Optional(CONF_DEFAULT_ENTITY_ID): entity_selector,
        vol.Optional(CONF_VARIABLES): selector.ObjectSelector(),
        vol.Optional(CONF_ATTRIBUTES): selector.ObjectSelector(),
        vol.Optional(CONF_DEVICE_CLASS): selector.TextSelector(),
        vol.Optional(CONF_STATE): selector.TemplateSelector(),
        vol.Optional(CONF_AVAILABILITY): selector.TemplateSelector(),
        vol.Optional(CONF_BASE_MEDIA_PLAYER_ENTITY_ID): entity_selector,
        vol.Optional(CONF_SEARCH_MEDIA_ENTITY_ID): entity_selector,
        vol.Optional(CONF_BROWSE_MEDIA_ENTITY_ID): entity_selector,
        vol.Optional(CONF_SERVICE_SCRIPTS): selector.ObjectSelector(),
        vol.Optional(CONF_SOUND_MODE_SCRIPTS): selector.ObjectSelector(),
        vol.Optional(CONF_SOURCE_SCRIPTS): selector.ObjectSelector(),
        vol.Optional(CONF_TRIGGERS): selector.ObjectSelector(),
    }

    return vol.Schema(schema)


options_schema = partial(generate_schema, flow_type="options")
config_schema = partial(generate_schema, flow_type="config")


CONFIG_FLOW = {
    "user": SchemaFlowFormStep(config_schema()),
}


OPTIONS_FLOW = {
    "init": SchemaFlowFormStep(options_schema()),
}


class TemplateMediaPlayerConfigFlow(SchemaConfigFlowHandler, domain=DOMAIN):
    """Handle a config flow for Template Media Player."""

    config_flow = CONFIG_FLOW
    options_flow = OPTIONS_FLOW
    options_flow_reloads = True

    VERSION = 1

    @callback
    def async_config_entry_title(self, options: Mapping[str, Any]) -> str:
        """Return config entry title."""
        return cast(str, options.get(CONF_NAME, "Template Media Player"))
