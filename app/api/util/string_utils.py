from typing import Any, Optional


def join_list(joining_list: Optional[list], join_txt: str = "\n") -> str:
    """
    Utility to join a list.

    Functionally equivalent to:
    "" if joining_list is None else "\n".join(joining_list)
    """
    if not joining_list:
        return ""

    return join_txt.join(joining_list)


def blank_for_null(value: Optional[Any]) -> str:
    """
    Utility to make a string blank if its null

    Functionally equivalent to

    ```"" if value is None else str(value)```
    """
    # If a value is blank
    if value is None:
        return ""
    return str(value)
