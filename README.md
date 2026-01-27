# Template Media Player for Home Assistant

A HACS installable custom Home Assistant component that provides template-based `media_player` entities. This component extends Home Assistant's native TemplateEntity to provide both state-based templates (that automatically update when referenced states change) and trigger-based templates (that only update on explicit triggers).

## Features

- **State-based templates**: Automatically update whenever Home Assistant detects a change in a referenced state
- **Trigger-based templates**: Only update on explicit triggers that you define
- **Full media player support**: All standard media player features with template-based control
- **Template all attributes**: Use Jinja2 templates for state, volume, media info, and more
- **Action support**: Define scripts/actions for all media player controls

## Installation

### HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Go to "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/Teagan42/hacs-template-media-player`
6. Select "Integration" as the category
7. Click "Add"
8. Find "Template Media Player" in the integration list and install it
9. Restart Home Assistant

### Manual Installation

1. Download the `custom_components/template_media_player` directory from this repository
2. Copy it to your Home Assistant's `custom_components` directory
3. Restart Home Assistant

## Configuration

Add the following to your `configuration.yaml`:

```yaml
media_player:
  - platform: template_media_player
    media_players:
      example_player:
        friendly_name: "Example Media Player"
        unique_id: example_media_player_1
        
        # State template - determines the current state
        value_template: "{{ states('media_player.real_player') }}"
        
        # Optional: Availability template
        availability_template: "{{ states('media_player.real_player') != 'unavailable' }}"
        
        # Optional: Media information templates
        media_title_template: "{{ state_attr('media_player.real_player', 'media_title') }}"
        media_artist_template: "{{ state_attr('media_player.real_player', 'media_artist') }}"
        media_album_name_template: "{{ state_attr('media_player.real_player', 'media_album_name') }}"
        media_content_id_template: "{{ state_attr('media_player.real_player', 'media_content_id') }}"
        media_content_type_template: "{{ state_attr('media_player.real_player', 'media_content_type') }}"
        media_duration_template: "{{ state_attr('media_player.real_player', 'media_duration') }}"
        media_position_template: "{{ state_attr('media_player.real_player', 'media_position') }}"
        media_image_url_template: "{{ state_attr('media_player.real_player', 'entity_picture') }}"
        
        # Optional: Volume templates
        volume_level_template: "{{ state_attr('media_player.real_player', 'volume_level') }}"
        is_volume_muted_template: "{{ state_attr('media_player.real_player', 'is_volume_muted') }}"
        
        # Optional: Source templates
        source_template: "{{ state_attr('media_player.real_player', 'source') }}"
        source_list_template: "{{ state_attr('media_player.real_player', 'source_list') }}"
        
        # Optional: Other templates
        repeat_template: "{{ state_attr('media_player.real_player', 'repeat') }}"
        shuffle_template: "{{ state_attr('media_player.real_player', 'shuffle') }}"
        sound_mode_template: "{{ state_attr('media_player.real_player', 'sound_mode') }}"
        sound_mode_list_template: "{{ state_attr('media_player.real_player', 'sound_mode_list') }}"
        
        # Actions - called when corresponding service is used
        turn_on:
          service: media_player.turn_on
          target:
            entity_id: media_player.real_player
            
        turn_off:
          service: media_player.turn_off
          target:
            entity_id: media_player.real_player
            
        play_media:
          service: media_player.play_media
          target:
            entity_id: media_player.real_player
          data:
            media_content_type: "{{ media_type }}"
            media_content_id: "{{ media_id }}"
            
        pause:
          service: media_player.media_pause
          target:
            entity_id: media_player.real_player
            
        volume_set:
          service: media_player.volume_set
          target:
            entity_id: media_player.real_player
          data:
            volume_level: "{{ volume_level }}"
```

## Template Variables

### Available in All Templates

All templates have access to standard Home Assistant Jinja2 template features:
- `states('entity_id')` - Get the state of an entity
- `state_attr('entity_id', 'attribute')` - Get an attribute of an entity
- `now()` - Current datetime
- All standard Jinja2 filters and functions

### Available in Action Templates

Actions receive additional variables based on the action type:

- **play_media**: `media_type`, `media_id`
- **volume_set**: `volume_level`
- **volume_mute**: `is_volume_muted`
- **media_seek**: `seek_position`
- **select_source**: `source`
- **select_sound_mode**: `sound_mode`
- **shuffle_set**: `shuffle`
- **repeat_set**: `repeat`

## Supported Features

The component automatically determines supported features based on which actions you define:

- `turn_on` action → TURN_ON feature
- `turn_off` action → TURN_OFF feature
- `play_media` action → PLAY_MEDIA feature
- `pause` action → PAUSE feature
- `stop` action → STOP feature
- `volume_up` / `volume_down` actions → VOLUME_STEP feature
- `volume_set` action → VOLUME_SET feature
- `volume_mute` action → VOLUME_MUTE feature
- `media_previous_track` action → PREVIOUS_TRACK feature
- `media_next_track` action → NEXT_TRACK feature
- `media_seek` action → SEEK feature
- `select_source` action → SELECT_SOURCE feature
- `select_sound_mode` action → SELECT_SOUND_MODE feature
- `shuffle_set` action → SHUFFLE_SET feature
- `repeat_set` action → REPEAT_SET feature

## Use Cases

### Proxy Media Player

Create a template media player that proxies another media player but modifies its behavior:

```yaml
media_player:
  - platform: template_media_player
    media_players:
      proxy_player:
        friendly_name: "Proxy Player"
        value_template: "{{ states('media_player.bedroom_speaker') }}"
        volume_level_template: "{{ state_attr('media_player.bedroom_speaker', 'volume_level') | float * 0.5 }}"
        turn_on:
          service: media_player.turn_on
          target:
            entity_id: media_player.bedroom_speaker
```

### Combined Media Player

Combine multiple media players into a single template entity:

```yaml
media_player:
  - platform: template_media_player
    media_players:
      combined_player:
        friendly_name: "All Speakers"
        value_template: >-
          {% if is_state('media_player.living_room', 'playing') or 
                is_state('media_player.bedroom', 'playing') %}
            playing
          {% else %}
            idle
          {% endif %}
        turn_on:
          - service: media_player.turn_on
            target:
              entity_id: media_player.living_room
          - service: media_player.turn_on
            target:
              entity_id: media_player.bedroom
```

### Virtual Media Player

Create a virtual media player controlled by input entities:

```yaml
media_player:
  - platform: template_media_player
    media_players:
      virtual_player:
        friendly_name: "Virtual Player"
        value_template: "{{ states('input_select.player_state') }}"
        volume_level_template: "{{ states('input_number.player_volume') | float }}"
        media_title_template: "{{ states('input_text.current_track') }}"
        turn_on:
          service: input_select.select_option
          target:
            entity_id: input_select.player_state
          data:
            option: "playing"
        volume_set:
          service: input_number.set_value
          target:
            entity_id: input_number.player_volume
          data:
            value: "{{ volume_level }}"
```

## Troubleshooting

### Templates not updating

Make sure your templates reference entities that actually change. The component tracks entity dependencies and only updates when those entities change.

### Actions not working

Verify that your action configurations are valid service calls. Check Home Assistant logs for errors.

### Entity not showing up

1. Check your `configuration.yaml` syntax
2. Restart Home Assistant after making changes
3. Check Home Assistant logs for errors

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Credits

This component extends Home Assistant's native TemplateEntity from:
https://github.com/home-assistant/core/blob/dev/homeassistant/components/template/entity.py
