# safe_eval.py
import ast
import operator as op

# allowed operators
ALLOWED_OPERATORS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
    ast.Mod: op.mod,
    ast.USub: op.neg,
    ast.UAdd: op.pos,
    ast.FloorDiv: op.floordiv,
}

ALLOWED_COMPARISONS = {
    ast.Eq: op.eq,
    ast.NotEq: op.ne,
    ast.Lt: op.lt,
    ast.LtE: op.le,
    ast.Gt: op.gt,
    ast.GtE: op.ge,
}

def _eval(node):
    if isinstance(node, ast.Expression):
        return _eval(node.body)

    if isinstance(node, ast.Num):  # < Py3.8
        return node.n
    if hasattr(ast, "Constant") and isinstance(node, ast.Constant):  # Py3.8+
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError("Only int/float constants are allowed")

    if isinstance(node, ast.BinOp):
        left = _eval(node.left)
        right = _eval(node.right)
        op_type = type(node.op)
        if op_type in ALLOWED_OPERATORS:
            return ALLOWED_OPERATORS[op_type](left, right)
        raise ValueError(f"Operator {op_type} not allowed")

    if isinstance(node, ast.UnaryOp):
        operand = _eval(node.operand)
        op_type = type(node.op)
        if op_type in ALLOWED_OPERATORS:
            return ALLOWED_OPERATORS[op_type](operand)
        raise ValueError("Unary operator not allowed")

    if isinstance(node, ast.Compare):
        left = _eval(node.left)
        results = []
        for op_node, comparator in zip(node.ops, node.comparators):
            right = _eval(comparator)
            op_type = type(op_node)
            if op_type in ALLOWED_COMPARISONS:
                results.append(ALLOWED_COMPARISONS[op_type](left, right))
                left = right
            else:
                raise ValueError("Comparison not allowed")
        return all(results)

    raise ValueError(f"Unsupported expression: {ast.dump(node)}")

def evaluate_expression(expr: str):
    """Safely evaluate arithmetic/comparison expression like '5+8' or '7>3'."""
    # strip commas and extra spaces
    expr = expr.replace(",", "")
    try:
        parsed = ast.parse(expr, mode="eval")
        return _eval(parsed)
    except Exception as e:
        raise ValueError(f"Invalid expression: {e}")
