import time


def page_loads(page, url, max_load_time=5.0, expected_status=200):
    """
    Navigates to `url` and checks:
    - HTTP status matches expected_status
    - Page loads within max_load_time seconds

    Returns a result dict: {"passed": bool, "message": str}
    """
    start = time.time()
    response = page.goto(url)
    load_time = time.time() - start

    if response is None:
        return {"passed": False, "message": f"No response received from {url}"}

    status = response.status

    if status != expected_status:
        return {
            "passed": False,
            "message": f"Expected status {expected_status}, got {status}"
        }

    if load_time > max_load_time:
        return {
            "passed": False,
            "message": f"Page took {load_time:.2f}s, exceeds limit of {max_load_time}s"
        }

    return {
        "passed": True,
        "message": f"Loaded in {load_time:.2f}s with status {status}"
    }