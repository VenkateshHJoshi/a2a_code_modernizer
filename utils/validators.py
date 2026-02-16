import ast
from typing import Tuple, List

def validate_python_syntax(code: str) -> Tuple[bool, List[str]]:
    """
    Parses Python code to detect syntax errors.
    Returns: (is_valid, list_of_error_messages)
    """
    try:
        ast.parse(code)
        return True, []
    except SyntaxError as e:
        return False, [f"Line {e.lineno}: {e.msg}"]
    except IndentationError as e:
        return False, [f"Line {e.lineno}: {e.msg}"]
    except Exception as e:
        return False, [str(e)]