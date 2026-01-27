"""Constants for Template Media Player."""

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
