from asyncpg import Record
from asyncpg.connection import Connection
from asyncpg.exceptions import TransactionRollbackError


def get_prefix(nested_level: int) -> str:
    return "\t" * nested_level


def convert_dict_to_markdown(dataset: dict, nested_count: int = 0, skippable_items=None) -> str:
    """
    Converts a dictionary into markdown format with proper nesting and formatting.

    Args:
        dataset (dict): The dataset to be converted into markdown.
        nested_count (int, optional): The current level of nesting. Defaults to 0.
        skippable_items (set, optional): Contains keys that'll be skipped during conversion.

    Returns:
        str: The markdown formatted string representation of the dataset.
    """

    result = ""

    if skippable_items is None:
        skippable_items = set()

    try:
        for key, value in dataset.items():
            # Perform conversion if key is not in skippable_items and there is value present.
            if key not in skippable_items and value:
                processed_value = ""
                # This variable will be used to indent the nested dataset based on the nested_count.
                prefix = ""

                # Check if the value type is not list or dict.
                # Which helps us to identify weather or not we need to perform a recursion call.
                if type(value) in {int, str, float, bool}:
                    processed_value = str(value)
                else:
                    # If value contains dict or list then call,
                    # The function to process the nested dataset.
                    # By following the same rules.
                    _result = ""

                    if isinstance(value, dict):
                        _result = convert_dict_to_markdown(
                            value, nested_count + 1, skippable_items)

                    elif isinstance(value, list):
                        for _value in value:
                            # If the list item is empty or None,
                            # The simply continue with the next item
                            if not _value:
                                continue

                            # Only perform recursion call if the _value is again a dict or list.
                            # For normal string, integer etc,
                            # Simply append that to the _result variable.
                            if type(_value) in {dict, list}:
                                _value = convert_dict_to_markdown(
                                    _value, nested_count + 1, skippable_items)
                            else:
                                _value = get_prefix(
                                    nested_count + 1) + f"- {_value}\n"

                            # Add horizontal rule after each item in the list.
                            _result += _value + \
                                get_prefix(nested_count + 1) + "---\n"

                    if not _result:
                        continue

                    processed_value = "\n" + _result

                # Add hyphen and indent the data in case of list or dict
                # to represent them as nested data in markdown.
                if nested_count:
                    prefix += get_prefix(nested_count)
                prefix += "- "

                result += f"{prefix}**{key}**: {processed_value}\n"

    except Exception as e:
        raise e

    return result


async def is_valid_query(query: str, conn: Connection) -> dict[str, bool | str]:
    """
    Validates whether a given PostgreSQL query is syntactically and semantically correct.

    Executes the query in a rolled-back transaction to ensure no changes are committed.

    Args:
        query (str): The SQL query to validate.
        conn (Connection): An active asyncpg database connection.

    Returns:
        A dictionary with:
            - 'status': True if query is valid, False otherwise.
            - 'msg': Error message if invalid, empty string if valid.
    """

    try:
        async with conn.transaction():
            await conn.execute(query)
            raise TransactionRollbackError()

    except TransactionRollbackError:
        return {"status": True, "msg": ""}
    except Exception as e:
        return {"status": False, "msg": str(e)}


def format_select_query_results(records: list[Record]) -> str:
    """
    Format query results into markdown table.

    Args:
        records: List of database records

    Returns:
        str: Formatted markdown string
    """

    if not records:
        return "No records found"

    return convert_dict_to_markdown({
        "records": [dict(record) for record in records]
    })


def is_select_query(query: str) -> bool:
    """
    Check if the query is a SELECT statement.

    Args:
        query: SQL query string

    Returns:
        bool: True if query starts with SELECT (case-insensitive)
    """

    return query.strip().lower().startswith("select")
