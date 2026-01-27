from __future__ import annotations

from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock
import logging

import pytest

from homeassistant.components.media_player import (
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.components.media_player import DOMAIN as MEDIA_PLAYER_DOMAIN
from homeassistant.components.media_player.browse_media import BrowseMedia
from homeassistant.const import CONF_UNIQUE_ID
from homeassistant.core import State
from homeassistant.helpers.entity_platform import EntityPlatform
from homeassistant.helpers.script import ScriptRunResult
from homeassistant.helpers.template import Template
from homeassistant.util import slugify

from custom_components.template_media_player.const import (
    DOMAIN,
    CONF_BASE_MEDIA_PLAYER_ENTITY_ID,
    CONF_BROWSE_MEDIA_ENTITY_ID,
    CONF_BROWSE_MEDIA_SCRIPT,
    CONF_DEFAULT_ENTITY_ID,
    CONF_MEDIA_PLAY_SCRIPT,
    CONF_MEDIA_PLAYERS,
    CONF_PLAY_MEDIA_SCRIPT,
    CONF_TURN_ON_SCRIPT,
    CONF_VOLUME_SET_SCRIPT,
)
from custom_components.template_media_player.media_player import (
    TemplateMediaPlayer,
    async_setup_platform,
)


@pytest.mark.asyncio
async def test_async_setup_platform_adds_entities(hass) -> None:
    added = []

    def async_add_entities(entities) -> None:
        added.extend(entities)

    config = {
        CONF_MEDIA_PLAYERS: {
            "alpha": {},
            "beta": {},
        }
    }

    await async_setup_platform(hass, config, async_add_entities)

    assert len(added) == 2
    assert {entity._object_id for entity in added} == {"alpha", "beta"}


@pytest.mark.asyncio
async def test_async_setup_platform_supports_flat_config(hass) -> None:
    added = []

    def async_add_entities(entities) -> None:
        added.extend(entities)

    config = {
        CONF_UNIQUE_ID: "example_media_player_1",
    }

    await async_setup_platform(hass, config, async_add_entities)

    assert len(added) == 1
    assert added[0]._object_id == slugify("example_media_player_1")


@pytest.mark.asyncio
async def test_async_setup_platform_default_entity_id_sets_object_id(hass) -> None:
    added = []

    def async_add_entities(entities) -> None:
        added.extend(entities)

    config = {
        CONF_DEFAULT_ENTITY_ID: "media_player.kitchen",
    }

    await async_setup_platform(hass, config, async_add_entities)

    assert len(added) == 1
    assert added[0]._object_id == "kitchen"
    assert added[0].entity_id == "media_player.kitchen"


@pytest.mark.asyncio
async def test_supported_features_combines_base_and_scripts(hass) -> None:
    base = SimpleNamespace(supported_features=MediaPlayerEntityFeature.PAUSE)
    hass.data[MEDIA_PLAYER_DOMAIN] = SimpleNamespace(get_entity=lambda entity_id: base)

    entity = TemplateMediaPlayer(hass, {}, "player")
    entity._base_entity_id = "media_player.base"
    entity._service_scripts = {
        CONF_TURN_ON_SCRIPT: object(),
        CONF_MEDIA_PLAY_SCRIPT: object(),
        CONF_PLAY_MEDIA_SCRIPT: object(),
        CONF_VOLUME_SET_SCRIPT: object(),
        CONF_BROWSE_MEDIA_SCRIPT: object(),
    }
    entity._source_scripts = {"spotify": object()}
    entity._sound_mode_scripts = {"stereo": object()}

    features = entity.supported_features

    assert features & MediaPlayerEntityFeature.PAUSE
    assert features & MediaPlayerEntityFeature.TURN_ON
    assert features & MediaPlayerEntityFeature.PLAY
    assert features & MediaPlayerEntityFeature.VOLUME_SET
    assert features & MediaPlayerEntityFeature.PLAY_MEDIA
    assert features & MediaPlayerEntityFeature.SELECT_SOURCE
    assert features & MediaPlayerEntityFeature.SELECT_SOUND_MODE
    assert features & MediaPlayerEntityFeature.BROWSE_MEDIA


@pytest.mark.asyncio
async def test_state_falls_back_to_base_entity(hass) -> None:
    def get_state(entity_id) -> State:
        return State("media_player.base", MediaPlayerState.PAUSED)

    base = SimpleNamespace(state=MediaPlayerState.PAUSED, available=True)
    setattr(
        hass,
        "states",
        SimpleNamespace(get=get_state),
    )
    hass.data[MEDIA_PLAYER_DOMAIN] = SimpleNamespace(
        get_entity=lambda entity_id: base,
        is_running=True,
    )

    entity = TemplateMediaPlayer(
        hass,
        {
            CONF_BASE_MEDIA_PLAYER_ENTITY_ID: "media_player.base",
        },
        "player",
    )
    entity.entity_id = "media_player.templated"
    entity.platform = EntityPlatform(
        hass=hass,
        logger=logging.getLogger(__name__),
        domain=DOMAIN,
        platform_name="Dunno",
        platform=None,
        scan_interval=timedelta(seconds=10),
        entity_namespace=None,
    )

    await entity.async_added_to_hass()

    assert entity.state == MediaPlayerState.PAUSED


@pytest.mark.asyncio
async def test_async_select_source_prefers_script(hass) -> None:
    script = SimpleNamespace(async_run=AsyncMock())
    base = SimpleNamespace(async_select_source=AsyncMock())
    hass.data[MEDIA_PLAYER_DOMAIN] = SimpleNamespace(get_entity=lambda entity_id: base)

    entity = TemplateMediaPlayer(hass, {}, "player")
    entity._base_entity_id = "media_player.base"
    entity._source_scripts = {"spotify": script}

    await entity.async_select_source("spotify")
    script.async_run.assert_awaited_once()
    base.async_select_source.assert_not_called()

    await entity.async_select_source("radio")
    base.async_select_source.assert_awaited_once_with("radio")


@pytest.mark.asyncio
async def test_run_script_falls_back_to_base(hass) -> None:
    base = SimpleNamespace(async_media_play=AsyncMock())
    hass.data[MEDIA_PLAYER_DOMAIN] = SimpleNamespace(get_entity=lambda entity_id: base)

    entity = TemplateMediaPlayer(hass, {}, "player")
    entity._base_entity_id = "media_player.base"
    entity._service_scripts = {}

    await entity._run_script(CONF_MEDIA_PLAY_SCRIPT)

    base.async_media_play.assert_awaited_once()


@pytest.mark.asyncio
async def test_extra_state_attributes_returns_values(hass) -> None:
    title = Template("{{ 'Song' }}", hass)
    artist = Template("{{ none }}", hass)

    config = {
        "attributes": {
            "title": title,
            "artist": artist,
        }
    }

    entity = TemplateMediaPlayer(hass, config, "player")
    entity._attr_title = None
    entity._attr_artist = None
    entity.entity_id = "media_player.player"

    await entity.async_added_to_hass()
    await hass.async_block_till_done()

    assert entity.extra_state_attributes == {"title": "Song"}


@pytest.mark.asyncio
async def test_run_script_uses_script(hass) -> None:
    script = SimpleNamespace(async_run=AsyncMock())

    entity = TemplateMediaPlayer(hass, {}, "player")
    entity._service_scripts = {CONF_MEDIA_PLAY_SCRIPT: script}

    await entity._run_script(CONF_MEDIA_PLAY_SCRIPT)

    script.async_run.assert_awaited_once()


@pytest.mark.asyncio
async def test_async_play_media_prefers_browse_entity(hass) -> None:
    browse = SimpleNamespace(async_play_media=AsyncMock())
    base = SimpleNamespace(async_play_media=AsyncMock())
    entities = {
        "media_player.browse": browse,
        "media_player.base": base,
    }
    hass.data[MEDIA_PLAYER_DOMAIN] = SimpleNamespace(
        get_entity=lambda entity_id: entities.get(entity_id)
    )

    entity = TemplateMediaPlayer(
        hass,
        {
            CONF_BROWSE_MEDIA_ENTITY_ID: "media_player.browse",
            CONF_BASE_MEDIA_PLAYER_ENTITY_ID: "media_player.base",
        },
        "player",
    )

    await entity.async_play_media("music", "track")

    browse.async_play_media.assert_awaited_once()
    base.async_play_media.assert_not_called()


@pytest.mark.asyncio
async def test_async_play_media_falls_back_to_base(hass) -> None:
    base = SimpleNamespace(async_play_media=AsyncMock())
    hass.data[MEDIA_PLAYER_DOMAIN] = SimpleNamespace(get_entity=lambda entity_id: base)

    entity = TemplateMediaPlayer(
        hass,
        {CONF_BASE_MEDIA_PLAYER_ENTITY_ID: "media_player.base"},
        "player",
    )

    await entity.async_play_media("music", "track")

    base.async_play_media.assert_awaited_once()


@pytest.mark.asyncio
async def test_async_play_media_uses_script(hass) -> None:
    script = SimpleNamespace(async_run=AsyncMock())
    entity = TemplateMediaPlayer(hass, {}, "player")
    entity._service_scripts = {CONF_PLAY_MEDIA_SCRIPT: script}

    await entity.async_play_media("music", "track")

    script.async_run.assert_awaited_once()


@pytest.mark.asyncio
async def test_async_browse_media_uses_script_result(hass) -> None:
    script_result = ScriptRunResult(
        conversation_response=None,
        service_response={
            "media_class": "music",
            "media_content_id": "root",
            "media_content_type": "library",
            "title": "Library",
            "can_play": False,
            "can_expand": True,
        },
        variables={},
    )
    script = SimpleNamespace(async_run=AsyncMock(return_value=script_result))

    entity = TemplateMediaPlayer(hass, {}, "player")
    entity._service_scripts = {CONF_BROWSE_MEDIA_SCRIPT: script}

    result = await entity.async_browse_media("library", "root")

    assert isinstance(result, BrowseMedia)
    assert result.title == "Library"


@pytest.mark.asyncio
async def test_async_browse_media_default_response(hass) -> None:
    entity = TemplateMediaPlayer(hass, {}, "player")

    result = await entity.async_browse_media()

    assert isinstance(result, BrowseMedia)
    assert result.can_play is False


@pytest.mark.asyncio
async def test_templates_render_name_icon_picture_and_availability(hass) -> None:
    name = Template("{{ 'Base Name' }}", hass)
    icon = Template("{{ 'mdi:base' }}", hass)
    availability = Template("{{ false }}", hass)

    config = {
        "name": name,
        "icon": icon,
        "availability": availability,
    }

    entity = TemplateMediaPlayer(hass, config, "player")
    entity.entity_id = "media_player.player"

    await entity.async_added_to_hass()
    await hass.async_block_till_done()

    assert entity.name == "Base Name"
    assert entity.icon == "mdi:base"
    assert entity.available is False
