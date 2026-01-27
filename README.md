# Template Media Player for Home Assistant

A HACS installable custom Home Assistant component that provides template-based `media_player` entities. This component extends Home Assistant's native `TemplateEntity` to provide both state-based templates (that automatically update when referenced states change) and trigger-based templates (that only update on explicit triggers).

## Features

- **State-based templates**: Automatically update whenever Home Assistant detects a change in a referenced state using `add_template_attribute`
- **Trigger-based templates**: Only update on explicit triggers that you define
- **Full media player support**: All standard media player features with script-based control
- **Custom attributes**: Define any custom attributes using templates with `attributes`
- **Service scripts**: Define scripts for all media player operations using `service_scripts`
- **Source/sound mode scripts**: Define scripts for specific sources or sound modes
- **Entity delegation**: Optionally delegate browse/search functionality to other media players
- **Base entity**: Optionally use another media player as a fallback for undefined operations

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
        name: "{{ 'Example Player' }}"  # Optional: template for name
        unique_id: example_media_player_1
        icon: "{{ 'mdi:speaker' }}"  # Optional: template for icon
        picture: "{{ state_attr('media_player.real_player', 'entity_picture') }}"  # Optional
        
        # State template - determines the current state
        state: "{{ states('media_player.real_player') }}"
        
        # Availability template
        availability: "{{ states('media_player.real_player') != 'unavailable' }}"
        
        # Custom attributes (using schema_with_slug_keys)
        attributes:
          media_title: "{{ state_attr('media_player.real_player', 'media_title') }}"
          media_artist: "{{ state_attr('media_player.real_player', 'media_artist') }}"
          media_album: "{{ state_attr('media_player.real_player', 'media_album_name') }}"
          volume_level: "{{ state_attr('media_player.real_player', 'volume_level') }}"
          is_volume_muted: "{{ state_attr('media_player.real_player', 'is_volume_muted') }}"
          source: "{{ state_attr('media_player.real_player', 'source') }}"
        
        # Service scripts (using schema_with_slug_keys)
        service_scripts:
          turn_on:
            service: media_player.turn_on
            target:
              entity_id: media_player.real_player
          
          turn_off:
            service: media_player.turn_off
            target:
              entity_id: media_player.real_player
          
          media_play:
            service: media_player.media_play
            target:
              entity_id: media_player.real_player
          
          media_pause:
            service: media_player.media_pause
            target:
              entity_id: media_player.real_player
          
          volume_set:
            service: media_player.volume_set
            target:
              entity_id: media_player.real_player
            data:
              volume_level: "{{ volume_level }}"
          
          play_media:
            service: media_player.play_media
            target:
              entity_id: media_player.real_player
            data:
              media_content_type: "{{ media_type }}"
              media_content_id: "{{ media_id }}"
        
        # Optional: Source scripts (each source has its own script)
        source_scripts:
          spotify:
            service: media_player.select_source
            target:
              entity_id: media_player.real_player
            data:
              source: "Spotify"
          
          radio:
            service: media_player.select_source
            target:
              entity_id: media_player.real_player
            data:
              source: "Radio"
        
        # Optional: Sound mode scripts (each sound mode has its own script)
        sound_mode_scripts:
          stereo:
            service: media_player.select_sound_mode
            target:
              entity_id: media_player.real_player
            data:
              sound_mode: "stereo"
          
          surround:
            service: media_player.select_sound_mode
            target:
              entity_id: media_player.real_player
            data:
              sound_mode: "surround"
```

## Advanced Configuration

### Using Triggers (Trigger-based Templates)

```yaml
media_player:
  - platform: template_media_player
    media_players:
      triggered_player:
        name: "Triggered Player"
        state: "{{ trigger.to_state.state }}"
        
        attributes:
          last_updated: "{{ now() }}"
        
        # Triggers that cause the entity to update
        triggers:
          - platform: state
            entity_id: media_player.source_player
        
        service_scripts:
          turn_on:
            service: media_player.turn_on
            target:
              entity_id: media_player.source_player
```

### Using Base Entity (Fallback)

```yaml
media_player:
  - platform: template_media_player
    media_players:
      enhanced_player:
        name: "Enhanced Player"
        
        # Use another media player as base for undefined operations
        base_entity_id: media_player.real_player
        
        # Override specific attributes with templates
        attributes:
          custom_info: "{{ 'Custom: ' ~ state_attr('media_player.real_player', 'media_title') }}"
        
        # Override specific operations with scripts
        service_scripts:
          volume_set:
            # Custom volume scaling
            service: media_player.volume_set
            target:
              entity_id: media_player.real_player
            data:
              volume_level: "{{ volume_level * 0.8 }}"  # Max volume at 80%
```

### Using Browse and Search Entities

```yaml
media_player:
  - platform: template_media_player
    media_players:
      delegated_player:
        name: "Delegated Player"
        state: "{{ states('media_player.main_player') }}"
        
        # Delegate browse functionality to another player
        browse_entity_id: media_player.spotify
        
        # Delegate search functionality to another player
        search_entity_id: media_player.youtube_music
        
        service_scripts:
          turn_on:
            service: media_player.turn_on
            target:
              entity_id: media_player.main_player
