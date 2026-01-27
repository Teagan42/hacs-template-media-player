#!/usr/bin/env python3
"""Validation script for Template Media Player component."""

import json
import sys
from pathlib import Path


def validate_structure():
    """Validate the component structure."""
    print("🔍 Validating Template Media Player component structure...")

    errors = []
    warnings = []

    # Check required files
    required_files = [
        "custom_components/template_media_player/__init__.py",
        "custom_components/template_media_player/manifest.json",
        "custom_components/template_media_player/const.py",
        "custom_components/template_media_player/entity.py",
        "custom_components/template_media_player/media_player.py",
        "hacs.json",
        "README.md",
        "LICENSE",
    ]

    for file_path in required_files:
        if not Path(file_path).exists():
            errors.append(f"❌ Missing required file: {file_path}")
        else:
            print(f"✅ Found: {file_path}")

    # Validate manifest.json
    try:
        with open("custom_components/template_media_player/manifest.json") as f:
            manifest = json.load(f)

            required_keys = ["domain", "name", "version", "documentation", "codeowners"]
            for key in required_keys:
                if key not in manifest:
                    errors.append(f"❌ Missing key in manifest.json: {key}")
                else:
                    print(f"✅ manifest.json has '{key}': {manifest[key]}")

            if manifest.get("domain") != "template_media_player":
                errors.append(
                    f"❌ Domain should be 'template_media_player', got: {manifest.get('domain')}"
                )

    except json.JSONDecodeError as e:
        errors.append(f"❌ Invalid JSON in manifest.json: {e}")
    except FileNotFoundError:
        errors.append("❌ manifest.json not found")

    # Validate hacs.json
    try:
        with open("hacs.json") as f:
            hacs = json.load(f)
            print(f"✅ hacs.json is valid: {hacs}")
    except json.JSONDecodeError as e:
        errors.append(f"❌ Invalid JSON in hacs.json: {e}")
    except FileNotFoundError:
        errors.append("❌ hacs.json not found")

    # Check Python files can be compiled
    python_files = [
        "custom_components/template_media_player/__init__.py",
        "custom_components/template_media_player/const.py",
        "custom_components/template_media_player/entity.py",
        "custom_components/template_media_player/media_player.py",
    ]

    for py_file in python_files:
        try:
            with open(py_file) as f:
                compile(f.read(), py_file, "exec")
            print(f"✅ {py_file} has valid syntax")
        except SyntaxError as e:
            errors.append(f"❌ Syntax error in {py_file}: {e}")
        except FileNotFoundError:
            errors.append(f"❌ File not found: {py_file}")
        except Exception as e:
            errors.append(f"❌ Error reading {py_file}: {e}")

    # Check entity.py imports native TemplateEntity
    try:
        with open("custom_components/template_media_player/entity.py") as f:
            content = f.read()
            if (
                "from homeassistant.components.template.entity import TemplateEntity"
                in content
            ):
                print(
                    "✅ entity.py imports native TemplateEntity from Home Assistant core"
                )
            else:
                errors.append("❌ entity.py does not import native TemplateEntity")
    except FileNotFoundError:
        pass  # Already reported above

    # Check media_player.py has required components
    try:
        with open("custom_components/template_media_player/media_player.py") as f:
            content = f.read()

            required_components = [
                ("MediaPlayerEntity", "MediaPlayerEntity class"),
                ("TemplateEntity", "TemplateEntity"),
                ("async_setup_platform", "Platform setup function"),
                ("TemplateMediaPlayer", "TemplateMediaPlayer class"),
            ]

            for component, description in required_components:
                if component in content:
                    print(f"✅ media_player.py contains {description}")
                else:
                    warnings.append(
                        f"⚠️  media_player.py might be missing {description}"
                    )

    except FileNotFoundError:
        pass  # Already reported above

    # Print summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)

    if errors:
        print(f"\n❌ Found {len(errors)} error(s):")
        for error in errors:
            print(f"  {error}")

    if warnings:
        print(f"\n⚠️  Found {len(warnings)} warning(s):")
        for warning in warnings:
            print(f"  {warning}")

    if not errors and not warnings:
        print("\n✅ All validations passed! Component structure is correct.")
        return 0
    elif not errors:
        print("\n✅ All critical validations passed (warnings are informational).")
        return 0
    else:
        print("\n❌ Validation failed. Please fix the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(validate_structure())
