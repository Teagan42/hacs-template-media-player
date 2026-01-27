from __future__ import annotations

import custom_components.template_media_player.entity as entity
from homeassistant.components.template.template_entity import TemplateEntity


def test_template_entity_reexport() -> None:
    assert entity.TemplateEntity is TemplateEntity
