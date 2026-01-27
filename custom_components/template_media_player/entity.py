"""Template entity for Template Media Player."""

from __future__ import annotations

try:
    from homeassistant.components.template.template_entity import TemplateEntity
except ImportError:  # HA <= 2025.12
    from homeassistant.components.template.entity import TemplateEntity

__all__ = ["TemplateEntity"]
