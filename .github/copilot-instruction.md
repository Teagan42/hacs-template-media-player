# Copilot Playbook: Template Media Player

## Mission overview
Build and maintain a reliable, HACS-installable Home Assistant integration that provides template-driven `media_player` entities with optional script control, triggers, and base-entity delegation.

## Repository map
- `custom_components/template_media_player/__init__.py`: Integration setup, config reload wiring.
- `custom_components/template_media_player/media_player.py`: Core entity implementation and behavior.
- `custom_components/template_media_player/const.py`: Integration constants.
- `custom_components/template_media_player/services.yaml`: Service descriptions.
- `custom_components/template_media_player/manifest.json`: Integration metadata.
- `tests/`: Pytest suite for component behavior.
- `README.md`: User-facing documentation and examples.
- `pyproject.toml`: Dependencies, tooling configuration.

## Development workflow (non-negotiable)
1) Understand current behavior in `custom_components/template_media_player/media_player.py` and `custom_components/template_media_player/__init__.py`.
2) Make the smallest change that solves the task.
3) Add or update tests for behavior changes.
4) Run quality gates in this exact order:
   - `uv run ruff check .`
   - `uv run black .`
   - `uv run pytest`
5) If any step fails, fix the root cause, then re-run the full sequence.

## Quality bar / enforcement
- Do not regress existing behavior; maintain backward compatibility where possible.
- Keep templates, triggers, and script behavior deterministic and well-tested.
- Avoid unnecessary dependencies or broad refactors.
- No unused imports, dead code, or silent error swallowing.
- Every behavior change must include or adjust tests.

## Release checklist
- Update `manifest.json` version if required by release process.
- Verify `README.md` configuration examples match current behavior.
- Run full quality gates (ruff, black, pytest) and confirm green.
- Ensure `services.yaml` is accurate for any service changes.
- Tag release and update HACS metadata if applicable.

## Troubleshooting & triage
- Test failures: run `uv run pytest -vv` and fix the first failing test before the rest.
- Import errors in HA: verify integration domain, manifest, and HA version compatibility.
- Template or trigger issues: confirm `async_attach_trigger`/`async_initialize_triggers` compatibility and check config schema.
- Service script issues: validate scripts in YAML and confirm service names and variables.
- If behavior differs between HA versions, add a small compatibility shim and cover it with tests.
