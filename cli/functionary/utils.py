from rich.console import Console
from rich.table import Table


def _get_str_value(value):
    """Helper function to return a string representation of a value.

    If the passed in value is not a dict, this will return the str() of it.
    If it is a dict, it will return the str() of the first item that doesn't
    have a key of 'id', otherwise it will return None.
    """
    if not isinstance(value, dict):
        return str(value)

    # If the value is a dict, find the first key that's not 'id'
    dictVals = [v for k, v in value.items() if k != "id"]
    return None if len(dictVals) == 0 else str(dictVals[0])


def format_results(results, title="", excluded_fields=[]):
    """
    Helper function to organize table results using Rich

    Args:
        results: Results to format as a List
        title: Optional table title as a String

    Returns:
        None
    """
    table = Table(title=title, show_lines=True, title_justify="left")
    console = Console()
    first_row = True

    for item in results:
        row_data = []
        for key, value in item.items():
            if key in excluded_fields:
                continue
            if first_row:
                table.add_column(key.capitalize())
            row_data.append(_get_str_value(value) if value else None)
        table.add_row(*row_data)
        first_row = False
    console.print(table)
