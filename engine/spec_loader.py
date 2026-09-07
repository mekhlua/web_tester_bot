import yaml
from pathlib import Path


class SpecError(Exception):
    """Raised when a spec file is missing required fields or malformed."""
    pass


def load_spec(spec_path):
    """
    Loads and validates a YAML requirements spec file.
    Returns a Python dict representing the spec.
    """
    path = Path(spec_path)

    if not path.exists():
        raise SpecError(f"Spec file not found: {spec_path}")

    with open(path, "r") as f:
        try:
            spec = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise SpecError(f"Invalid YAML in {spec_path}: {e}")

    _validate_spec(spec, spec_path)
    return spec


def _validate_spec(spec, spec_path):
    if not isinstance(spec, dict):
        raise SpecError(f"{spec_path} must contain a YAML mapping at the top level")

    required_top_level = ["site", "base_url", "pages"]
    for field in required_top_level:
        if field not in spec:
            raise SpecError(f"{spec_path} is missing required field: '{field}'")

    if not isinstance(spec["pages"], list) or len(spec["pages"]) == 0:
        raise SpecError(f"{spec_path} must have at least one entry under 'pages'")

    for i, page in enumerate(spec["pages"]):
        if "path" not in page:
            raise SpecError(f"{spec_path}: pages[{i}] is missing 'path'")
        if "checks" not in page or not isinstance(page["checks"], list):
            raise SpecError(f"{spec_path}: pages[{i}] must have a 'checks' list")
        for j, check in enumerate(page["checks"]):
            if "type" not in check:
                raise SpecError(f"{spec_path}: pages[{i}].checks[{j}] is missing 'type'")