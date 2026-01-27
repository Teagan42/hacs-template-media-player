"""Template Media Player Component for Home Assistant."""

from __future__ import annotations

from dataclasses import asdict
import logging
from typing import Any

import voluptuous as vol

from homeassistant.components.media_player import (
    DOMAIN as MEDIA_PLAYER_DOMAIN,
    PLATFORM_SCHEMA as MEDIA_PLAYER_PLATFORM_SCHEMA,
    BrowseMedia,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
    MediaType,
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
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import TemplateError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.script import Script
from homeassistant.helpers.template import Template
from homeassistant.helpers.trigger import async_attach_trigger
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import (
    CONF_ATTRIBUTES,
    CONF_AVAILABILITY,
    CONF_BASE_MEDIA_PLAYER_ENTITY_ID,
    CONF_BROWSE_MEDIA_ENTITY_ID,
    CONF_BROWSE_MEDIA_SCRIPT,
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
    CONF_SEARCH_MEDIA_SCRIPT,
    CONF_SERVICE_SCRIPTS,
    CONF_SHUFFLE_SET_SCRIPT,
    CONF_SOUND_MODE_SCRIPTS,
    CONF_SOURCE_SCRIPTS,
    CONF_STATE,
    CONF_TRIGGERS,
    CONF_TURN_OFF_SCRIPT,
    CONF_TURN_ON_SCRIPT,
    CONF_VARIABLES,
    CONF_VOLUME_DOWN_SCRIPT,
    CONF_VOLUME_MUTE_SCRIPT,
    CONF_VOLUME_SET_SCRIPT,
    CONF_VOLUME_UP_SCRIPT,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

MEDIA_PLAYER_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_NAME): cv.template,
        vol.Optional(CONF_UNIQUE_ID): cv.string,
        vol.Optional(CONF_ICON): cv.template,
        vol.Optional(CONF_PICTURE): cv.template,
        vol.Optional(CONF_VARIABLES): cv.SCRIPT_VARIABLES_SCHEMA,
        vol.Optional(CONF_ATTRIBUTES, default={}): cv.schema_with_slug_keys(
            cv.template
        ),
        vol.Optional(CONF_DEVICE_CLASS): cv.string,
        vol.Optional(CONF_STATE): cv.template,
        vol.Optional(CONF_AVAILABILITY): cv.template,
        vol.Optional(CONF_BASE_MEDIA_PLAYER_ENTITY_ID): cv.entity_id,
        vol.Optional(CONF_SEARCH_MEDIA_ENTITY_ID): cv.entity_id,
        vol.Optional(CONF_BROWSE_MEDIA_ENTITY_ID): cv.entity_id,
        vol.Optional(CONF_SERVICE_SCRIPTS, default={}): cv.schema_with_slug_keys(
            cv.SCRIPT_SCHEMA
        ),
        vol.Optional(CONF_SOUND_MODE_SCRIPTS, default={}): cv.schema_with_slug_keys(
            cv.SCRIPT_SCHEMA
        ),
        vol.Optional(CONF_SOURCE_SCRIPTS, default={}): cv.schema_with_slug_keys(
            cv.SCRIPT_SCHEMA
        ),
        vol.Optional(CONF_TRIGGERS, default=[]): vol.All(
            cv.ensure_list, [cv.TRIGGER_SCHEMA]
        ),
    }
)

