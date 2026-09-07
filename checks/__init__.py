from checks.page_checks import (
    page_loads,
    element_exists,
    text_present,
    link_valid,
    no_console_errors,
)

CHECK_REGISTRY = {
    "page_loads": page_loads,
    "element_exists": element_exists,
    "text_present": text_present,
    "link_valid": link_valid,
    "no_console_errors": no_console_errors,
}


def get_check(check_type):
    """
    Looks up a check function by its spec 'type' name.
    Raises KeyError with a clear message if unknown.
    """
    if check_type not in CHECK_REGISTRY:
        available = ", ".join(CHECK_REGISTRY.keys())
        raise KeyError(
            f"Unknown check type '{check_type}'. Available: {available}"
        )
    return CHECK_REGISTRY[check_type]
