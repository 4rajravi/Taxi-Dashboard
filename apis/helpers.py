import orjson  # type: ignore  # Import orjson for fast JSON parsing (ignore type checker warnings)


def parse_json_safely(json_string: str) -> dict:
    """
    Safely parse a JSON string into a Python dictionary.

    Args:
        json_string (str): The JSON string to parse.

    Returns:
        dict: The parsed dictionary if successful, otherwise an empty dict.

    This function uses orjson for fast parsing. If the input is empty or
    parsing fails, it returns an empty dictionary.
    """
    if not json_string:
        # Return empty dict if input string is empty or None
        return {}
    try:
        # Attempt to parse the JSON string
        return orjson.loads(json_string)
    except orjson.JSONDecodeError:
        # Return empty dict if parsing fails due to invalid JSON
        return {}
