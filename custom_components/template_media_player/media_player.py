"""Support for Template Media Players."""
from __future__ import annotations

from functools import cached_property
import logging
from typing import Any

import voluptuous as vol

from homeassistant.components.media_player import (
    PLATFORM_SCHEMA,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.const import (
    CONF_FRIENDLY_NAME,
    CONF_UNIQUE_ID,
    STATE_IDLE,
    STATE_OFF,
    STATE_ON,
    STATE_PAUSED,
    STATE_PLAYING,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import TemplateError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.script import Script
from homeassistant.helpers.template import Template
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import (
    CONF_APP_NAME_TEMPLATE,
    CONF_AVAILABILITY_TEMPLATE,
    CONF_ENTITY_PICTURE_TEMPLATE,
    CONF_ICON_TEMPLATE,
    CONF_IS_VOLUME_MUTED_TEMPLATE,
    CONF_MEDIA_ALBUM_NAME_TEMPLATE,
    CONF_MEDIA_ARTIST_TEMPLATE,
    CONF_MEDIA_CONTENT_ID_TEMPLATE,
    CONF_MEDIA_CONTENT_TYPE_TEMPLATE,
    CONF_MEDIA_DURATION_TEMPLATE,
    CONF_MEDIA_IMAGE_URL_TEMPLATE,
    CONF_MEDIA_PLAYERS,
    CONF_MEDIA_POSITION_TEMPLATE,
    CONF_MEDIA_POSITION_UPDATED_AT_TEMPLATE,
    CONF_MEDIA_TITLE_TEMPLATE,
    CONF_PAUSE_ACTION,
    CONF_PLAY_MEDIA_ACTION,
    CONF_REPEAT_TEMPLATE,
    CONF_SHUFFLE_TEMPLATE,
    CONF_SOUND_MODE_LIST_TEMPLATE,
    CONF_SOUND_MODE_TEMPLATE,
    CONF_SOURCE_LIST_TEMPLATE,
    CONF_SOURCE_TEMPLATE,
    CONF_TURN_OFF_ACTION,
    CONF_TURN_ON_ACTION,
    CONF_VALUE_TEMPLATE,
    CONF_VOLUME_DOWN_ACTION,
    CONF_VOLUME_LEVEL_TEMPLATE,
    CONF_VOLUME_MUTE_ACTION,
    CONF_VOLUME_SET_ACTION,
    CONF_VOLUME_UP_ACTION,
    CONF_MEDIA_NEXT_TRACK_ACTION,
    CONF_MEDIA_PREVIOUS_TRACK_ACTION,
    CONF_MEDIA_SEEK_ACTION,
    CONF_SELECT_SOURCE_ACTION,
    CONF_SELECT_SOUND_MODE_ACTION,
    CONF_SHUFFLE_SET_ACTION,
    CONF_REPEAT_SET_ACTION,
    CONF_STOP_ACTION,
)
from homeassistant.components.template.entity import TemplateEntity
from homeassistant.helpers.event import TrackTemplate

_LOGGER = logging.getLogger(__name__)

MEDIA_PLAYER_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_FRIENDLY_NAME): cv.string,
        vol.Optional(CONF_UNIQUE_ID): cv.string,
        vol.Optional(CONF_VALUE_TEMPLATE): cv.template,
        vol.Optional(CONF_ICON_TEMPLATE): cv.template,
        vol.Optional(CONF_ENTITY_PICTURE_TEMPLATE): cv.template,
        vol.Optional(CONF_AVAILABILITY_TEMPLATE): cv.template,
        # Media player specific templates
        vol.Optional(CONF_SOURCE_TEMPLATE): cv.template,
        vol.Optional(CONF_SOURCE_LIST_TEMPLATE): cv.template,
        vol.Optional(CONF_VOLUME_LEVEL_TEMPLATE): cv.template,
        vol.Optional(CONF_IS_VOLUME_MUTED_TEMPLATE): cv.template,
        vol.Optional(CONF_MEDIA_TITLE_TEMPLATE): cv.template,
        vol.Optional(CONF_MEDIA_ARTIST_TEMPLATE): cv.template,
        vol.Optional(CONF_MEDIA_ALBUM_NAME_TEMPLATE): cv.template,
        vol.Optional(CONF_MEDIA_CONTENT_ID_TEMPLATE): cv.template,
        vol.Optional(CONF_MEDIA_CONTENT_TYPE_TEMPLATE): cv.template,
        vol.Optional(CONF_MEDIA_DURATION_TEMPLATE): cv.template,
        vol.Optional(CONF_MEDIA_POSITION_TEMPLATE): cv.template,
        vol.Optional(CONF_MEDIA_POSITION_UPDATED_AT_TEMPLATE): cv.template,
        vol.Optional(CONF_MEDIA_IMAGE_URL_TEMPLATE): cv.template,
        vol.Optional(CONF_REPEAT_TEMPLATE): cv.template,
        vol.Optional(CONF_SHUFFLE_TEMPLATE): cv.template,
        vol.Optional(CONF_APP_NAME_TEMPLATE): cv.template,
        vol.Optional(CONF_SOUND_MODE_TEMPLATE): cv.template,
        vol.Optional(CONF_SOUND_MODE_LIST_TEMPLATE): cv.template,
        # Actions
        vol.Optional(CONF_TURN_ON_ACTION): cv.SCRIPT_SCHEMA,
        vol.Optional(CONF_TURN_OFF_ACTION): cv.SCRIPT_SCHEMA,
        vol.Optional(CONF_PLAY_MEDIA_ACTION): cv.SCRIPT_SCHEMA,
        vol.Optional(CONF_PAUSE_ACTION): cv.SCRIPT_SCHEMA,
        vol.Optional(CONF_STOP_ACTION): cv.SCRIPT_SCHEMA,
        vol.Optional(CONF_VOLUME_UP_ACTION): cv.SCRIPT_SCHEMA,
        vol.Optional(CONF_VOLUME_DOWN_ACTION): cv.SCRIPT_SCHEMA,
        vol.Optional(CONF_VOLUME_SET_ACTION): cv.SCRIPT_SCHEMA,
        vol.Optional(CONF_VOLUME_MUTE_ACTION): cv.SCRIPT_SCHEMA,
        vol.Optional(CONF_MEDIA_PREVIOUS_TRACK_ACTION): cv.SCRIPT_SCHEMA,
        vol.Optional(CONF_MEDIA_NEXT_TRACK_ACTION): cv.SCRIPT_SCHEMA,
        vol.Optional(CONF_MEDIA_SEEK_ACTION): cv.SCRIPT_SCHEMA,
        vol.Optional(CONF_SELECT_SOURCE_ACTION): cv.SCRIPT_SCHEMA,
        vol.Optional(CONF_SELECT_SOUND_MODE_ACTION): cv.SCRIPT_SCHEMA,
        vol.Optional(CONF_SHUFFLE_SET_ACTION): cv.SCRIPT_SCHEMA,
        vol.Optional(CONF_REPEAT_SET_ACTION): cv.SCRIPT_SCHEMA,
    }
)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {vol.Required(CONF_MEDIA_PLAYERS): cv.schema_with_slug_keys(MEDIA_PLAYER_SCHEMA)}
)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the Template Media Player."""
    media_players = []

    for device, device_config in config[CONF_MEDIA_PLAYERS].items():
        friendly_name = device_config.get(CONF_FRIENDLY_NAME, device)
        unique_id = device_config.get(CONF_UNIQUE_ID)

        state_template = device_config.get(CONF_VALUE_TEMPLATE)
        icon_template = device_config.get(CONF_ICON_TEMPLATE)
        entity_picture_template = device_config.get(CONF_ENTITY_PICTURE_TEMPLATE)
        availability_template = device_config.get(CONF_AVAILABILITY_TEMPLATE)

        templates = {
            "state": state_template,
            "icon": icon_template,
            "entity_picture": entity_picture_template,
            "availability": availability_template,
            "source": device_config.get(CONF_SOURCE_TEMPLATE),
            "source_list": device_config.get(CONF_SOURCE_LIST_TEMPLATE),
            "volume_level": device_config.get(CONF_VOLUME_LEVEL_TEMPLATE),
            "is_volume_muted": device_config.get(CONF_IS_VOLUME_MUTED_TEMPLATE),
            "media_title": device_config.get(CONF_MEDIA_TITLE_TEMPLATE),
            "media_artist": device_config.get(CONF_MEDIA_ARTIST_TEMPLATE),
            "media_album_name": device_config.get(CONF_MEDIA_ALBUM_NAME_TEMPLATE),
            "media_content_id": device_config.get(CONF_MEDIA_CONTENT_ID_TEMPLATE),
            "media_content_type": device_config.get(CONF_MEDIA_CONTENT_TYPE_TEMPLATE),
            "media_duration": device_config.get(CONF_MEDIA_DURATION_TEMPLATE),
            "media_position": device_config.get(CONF_MEDIA_POSITION_TEMPLATE),
            "media_position_updated_at": device_config.get(
                CONF_MEDIA_POSITION_UPDATED_AT_TEMPLATE
            ),
            "media_image_url": device_config.get(CONF_MEDIA_IMAGE_URL_TEMPLATE),
            "repeat": device_config.get(CONF_REPEAT_TEMPLATE),
            "shuffle": device_config.get(CONF_SHUFFLE_TEMPLATE),
            "app_name": device_config.get(CONF_APP_NAME_TEMPLATE),
            "sound_mode": device_config.get(CONF_SOUND_MODE_TEMPLATE),
            "sound_mode_list": device_config.get(CONF_SOUND_MODE_LIST_TEMPLATE),
        }

        actions = {
            "turn_on": device_config.get(CONF_TURN_ON_ACTION),
            "turn_off": device_config.get(CONF_TURN_OFF_ACTION),
            "play_media": device_config.get(CONF_PLAY_MEDIA_ACTION),
            "pause": device_config.get(CONF_PAUSE_ACTION),
            "stop": device_config.get(CONF_STOP_ACTION),
            "volume_up": device_config.get(CONF_VOLUME_UP_ACTION),
            "volume_down": device_config.get(CONF_VOLUME_DOWN_ACTION),
            "volume_set": device_config.get(CONF_VOLUME_SET_ACTION),
            "volume_mute": device_config.get(CONF_VOLUME_MUTE_ACTION),
            "media_previous_track": device_config.get(CONF_MEDIA_PREVIOUS_TRACK_ACTION),
            "media_next_track": device_config.get(CONF_MEDIA_NEXT_TRACK_ACTION),
            "media_seek": device_config.get(CONF_MEDIA_SEEK_ACTION),
            "select_source": device_config.get(CONF_SELECT_SOURCE_ACTION),
            "select_sound_mode": device_config.get(CONF_SELECT_SOUND_MODE_ACTION),
            "shuffle_set": device_config.get(CONF_SHUFFLE_SET_ACTION),
            "repeat_set": device_config.get(CONF_REPEAT_SET_ACTION),
        }

        media_players.append(
            TemplateMediaPlayer(
                hass,
                device,
                friendly_name,
                unique_id,
                templates,
                actions,
            )
        )

    async_add_entities(media_players)


class TemplateMediaPlayer(TemplateEntity, MediaPlayerEntity):
    """Representation of a Template Media Player."""

    def __init__(
        self,
        hass: HomeAssistant,
        device_id: str,
        friendly_name: str,
        unique_id: str | None,
        templates: dict[str, Template | None],
        actions: dict[str, Any],
    ) -> None:
        """Initialize the Template Media Player."""
        # Initialize TemplateEntity with basic configuration
        super().__init__(
            hass,
            availability_template=templates.get("availability"),
            icon_template=templates.get("icon"),
            entity_picture_template=templates.get("entity_picture"),
        )
        
        self._attr_name = friendly_name
        self._attr_unique_id = unique_id
        self._device_id = device_id
        self._templates = templates
        self._actions = actions
        self._context = None

        # Initialize scripts for actions
        self._scripts = {}
        for action_name, action_config in actions.items():
            if action_config is not None:
                self._scripts[action_name] = Script(
                    hass,
                    action_config,
                    friendly_name,
                    "template_media_player",
                )

    async def async_added_to_hass(self) -> None:
        """Register callbacks and track template changes."""
        # First, call the parent's async_added_to_hass to set up basic template tracking
        await super().async_added_to_hass()
        
        # Add tracking for media player specific templates
        track_templates = []
        for attr_name, template in self._templates.items():
            if attr_name not in ("icon", "entity_picture", "availability") and template is not None:
                track_templates.append(TrackTemplate(template, None))
        
        # Track the additional templates
        if track_templates:
            from homeassistant.helpers.event import async_track_template_result
            self.async_on_remove(
                async_track_template_result(
                    self.hass,
                    track_templates,
                    self._handle_media_template_update,
                )
            )

    @callback
    def _handle_media_template_update(self, event, updates) -> None:
        """Handle updates of media player templates."""
        self.async_write_ha_state()

    def _get_template_value(self, template: Template | None) -> Any:
        """Get the value of a template."""
        if template is None:
            return None
        
        try:
            return template.async_render()
        except TemplateError as err:
            _LOGGER.error("Error rendering template: %s", err)
            return None

    @cached_property
    def supported_features(self) -> MediaPlayerEntityFeature:
        """Flag media player features that are supported."""
        features = MediaPlayerEntityFeature(0)

        if self._scripts.get("turn_on"):
            features |= MediaPlayerEntityFeature.TURN_ON
        if self._scripts.get("turn_off"):
            features |= MediaPlayerEntityFeature.TURN_OFF
        if self._scripts.get("play_media"):
            features |= MediaPlayerEntityFeature.PLAY_MEDIA
        if self._scripts.get("pause"):
            features |= MediaPlayerEntityFeature.PAUSE
        if self._scripts.get("stop"):
            features |= MediaPlayerEntityFeature.STOP
        if self._scripts.get("volume_up"):
            features |= MediaPlayerEntityFeature.VOLUME_STEP
        if self._scripts.get("volume_down"):
            features |= MediaPlayerEntityFeature.VOLUME_STEP
        if self._scripts.get("volume_set"):
            features |= MediaPlayerEntityFeature.VOLUME_SET
        if self._scripts.get("volume_mute"):
            features |= MediaPlayerEntityFeature.VOLUME_MUTE
        if self._scripts.get("media_previous_track"):
            features |= MediaPlayerEntityFeature.PREVIOUS_TRACK
        if self._scripts.get("media_next_track"):
            features |= MediaPlayerEntityFeature.NEXT_TRACK
        if self._scripts.get("media_seek"):
            features |= MediaPlayerEntityFeature.SEEK
        if self._scripts.get("select_source"):
            features |= MediaPlayerEntityFeature.SELECT_SOURCE
        if self._scripts.get("select_sound_mode"):
            features |= MediaPlayerEntityFeature.SELECT_SOUND_MODE
        if self._scripts.get("shuffle_set"):
            features |= MediaPlayerEntityFeature.SHUFFLE_SET
        if self._scripts.get("repeat_set"):
            features |= MediaPlayerEntityFeature.REPEAT_SET

        return features

    @property
    def state(self) -> MediaPlayerState | None:
        """Return the state of the player."""
        state_template = self._templates.get("state")
        if state_template is None:
            return None

        state_value = self._get_template_value(state_template)
        if state_value is None:
            return None

        # Convert string state to MediaPlayerState
        state_str = str(state_value).lower()
        
        if state_str in (STATE_PLAYING, "on"):
            return MediaPlayerState.PLAYING
        elif state_str == STATE_PAUSED:
            return MediaPlayerState.PAUSED
        elif state_str in (STATE_IDLE, "idle"):
            return MediaPlayerState.IDLE
        elif state_str in (STATE_OFF, "off"):
            return MediaPlayerState.OFF
        elif state_str == STATE_UNAVAILABLE:
            return None
        
        return MediaPlayerState.IDLE

    @property
    def source(self) -> str | None:
        """Return the current input source."""
        return self._get_template_value(self._templates.get("source"))

    @property
    def source_list(self) -> list[str] | None:
        """Return the list of available input sources."""
        source_list = self._get_template_value(self._templates.get("source_list"))
        if isinstance(source_list, list):
            return source_list
        return None

    @property
    def volume_level(self) -> float | None:
        """Return the volume level."""
        volume = self._get_template_value(self._templates.get("volume_level"))
        if volume is not None:
            try:
                return float(volume)
            except (ValueError, TypeError):
                return None
        return None

    @property
    def is_volume_muted(self) -> bool | None:
        """Return boolean if volume is muted."""
        muted = self._get_template_value(self._templates.get("is_volume_muted"))
        if muted is not None:
            return bool(muted)
        return None

    @property
    def media_content_id(self) -> str | None:
        """Return the content ID of current playing media."""
        return self._get_template_value(self._templates.get("media_content_id"))

    @property
    def media_content_type(self) -> str | None:
        """Return the content type of current playing media."""
        return self._get_template_value(self._templates.get("media_content_type"))

    @property
    def media_duration(self) -> int | None:
        """Return the duration of current playing media in seconds."""
        duration = self._get_template_value(self._templates.get("media_duration"))
        if duration is not None:
            try:
                return int(duration)
            except (ValueError, TypeError):
                return None
        return None

    @property
    def media_position(self) -> int | None:
        """Return the position of current playing media in seconds."""
        position = self._get_template_value(self._templates.get("media_position"))
        if position is not None:
            try:
                return int(position)
            except (ValueError, TypeError):
                return None
        return None

    @property
    def media_position_updated_at(self):
        """Return when the position was last updated."""
        return self._get_template_value(
            self._templates.get("media_position_updated_at")
        )

    @property
    def media_image_url(self) -> str | None:
        """Return the image URL of current playing media."""
        return self._get_template_value(self._templates.get("media_image_url"))

    @property
    def media_title(self) -> str | None:
        """Return the title of current playing media."""
        return self._get_template_value(self._templates.get("media_title"))

    @property
    def media_artist(self) -> str | None:
        """Return the artist of current playing media."""
        return self._get_template_value(self._templates.get("media_artist"))

    @property
    def media_album_name(self) -> str | None:
        """Return the album name of current playing media."""
        return self._get_template_value(self._templates.get("media_album_name"))

    @property
    def repeat(self) -> str | None:
        """Return the repeat mode."""
        return self._get_template_value(self._templates.get("repeat"))

    @property
    def shuffle(self) -> bool | None:
        """Return boolean if shuffle is enabled."""
        shuffle = self._get_template_value(self._templates.get("shuffle"))
        if shuffle is not None:
            return bool(shuffle)
        return None

    @property
    def app_name(self) -> str | None:
        """Return the app name."""
        return self._get_template_value(self._templates.get("app_name"))

    @property
    def sound_mode(self) -> str | None:
        """Return the current sound mode."""
        return self._get_template_value(self._templates.get("sound_mode"))

    @property
    def sound_mode_list(self) -> list[str] | None:
        """Return the list of available sound modes."""
        sound_mode_list = self._get_template_value(
            self._templates.get("sound_mode_list")
        )
        if isinstance(sound_mode_list, list):
            return sound_mode_list
        return None

    async def async_turn_on(self) -> None:
        """Turn the media player on."""
        if script := self._scripts.get("turn_on"):
            await script.async_run(context=self._context)

    async def async_turn_off(self) -> None:
        """Turn the media player off."""
        if script := self._scripts.get("turn_off"):
            await script.async_run(context=self._context)

    async def async_play_media(
        self, media_type: str, media_id: str, **kwargs: Any
    ) -> None:
        """Play a piece of media."""
        if script := self._scripts.get("play_media"):
            await script.async_run(
                variables={
                    "media_type": media_type,
                    "media_id": media_id,
                },
                context=self._context,
            )

    async def async_media_pause(self) -> None:
        """Pause the media player."""
        if script := self._scripts.get("pause"):
            await script.async_run(context=self._context)

    async def async_media_play(self) -> None:
        """Play the media player."""
        # Using turn_on for play if pause is not available
        if script := self._scripts.get("pause"):
            await script.async_run(context=self._context)
        elif script := self._scripts.get("turn_on"):
            await script.async_run(context=self._context)

    async def async_media_stop(self) -> None:
        """Stop the media player."""
        if script := self._scripts.get("stop"):
            await script.async_run(context=self._context)

    async def async_volume_up(self) -> None:
        """Volume up the media player."""
        if script := self._scripts.get("volume_up"):
            await script.async_run(context=self._context)

    async def async_volume_down(self) -> None:
        """Volume down the media player."""
        if script := self._scripts.get("volume_down"):
            await script.async_run(context=self._context)

    async def async_set_volume_level(self, volume: float) -> None:
        """Set volume level."""
        if script := self._scripts.get("volume_set"):
            await script.async_run(
                variables={"volume_level": volume},
                context=self._context,
            )

    async def async_mute_volume(self, mute: bool) -> None:
        """Mute the volume."""
        if script := self._scripts.get("volume_mute"):
            await script.async_run(
                variables={"is_volume_muted": mute},
                context=self._context,
            )

    async def async_media_previous_track(self) -> None:
        """Send previous track command."""
        if script := self._scripts.get("media_previous_track"):
            await script.async_run(context=self._context)

    async def async_media_next_track(self) -> None:
        """Send next track command."""
        if script := self._scripts.get("media_next_track"):
            await script.async_run(context=self._context)

    async def async_media_seek(self, position: float) -> None:
        """Send seek command."""
        if script := self._scripts.get("media_seek"):
            await script.async_run(
                variables={"seek_position": position},
                context=self._context,
            )

    async def async_select_source(self, source: str) -> None:
        """Select input source."""
        if script := self._scripts.get("select_source"):
            await script.async_run(
                variables={"source": source},
                context=self._context,
            )

    async def async_select_sound_mode(self, sound_mode: str) -> None:
        """Select sound mode."""
        if script := self._scripts.get("select_sound_mode"):
            await script.async_run(
                variables={"sound_mode": sound_mode},
                context=self._context,
            )

    async def async_set_shuffle(self, shuffle: bool) -> None:
        """Enable/disable shuffle mode."""
        if script := self._scripts.get("shuffle_set"):
            await script.async_run(
                variables={"shuffle": shuffle},
                context=self._context,
            )

    async def async_set_repeat(self, repeat: str) -> None:
        """Set repeat mode."""
        if script := self._scripts.get("repeat_set"):
            await script.async_run(
                variables={"repeat": repeat},
                context=self._context,
            )
