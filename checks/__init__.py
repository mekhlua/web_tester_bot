from checks.page_checks import page_loads

CHECK_REGISTRY = {
    "page_loads": page_loads,
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