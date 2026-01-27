from __future__ import annotations

import voluptuous as vol

from custom_components.template_media_player import config_flow as flow
from custom_components.template_media_player.const import CONF_NAME


def _schema_keys(schema: vol.Schema) -> set[str]:
    keys = set()
    for key in schema.schema:
        if isinstance(key, vol.Marker):
            keys.add(key.schema)
        else:
            keys.add(key)
    return keys


def test_generate_schema_config_includes_name() -> None:
    schema = flow.generate_schema("config")
    assert CONF_NAME in _schema_keys(schema)


def test_generate_schema_options_excludes_name() -> None:
    schema = flow.generate_schema("options")
    assert CONF_NAME not in _schema_keys(schema)


def test_config_flow_title_defaults() -> None:
    handler = object.__new__(flow.TemplateMediaPlayerConfigFlow)
    assert handler.async_config_entry_title({}) == "Template Media Player"
    assert handler.async_config_entry_title({CONF_NAME: "Den"}) == "Den"


def test_flow_maps_exist() -> None:
    assert "user" in flow.CONFIG_FLOW
    assert "init" in flow.OPTIONS_FLOW
    assert flow.TemplateMediaPlayerConfigFlow.options_flow_reloads is True
    assert flow.TemplateMediaPlayerConfigFlow.VERSION == 1