```

## Configuration Options

### Main Options

| Option | Type | Required | Description |
|--------|------|----------|-------------|
| `name` | template | No | Template for the entity name |
| `unique_id` | string | No | Unique ID for the entity |
| `icon` | template | No | Template for the entity icon |
| `picture` | template | No | Template for the entity picture |
| `state` | template | No | Template for the entity state |
| `availability` | template | No | Template for availability (default: true) |
| `device_class` | string | No | Device class for the media player |
| `attributes` | dict | No | Custom attributes as templates (slug_keys) |
| `variables` | dict | No | Variables available in scripts |
| `base_entity_id` | entity_id | No | Base media player for fallback operations |
| `search_entity_id` | entity_id | No | Media player for search operations |
| `browse_entity_id` | entity_id | No | Media player for browse operations |
| `service_scripts` | dict | No | Scripts for media player services (slug_keys) |
| `source_scripts` | dict | No | Scripts for each source (slug_keys) |
| `sound_mode_scripts` | dict | No | Scripts for each sound mode (slug_keys) |
| `triggers` | list | No | Triggers for trigger-based updates |

### Service Script Keys

Use these keys in the `service_scripts` dictionary:

- `turn_on` - Turn on the media player
- `turn_off` - Turn off the media player
- `media_play` - Play media
- `media_pause` - Pause media
- `media_stop` - Stop media
- `media_next_track` - Next track
- `media_previous_track` - Previous track
- `media_seek` - Seek to position (variable: `position`)
- `volume_up` - Volume up
- `volume_down` - Volume down
- `volume_set` - Set volume (variable: `volume_level`)
- `volume_mute` - Mute volume (variable: `is_volume_muted`)
- `play_media` - Play specific media (variables: `media_type`, `media_id`)
- `shuffle_set` - Set shuffle mode (variable: `shuffle`)
- `repeat_set` - Set repeat mode (variable: `repeat`)
- `browse_media` - Browse media (variables: `media_content_type`, `media_content_id`)
- `search_media` - Search media (query variables)

## Use Cases

### Virtual Media Player

Create a virtual media player controlled by input entities:

```yaml
media_player:
  - platform: template_media_player
    media_players:
      virtual_player:
        name: "Virtual Player"
        state: "{{ states('input_select.player_state') }}"
        
        attributes:
          media_title: "{{ states('input_text.current_track') }}"
          volume_level: "{{ states('input_number.player_volume') | float }}"
        
        service_scripts:
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

### Combined Multi-Room Player

```yaml
media_player:
  - platform: template_media_player
    media_players:
      whole_house:
        name: "Whole House Audio"
        
        state: >-
          {% set players = ['media_player.living_room', 'media_player.bedroom'] %}
          {% if players | select('is_state', 'playing') | list | count > 0 %}
            playing
          {% elif players | select('is_state', 'paused') | list | count > 0 %}
            paused
          {% else %}
            idle
          {% endif %}
        
        attributes:
          volume_level: >-
            {% set players = ['media_player.living_room', 'media_player.bedroom'] %}
            {% set volumes = players | map('state_attr', 'volume_level') | select('number') | list %}
            {{ (volumes | sum / volumes | length) | round(2) if volumes else 0.5 }}
        
        service_scripts:
          turn_on:
            - service: media_player.turn_on
              target:
                entity_id:
                  - media_player.living_room
                  - media_player.bedroom
          
          volume_set:
            - service: media_player.volume_set
              target:
                entity_id:
                  - media_player.living_room
                  - media_player.bedroom
              data:
                volume_level: "{{ volume_level }}"
```

## Template Variables in Scripts

Scripts have access to these variables depending on the operation:

- **All scripts**: Access to `variables` defined in configuration
- **volume_set**: `volume_level` (float 0.0-1.0)
- **volume_mute**: `is_volume_muted` (boolean)
- **media_seek**: `position` (seconds)
- **play_media**: `media_type`, `media_id` (strings)
- **shuffle_set**: `shuffle` (boolean)
- **repeat_set**: `repeat` (string)

## Reloading Configuration

The component supports reloading configuration without restarting Home Assistant. This is useful when you make changes to your template media player configuration and want to apply them immediately.

### Using the Reload Service

Call the `template_media_player.reload` service:

1. Go to Developer Tools > Services
2. Select `template_media_player.reload`
3. Click "Call Service"

Or use YAML:

```yaml
service: template_media_player.reload
```

This will:
- Remove all existing template media player entities
- Reload the configuration from `configuration.yaml`
- Create new entities with the updated configuration
- Fire an `event_template_media_player_reloaded` event

### Automation Example

You can automate configuration reloads when the configuration file changes:

```yaml
automation:
  - alias: "Reload Template Media Players on Config Change"
    trigger:
      - platform: event
        event_type: folder_watcher
        event_data:
          event_type: modified
          path: /config/configuration.yaml
    action:
      - service: template_media_player.reload
```

## Troubleshooting

### Templates not updating

- Ensure templates reference entities that change
- Use `triggers` for explicit update control
- Check template syntax in Developer Tools > Template

### Actions not working

- Verify service call syntax
- Check Home Assistant logs for errors
- Test service calls in Developer Tools > Services

### Entity not showing up

1. Check `configuration.yaml` syntax
2. Restart Home Assistant or use the reload service
3. Check logs for errors

### Configuration changes not applying

1. Use the `template_media_player.reload` service to reload without restart
2. If reload doesn't work, restart Home Assistant
3. Check logs for configuration errors

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Credits

This component extends Home Assistant's native TemplateEntity from:
https://github.com/home-assistant/core/blob/dev/homeassistant/components/template/template_entity.py
