"""Template Media Player Component for Home Assistant."""

from __future__ import annotations

from inspect import iscoroutinefunction
import logging
from typing import Any, Mapping, Optional, cast

import voluptuous as vol

from homeassistant.components.media_player import (
    ENTITY_ID_FORMAT,
    PLATFORM_SCHEMA as MEDIA_PLAYER_PLATFORM_SCHEMA,
    MediaPlayerEntity,
)
from homeassistant.components.media_player.const import (
    DOMAIN as MEDIA_PLAYER_DOMAIN,
    MediaPlayerEntityFeature,
    MediaType,
)
from homeassistant.components.media_player.browse_media import (
    BrowseMedia,
    async_process_play_media_url,
)
from homeassistant.components.media_source import (
    async_resolve_media,
    is_media_source_id,
)
from homeassistant.components.template.template_entity import TemplateEntity
from homeassistant.const import (
    CONF_DEVICE_CLASS,
    CONF_ICON,
    CONF_NAME,
    CONF_UNIQUE_ID,
    CONF_VARIABLES,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.script import Script, ScriptRunResult
from homeassistant.helpers.template import Template
from homeassistant.util import slugify

try:
    from homeassistant.helpers.trigger import async_attach_trigger  # type: ignore
except ImportError:  # HA 2026.1+
    from homeassistant.helpers.trigger import async_initialize_triggers

    async def async_attach_trigger(  # type: ignore[misc]
        hass: HomeAssistant,
        trigger_config: ConfigType,
        action,
        name: str,
    ):
        """Back-compat wrapper for removed async_attach_trigger."""
        return async_initialize_triggers(
            hass,
            [trigger_config],
            action,
            DOMAIN,
            name,
            log_cb=lambda *args, **kwargs: None,
        )


from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import (
    CONF_ATTRIBUTES,
    CONF_AVAILABILITY,
    CONF_BASE_MEDIA_PLAYER_ENTITY_ID,
    CONF_BROWSE_MEDIA_ENTITY_ID,
    CONF_BROWSE_MEDIA_SCRIPT,
    CONF_DEFAULT_ENTITY_ID,
    CONF_MEDIA_NEXT_TRACK_SCRIPT,
    CONF_MEDIA_PAUSE_SCRIPT,
    CONF_MEDIA_PLAY_SCRIPT,
    CONF_MEDIA_PLAYERS,
    CONF_MEDIA_PREVIOUS_TRACK_SCRIPT,
    CONF_MEDIA_SEEK_SCRIPT,
    CONF_MEDIA_STOP_SCRIPT,
    CONF_PICTURE,
    CONF_PLAY_MEDIA_SCRIPT,
    CONF_REPEAT_SET_SCRIPT,
    CONF_SEARCH_MEDIA_ENTITY_ID,
    CONF_SERVICE_SCRIPTS,
    CONF_SHUFFLE_SET_SCRIPT,
    CONF_SOUND_MODE_SCRIPTS,
    CONF_SOURCE_SCRIPTS,
    CONF_STATE,
    CONF_TRIGGERS,
    CONF_TURN_OFF_SCRIPT,
    CONF_TURN_ON_SCRIPT,
    CONF_VOLUME_DOWN_SCRIPT,
    CONF_VOLUME_MUTE_SCRIPT,
    CONF_VOLUME_SET_SCRIPT,
    CONF_VOLUME_UP_SCRIPT,
    DOMAIN,
    PLATFORM_CONFIG_SCHEMA,
)

_LOGGER = logging.getLogger(__name__)


PLATFORM_SCHEMA = vol.All(
    MEDIA_PLAYER_PLATFORM_SCHEMA.extend(PLATFORM_CONFIG_SCHEMA.schema)
)


def _get_template(
    hass, base_entity_id: str | None, attribute: str | None = None
) -> Template:
    if base_entity_id is None:
        return Template("{{ None }}", hass)
    if attribute:
        return Template(
            f"{{{{ state_attr('{base_entity_id}', '{attribute}') }}}}", hass
        )
    return Template(f"{{{{ states('{base_entity_id}') }}}}", hass)


def _get_available_template(
    hass,
    base_entity_id: str | None,
) -> Template:
    if base_entity_id is None:
        return Template("{{ True }}", hass)
    return Template(f"{{{{ has_value('{base_entity_id}') }}}}", hass)


def _derive_object_id(config: dict[str, Any]) -> str:
    if default_entity_id := config.get(CONF_DEFAULT_ENTITY_ID):
        return default_entity_id.partition(".")[2]
    if object_id_source := config.get(CONF_UNIQUE_ID):
        return slugify(object_id_source)
    if name_template := config.get(CONF_NAME):
        return slugify(getattr(name_template, "template", str(name_template)))
    return "template_media_player"


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the template media players."""
    # Support both direct platform config and discovery
    if discovery_info is not None:
        # Called via discovery from __init__.py
        media_players_config = discovery_info.get(CONF_MEDIA_PLAYERS, {})
    else:
        # Called directly with platform config
        media_players_config = config.get(CONF_MEDIA_PLAYERS, {})

    if not media_players_config:
        single_config = dict(config)
        single_config.pop("platform", None)
        object_id = _derive_object_id(single_config)
        media_players_config = {object_id: single_config}
        _LOGGER.debug(
            "Setting up template media player from flat config: %s", object_id
        )
    else:
        _LOGGER.debug(
            "Setting up template media players: %s",
            ", ".join(media_players_config.keys()),
        )

    entities = [
        TemplateMediaPlayer(hass, cfg, name)
        for name, cfg in media_players_config.items()
    ]

    async_add_entities(entities)


async def async_setup_entry(
    hass: HomeAssistant,
    entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up template media player from a config entry."""
    config = dict(entry.options or entry.data)
    if not config:
        _LOGGER.error("Config entry is missing data/options")
        return

    try:
        config = PLATFORM_CONFIG_SCHEMA(config)
    except vol.Invalid as err:
        _LOGGER.error("Invalid config entry data: %s", err)
        return

    object_id = _derive_object_id(config)
    async_add_entities([TemplateMediaPlayer(hass, config, object_id)])


class TemplateMediaPlayer(TemplateEntity, MediaPlayerEntity):
    """A template-driven media player that behaves like native template entities."""

    _attr_should_poll = False
    _entity_id_format = ENTITY_ID_FORMAT

    def __init__(
        self, hass: HomeAssistant, config: dict[str, Any], object_id: str
    ) -> None:
        """Initialize the template media player."""
        config = dict(config)
        config.setdefault(CONF_ATTRIBUTES, {})
        config.setdefault(CONF_VARIABLES, {})

        # Optional entity references for delegating functionality
        self._base_entity_id: str | None = config.get(CONF_BASE_MEDIA_PLAYER_ENTITY_ID)
        self._search_entity_id: str | None = config.get(CONF_SEARCH_MEDIA_ENTITY_ID)
        self._browse_entity_id: str | None = config.get(CONF_BROWSE_MEDIA_ENTITY_ID)

        for var, val in {
            CONF_BASE_MEDIA_PLAYER_ENTITY_ID: self._base_entity_id,
            CONF_SEARCH_MEDIA_ENTITY_ID: self._search_entity_id,
            CONF_BROWSE_MEDIA_ENTITY_ID: self._browse_entity_id,
        }.items():
            if val is None:
                continue
            config[CONF_VARIABLES] = {
                var: Template(val, hass),
                **config[CONF_VARIABLES],
            }

        base_entity = None
        if self._base_entity_id:
            base_entity = hass.data.get(MEDIA_PLAYER_DOMAIN, {}).get_entity(
                self._base_entity_id
            )
        if base_entity:
            for attr in getattr(base_entity, "state_attributes", {}) or {}:
                if attr in config[CONF_ATTRIBUTES]:
                    continue
                config[CONF_ATTRIBUTES][attr] = _get_template(
                    hass, self._base_entity_id, attr
                )

        self._object_id = object_id
        defaults = {
            CONF_STATE: _get_template(hass, self._base_entity_id),
            CONF_AVAILABILITY: _get_available_template(hass, self._base_entity_id),
        }
        if self._base_entity_id:
            defaults |= {
                CONF_ICON: _get_template(hass, self._base_entity_id, "icon"),
                CONF_PICTURE: _get_template(
                    hass, self._base_entity_id, "entity_picture"
                ),
                CONF_NAME: _get_template(hass, self._base_entity_id, "name"),
            }
        config = {**defaults, **config}

        # Service scripts with slug keys
        self._service_scripts: dict[str, Script] = {
            svc: Script(hass, script, object_id, DOMAIN)
            for svc, script in config.get(CONF_SERVICE_SCRIPTS, {}).items()
        }
        self._source_scripts: dict[str, Script] = {
            src: Script(hass, script, object_id, DOMAIN)
            for src, script in config.get(CONF_SOURCE_SCRIPTS, {}).items()
        }
        self._sound_mode_scripts: dict[str, Script] = {
            sm: Script(hass, script, object_id, DOMAIN)
            for sm, script in config.get(CONF_SOUND_MODE_SCRIPTS, {}).items()
        }

        # Trigger configuration for trigger-based updates
        self._trigger_configs: list[dict[str, Any]] = config.get(CONF_TRIGGERS, [])
        # Device class
        self._attr_device_class = config.get(CONF_DEVICE_CLASS)
        TemplateEntity.__init__(
            self, hass, config=config, unique_id=config.get(CONF_UNIQUE_ID, object_id)
        )
        self.setup_state_template(CONF_STATE, "_attr_state")

    async def async_added_to_hass(self) -> None:
        """Register template tracking and optional triggers."""
        # Set up triggers for trigger-based updates (like native template entities)
        if self._trigger_configs:
            for trigger_conf in self._trigger_configs:
                await async_attach_trigger(
                    self.hass,
                    trigger_conf,
                    lambda *args: self.async_write_ha_state(),
                    self.entity_id,
                )

        await super().async_added_to_hass()

    # =================================================
    # HELPER METHODS TO GET REFERENCED ENTITIES
    # =================================================

    def _get_base_entity(self) -> MediaPlayerEntity | None:
        """Get the base media player entity if configured."""
        if not self._base_entity_id or self.hass is None:
            return None
        component = self.hass.data.get(MEDIA_PLAYER_DOMAIN)
        if component is None:
            return None
        return component.get_entity(self._base_entity_id)

    def _get_search_entity(self) -> MediaPlayerEntity | None:
        """Get the search media player entity if configured."""
        if not self._search_entity_id or self.hass is None:
            return None
        component = self.hass.data.get(MEDIA_PLAYER_DOMAIN)
        if component is None:
            return None
        return component.get_entity(self._search_entity_id)

    def _get_browse_entity(self) -> MediaPlayerEntity | None:
        """Get the browse media player entity if configured."""
        if not self._browse_entity_id or self.hass is None:
            return None
        component = self.hass.data.get(MEDIA_PLAYER_DOMAIN)
        if component is None:
            return None
        return component.get_entity(self._browse_entity_id)

    # =================================================
    # PROPERTIES
    # =================================================

    @property
    def supported_features(self) -> MediaPlayerEntityFeature:  # type: ignore
        """Flag media player features that are supported."""
        # Start with base entity features if available
        base = self._get_base_entity()
        features = base.supported_features if base else MediaPlayerEntityFeature(0)

        # Add features based on configured scripts
        if CONF_TURN_ON_SCRIPT in self._service_scripts:
            features |= MediaPlayerEntityFeature.TURN_ON
        if CONF_TURN_OFF_SCRIPT in self._service_scripts:
            features |= MediaPlayerEntityFeature.TURN_OFF
        if CONF_MEDIA_PLAY_SCRIPT in self._service_scripts:
            features |= MediaPlayerEntityFeature.PLAY
        if CONF_MEDIA_PAUSE_SCRIPT in self._service_scripts:
            features |= MediaPlayerEntityFeature.PAUSE
        if CONF_MEDIA_STOP_SCRIPT in self._service_scripts:
            features |= MediaPlayerEntityFeature.STOP
        if CONF_PLAY_MEDIA_SCRIPT in self._service_scripts:
            features |= MediaPlayerEntityFeature.PLAY_MEDIA
        if (
            CONF_VOLUME_UP_SCRIPT in self._service_scripts
            or CONF_VOLUME_DOWN_SCRIPT in self._service_scripts
        ):
            features |= MediaPlayerEntityFeature.VOLUME_STEP
        if CONF_VOLUME_SET_SCRIPT in self._service_scripts:
            features |= MediaPlayerEntityFeature.VOLUME_SET
        if CONF_VOLUME_MUTE_SCRIPT in self._service_scripts:
            features |= MediaPlayerEntityFeature.VOLUME_MUTE
        if CONF_MEDIA_PREVIOUS_TRACK_SCRIPT in self._service_scripts:
            features |= MediaPlayerEntityFeature.PREVIOUS_TRACK
        if CONF_MEDIA_NEXT_TRACK_SCRIPT in self._service_scripts:
            features |= MediaPlayerEntityFeature.NEXT_TRACK
        if CONF_MEDIA_SEEK_SCRIPT in self._service_scripts:
            features |= MediaPlayerEntityFeature.SEEK
        if self._source_scripts:
            features |= MediaPlayerEntityFeature.SELECT_SOURCE
        if self._sound_mode_scripts:
            features |= MediaPlayerEntityFeature.SELECT_SOUND_MODE
        if CONF_SHUFFLE_SET_SCRIPT in self._service_scripts:
            features |= MediaPlayerEntityFeature.SHUFFLE_SET
        if CONF_REPEAT_SET_SCRIPT in self._service_scripts:
            features |= MediaPlayerEntityFeature.REPEAT_SET
        if self._browse_entity_id or CONF_BROWSE_MEDIA_SCRIPT in self._service_scripts:
            features |= MediaPlayerEntityFeature.BROWSE_MEDIA

        for var in [
            self._base_entity_id,
            self._search_entity_id,
            self._browse_entity_id,
        ]:
            if var is None:
                continue
            self._run_variables

        return features

    @property
    def source_list(self) -> list[str] | None:  # type: ignore
        """Return the list of available input sources."""
        if self._source_scripts:
            return list(self._source_scripts.keys())
        if base := self._get_base_entity():
            return base.source_list
        return None

    @property
    def sound_mode_list(self) -> list[str] | None:  # type: ignore
        """Return the list of available sound modes."""
        if self._sound_mode_scripts:
            return list(self._sound_mode_scripts.keys())
        if base := self._get_base_entity():
            return base.sound_mode_list
        return None

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:  # type: ignore
        """Return the extra state attributes."""
        base_entity = self._get_base_entity()
        base_attrs = {}
        if base_entity:
            base_attrs = getattr(base_entity, "state_attributes", {}) or {}
        attrs = {**base_attrs}
        for key, value in (getattr(self, "_attr_extra_state_attributes", {}) or {}).items():
            if value is not None:
                attrs[key] = value
        return attrs

    # =================================================
    # COMMAND METHODS
    # =================================================

    async def _run_script(
        self, script_key: str, variables: dict[str, Any] | None = None
    ) -> ScriptRunResult | None:
        """Run a service script or delegate to base entity."""
        script = self._service_scripts.get(script_key)
        if script:
            script_vars = {**(variables or {}), **self._render_script_variables()}
            return await script.async_run(script_vars, context=self._context)

        # Fall back to base entity if no script configured
        base = self._get_base_entity()
        if base:
            method_name = f"async_{script_key}"
            method = getattr(base, method_name, None)
            if method and callable(method):
                if iscoroutinefunction(method):
                    return await method(**(variables or {}))
                else:
                    return cast(Optional[ScriptRunResult], method(**(variables or {})))

        _LOGGER.debug(
            "No script or base entity handler for %s on %s",
            script_key,
            self.entity_id,
        )

    async def async_turn_on(self) -> None:
        """Turn the media player on."""
        await self._run_script(CONF_TURN_ON_SCRIPT)

    async def async_turn_off(self) -> None:
        """Turn the media player off."""
        await self._run_script(CONF_TURN_OFF_SCRIPT)

    async def async_media_play(self) -> None:
        """Send play command."""
        await self._run_script(CONF_MEDIA_PLAY_SCRIPT)

    async def async_media_pause(self) -> None:
        """Send pause command."""
        await self._run_script(CONF_MEDIA_PAUSE_SCRIPT)

    async def async_media_stop(self) -> None:
        """Send stop command."""
        await self._run_script(CONF_MEDIA_STOP_SCRIPT)

    async def async_media_previous_track(self) -> None:
        """Send previous track command."""
        await self._run_script(CONF_MEDIA_PREVIOUS_TRACK_SCRIPT)

    async def async_media_next_track(self) -> None:
        """Send next track command."""
        await self._run_script(CONF_MEDIA_NEXT_TRACK_SCRIPT)

    async def async_media_seek(self, position: float) -> None:
        """Send seek command."""
        await self._run_script(CONF_MEDIA_SEEK_SCRIPT, {"position": position})

    async def async_volume_up(self) -> None:
        """Turn volume up."""
        await self._run_script(CONF_VOLUME_UP_SCRIPT)

    async def async_volume_down(self) -> None:
        """Turn volume down."""
        await self._run_script(CONF_VOLUME_DOWN_SCRIPT)

    async def async_set_volume_level(self, volume: float) -> None:
        """Set volume level."""
        await self._run_script(CONF_VOLUME_SET_SCRIPT, {"volume_level": volume})

    async def async_mute_volume(self, mute: bool) -> None:
        """Mute the volume."""
        await self._run_script(CONF_VOLUME_MUTE_SCRIPT, {"is_volume_muted": mute})

    async def async_set_shuffle(self, shuffle: bool) -> None:
        """Enable/disable shuffle mode."""
        await self._run_script(CONF_SHUFFLE_SET_SCRIPT, {"shuffle": shuffle})

    async def async_set_repeat(self, repeat: str) -> None:
        """Set repeat mode."""
        await self._run_script(CONF_REPEAT_SET_SCRIPT, {"repeat": repeat})

    async def async_select_source(self, source: str) -> None:
        """Select input source."""
        if source in self._source_scripts:
            script = self._source_scripts[source]
            await script.async_run(
                self._render_script_variables(), context=self._context
            )
        elif base := self._get_base_entity():
            await base.async_select_source(source)

    async def async_select_sound_mode(self, sound_mode: str) -> None:
        """Select sound mode."""
        if sound_mode in self._sound_mode_scripts:
            script = self._sound_mode_scripts[sound_mode]
            await script.async_run(
                self._render_script_variables(), context=self._context
            )
        elif base := self._get_base_entity():
            await base.async_select_sound_mode(sound_mode)

    async def async_play_media(
        self, media_type: str, media_id: str, **kwargs: Any
    ) -> None:
        """Play a piece of media."""
        # Handle media source URLs
        if is_media_source_id(media_id):
            item = await async_resolve_media(self.hass, media_id, self.entity_id)
            media_id = async_process_play_media_url(self.hass, item.url)
            media_type = MediaType.MUSIC

        # Try script first
        if CONF_PLAY_MEDIA_SCRIPT in self._service_scripts:
            await self._run_script(
                CONF_PLAY_MEDIA_SCRIPT,
                {"media_type": media_type, "media_id": media_id},
            )
            return

        # Fall back to browse entity
        if browse := self._get_browse_entity():
            await browse.async_play_media(media_type, media_id, **kwargs)
            return

        # Fall back to base entity
        if base := self._get_base_entity():
            await base.async_play_media(media_type, media_id, **kwargs)

    async def async_browse_media(
        self,
        media_content_type: str | None = None,
        media_content_id: str | None = None,
    ) -> BrowseMedia:
        """Browse media."""
        # Try browse entity first
        if browse := self._get_browse_entity():
            return await browse.async_browse_media(media_content_type, media_content_id)

        # Try script
        if CONF_BROWSE_MEDIA_SCRIPT in self._service_scripts:
            result = await self._run_script(
                CONF_BROWSE_MEDIA_SCRIPT,
                {
                    "media_content_type": media_content_type,
                    "media_content_id": media_content_id,
                },
            )
            if result:
                return BrowseMedia(**result.service_response)  # type: ignore

        return BrowseMedia(
            media_class="",
            media_content_id="",
            media_content_type="",
            title="",
            can_play=False,
            can_expand=False,
        )
