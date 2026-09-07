from checks import get_check


def run_check(page, check_config):
    """
    Runs a single check based on its spec config dict.
    check_config example: {"type": "page_loads", "max_load_time": 5.0}
    """
    check_type = check_config["type"]
    kwargs = {k: v for k, v in check_config.items() if k != "type"}

    try:
        check_fn = get_check(check_type)
        result = check_fn(page, **kwargs)
    except Exception as e:
        result = {"passed": False, "message": f"Check raised an error: {e}"}

    result["check_type"] = check_type
    return result
