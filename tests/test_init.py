from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

import custom_components.template_media_player as integration
from custom_components.template_media_player.const import CONF_MEDIA_PLAYERS, DOMAIN
from homeassistant.const import SERVICE_RELOAD
from pytest_homeassistant_custom_component.common import MockConfigEntry


@pytest.mark.asyncio
async def test_async_setup_processes_config(hass, monkeypatch) -> None:
    async_load = AsyncMock()
    monkeypatch.setattr(integration.discovery, "async_load_platform", async_load)

    config = {DOMAIN: {CONF_MEDIA_PLAYERS: {"alpha": {}}}}

    assert await integration.async_setup(hass, config)
    await hass.async_block_till_done()

    async_load.assert_called_once()


@pytest.mark.asyncio
async def test_reload_service_calls_process(hass, monkeypatch) -> None:
    config = {DOMAIN: {CONF_MEDIA_PLAYERS: {"alpha": {}}}}

    monkeypatch.setattr(
        integration.conf_util,
        "async_hass_config_yaml",
        AsyncMock(return_value=config),
    )
    monkeypatch.setattr(
        integration.conf_util,
        "async_process_component_and_handle_errors",
        AsyncMock(return_value=config),
    )
    monkeypatch.setattr(integration, "async_get_integration", AsyncMock(return_value=object()))
    monkeypatch.setattr(
        integration,
        "async_reload_integration_platforms",
        AsyncMock(return_value=True),
    )
    process = AsyncMock()
    monkeypatch.setattr(integration, "_process_config", process)

    assert await integration.async_setup(hass, config)
    await hass.services.async_call(DOMAIN, SERVICE_RELOAD, {}, blocking=True)

    process.assert_awaited_with(hass, config)


@pytest.mark.asyncio
async def test_setup_and_unload_entry(hass, monkeypatch) -> None:
    entry = MockConfigEntry(domain=DOMAIN, data={"name": "Entry"})
    entry.add_to_hass(hass)

    forward = AsyncMock(return_value=True)
    unload = AsyncMock(return_value=True)

    monkeypatch.setattr(hass.config_entries, "async_forward_entry_setups", forward)
    monkeypatch.setattr(hass.config_entries, "async_unload_platforms", unload)

    assert await integration.async_setup_entry(hass, entry)
    forward.assert_awaited_once_with(entry, integration.PLATFORMS)

    assert await integration.async_unload_entry(hass, entry)
    unload.assert_awaited_once_with(entry, integration.PLATFORMS)