PLATFORM_SCHEMA = MEDIA_PLAYER_PLATFORM_SCHEMA.extend(
    {vol.Required(CONF_MEDIA_PLAYERS): cv.schema_with_slug_keys(MEDIA_PLAYER_SCHEMA)}
)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the template media players."""
    entities = []
    for name, cfg in config[CONF_MEDIA_PLAYERS].items():
        entities.append(TemplateMediaPlayer(hass, cfg, name))
    async_add_entities(entities)


class TemplateMediaPlayer(TemplateEntity, MediaPlayerEntity):
    """A template-driven media player that behaves like native template entities."""

    _attr_should_poll = False

    def __init__(
        self, hass: HomeAssistant, config: dict[str, Any], object_id: str
    ) -> None:
        """Initialize the template media player."""
        # Initialize TemplateEntity with config and unique_id
        TemplateEntity.__init__(
            self, hass, config=config, unique_id=config.get(CONF_UNIQUE_ID, object_id)
        )

        self._object_id = object_id
        self._state_template: Template | None = config.get(CONF_STATE)
        self._availability_template: Template | None = config.get(CONF_AVAILABILITY)
        self._icon_template: Template | None = config.get(CONF_ICON)
        self._picture_template: Template | None = config.get(CONF_PICTURE)
        self._name_template: Template | None = config.get(CONF_NAME)

        self._attribute_templates: dict[str, Template] = config.get(
            CONF_ATTRIBUTES, {}
        )

        # Optional entity references for delegating functionality
        self._base_entity_id = config.get(CONF_BASE_MEDIA_PLAYER_ENTITY_ID)
        self._search_entity_id = config.get(CONF_SEARCH_MEDIA_ENTITY_ID)
        self._browse_entity_id = config.get(CONF_BROWSE_MEDIA_ENTITY_ID)

        # Service scripts with slug keys
        self._service_scripts = {
            svc: Script(hass, script, object_id, DOMAIN)
            for svc, script in config.get(CONF_SERVICE_SCRIPTS, {}).items()
        }
        self._source_scripts = {
            src: Script(hass, script, object_id, DOMAIN)
            for src, script in config.get(CONF_SOURCE_SCRIPTS, {}).items()
        }
        self._sound_mode_scripts = {
            sm: Script(hass, script, object_id, DOMAIN)
            for sm, script in config.get(CONF_SOUND_MODE_SCRIPTS, {}).items()
        }

        # Trigger configuration for trigger-based updates
        self._trigger_configs = config.get(CONF_TRIGGERS, [])

        # State storage
        self._state: MediaPlayerState | None = None
        self._available: bool = True
        self._icon: str | None = None
        self._picture: str | None = None
        self._name: str | None = None

        # Device class
        self._attr_device_class = config.get(CONF_DEVICE_CLASS)

    async def async_added_to_hass(self) -> None:
        """Register template tracking and optional triggers."""
        # Register state template
        if self._state_template:
            self.add_template_attribute(
                "_state",
                self._state_template,
                validator=lambda v: MediaPlayerState(v) if v else None,
                none_on_template_error=True,
            )

        # Register availability template
        if self._availability_template:
            self.add_template_attribute(
                "_available",
                self._availability_template,
                validator=bool,
            )

        # Register icon template
        if self._icon_template:
            self.add_template_attribute("_icon", self._icon_template)

        # Register picture template
        if self._picture_template:
            self.add_template_attribute("_picture", self._picture_template)

        # Register name template
        if self._name_template:
            self.add_template_attribute("_name", self._name_template)

        # Register custom attribute templates
        for attr, tmpl in self._attribute_templates.items():
            self.add_template_attribute(
                f"_attr_{attr}",
                tmpl,
                none_on_template_error=True,
            )

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
        if not self._base_entity_id:
            return None
        return self.hass.data.get(MEDIA_PLAYER_DOMAIN, {}).get_entity(
            self._base_entity_id
        )

    def _get_search_entity(self) -> MediaPlayerEntity | None:
        """Get the search media player entity if configured."""
        if not self._search_entity_id:
            return None
        return self.hass.data.get(MEDIA_PLAYER_DOMAIN, {}).get_entity(
            self._search_entity_id
        )

    def _get_browse_entity(self) -> MediaPlayerEntity | None:
        """Get the browse media player entity if configured."""
        if not self._browse_entity_id:
            return None
        return self.hass.data.get(MEDIA_PLAYER_DOMAIN, {}).get_entity(
            self._browse_entity_id
        )

    # =================================================
    # PROPERTIES
    # =================================================

    @property
    def name(self) -> str | None:
        """Return the name of the entity."""
        if self._name:
            return self._name
        return self._object_id

    @property
    def available(self) -> bool:
        """Return if the entity is available."""
        return self._available

    @property
    def icon(self) -> str | None:
        """Return the icon."""
        return self._icon

    @property
    def entity_picture(self) -> str | None:
        """Return the entity picture."""
        return self._picture

    @property
    def state(self) -> MediaPlayerState | None:
        """Return the state of the player."""
        if self._state:
            return self._state
        # Fall back to base entity if no template state
        if base := self._get_base_entity():
            return base.state
        return None

    @property
    def supported_features(self) -> MediaPlayerEntityFeature:
        """Flag media player features that are supported."""
        # Start with base entity features if available
        base = self._get_base_entity()
        features = (
            base.supported_features if base else MediaPlayerEntityFeature(0)
        )

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

        return features

    @property
    def source_list(self) -> list[str] | None:
        """Return the list of available input sources."""
        if self._source_scripts:
            return list(self._source_scripts.keys())
        if base := self._get_base_entity():
            return base.source_list
        return None

    @property
    def sound_mode_list(self) -> list[str] | None:
        """Return the list of available sound modes."""
        if self._sound_mode_scripts:
            return list(self._sound_mode_scripts.keys())
        if base := self._get_base_entity():
            return base.sound_mode_list
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the extra state attributes."""
        attrs = {}
        for attr in self._attribute_templates:
            value = getattr(self, f"_attr_{attr}", None)
            if value is not None:
                attrs[attr] = value
        return attrs

    # =================================================
    # COMMAND METHODS
    # =================================================

    def _render_script_variables(self) -> dict[str, Any]:
        """Render template variables for scripts."""
        # This would render CONF_VARIABLES if needed
        # For now, return empty dict
        return {}

    async def _run_script(
        self, script_key: str, variables: dict[str, Any] | None = None
    ) -> None:
        """Run a service script or delegate to base entity."""
        script = self._service_scripts.get(script_key)
        if script:
            script_vars = {**(variables or {}), **self._render_script_variables()}
            await script.async_run(script_vars, context=self._context)
            return

        # Fall back to base entity if no script configured
        base = self._get_base_entity()
        if base:
            method_name = f"async_{script_key}"
            method = getattr(base, method_name, None)
            if method and callable(method):
                if variables:
                    await method(**variables)
                else:
                    await method()

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
    ) -> BrowseMedia | None:
        """Browse media."""
        # Try browse entity first
        if browse := self._get_browse_entity():
            return await browse.async_browse_media(
                media_content_type, media_content_id
            )

        # Try script
        if CONF_BROWSE_MEDIA_SCRIPT in self._service_scripts:
            await self._run_script(
                CONF_BROWSE_MEDIA_SCRIPT,
                {
                    "media_content_type": media_content_type,
                    "media_content_id": media_content_id,
                },
            )
            return None

        return None
