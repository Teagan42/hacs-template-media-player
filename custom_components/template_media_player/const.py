"""Constants for Template Media Player."""

import voluptuous as vol

from homeassistant.helpers import config_validation as cv
from homeassistant.const import (
    CONF_DEVICE_CLASS,
    CONF_ICON,
    CONF_NAME,
    CONF_UNIQUE_ID,
)

DOMAIN = "template_media_player"

# Configuration
CONF_MEDIA_PLAYERS = "media_players"
CONF_ATTRIBUTES = "attributes"
CONF_AVAILABILITY = "availability"
CONF_DEFAULT_ENTITY_ID = "default_entity_id"
CONF_PICTURE = "picture"
CONF_STATE = "state"
CONF_VARIABLES = "variables"
CONF_TRIGGERS = "triggers"

# Entity references for delegating functionality
CONF_BASE_MEDIA_PLAYER_ENTITY_ID = "base_entity_id"
CONF_SEARCH_MEDIA_ENTITY_ID = "search_entity_id"
CONF_BROWSE_MEDIA_ENTITY_ID = "browse_entity_id"

# Service script configuration (using dict of scripts)
CONF_SERVICE_SCRIPTS = "service_scripts"
CONF_SOURCE_SCRIPTS = "source_scripts"
CONF_SOUND_MODE_SCRIPTS = "sound_mode_scripts"

# Service script keys (for CONF_SERVICE_SCRIPTS dict)
CONF_MEDIA_PLAY_SCRIPT = "media_play"
CONF_MEDIA_PAUSE_SCRIPT = "media_pause"
CONF_MEDIA_STOP_SCRIPT = "media_stop"
CONF_MEDIA_NEXT_TRACK_SCRIPT = "media_next_track"
CONF_MEDIA_PREVIOUS_TRACK_SCRIPT = "media_previous_track"
CONF_MEDIA_SEEK_SCRIPT = "media_seek"
CONF_VOLUME_UP_SCRIPT = "volume_up"
CONF_VOLUME_DOWN_SCRIPT = "volume_down"
CONF_VOLUME_SET_SCRIPT = "volume_set"
CONF_VOLUME_MUTE_SCRIPT = "volume_mute"
CONF_TURN_ON_SCRIPT = "turn_on"
CONF_TURN_OFF_SCRIPT = "turn_off"
CONF_PLAY_MEDIA_SCRIPT = "play_media"
CONF_SHUFFLE_SET_SCRIPT = "shuffle_set"
CONF_REPEAT_SET_SCRIPT = "repeat_set"
CONF_BROWSE_MEDIA_SCRIPT = "browse_media"
CONF_SEARCH_MEDIA_SCRIPT = "search_media"

PLATFORM_CONFIG_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_NAME): cv.template,
        vol.Optional(CONF_UNIQUE_ID): cv.string,
        vol.Optional(CONF_ICON): cv.template,
        vol.Optional(CONF_PICTURE): cv.template,
        vol.Optional(CONF_DEFAULT_ENTITY_ID): cv.entity_id,
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
        vol.Optional(CONF_TRIGGERS, default=[]): cv.TRIGGER_SCHEMA,
    }
)
