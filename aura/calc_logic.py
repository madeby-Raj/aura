# calc_logic.py
"""
Safe math evaluation:
- calculate_expression(text): returns string result or None
  Uses sympy after sanitizing input; disallows letters and suspicious tokens.
- compare_logic(text): safe simple comparisons like 'is 5 > 3'
"""

import re
from sympy import sympify, SympifyError
import math

# allowed characters: digits, whitespace, operators + - * / % ^ ( ) . 
_allowed_re = re.compile(r'^[0-9\s\+\-\*\/\%\^\.\(\)]+$')

def _sanitize_expr(expr):
    """Replace common user words and ensure allowed chars only.
    Replace '^' with '**' for power, remove accidental commas.
    """
    s = expr.replace(',', '')
    s = s.replace('x', '*')   # user might use 'x' for multiply
    s = s.replace('X', '*')
    s = s.replace('^', '**')
    # remove any characters outside allowed set
    if not _allowed_re.match(s):
        return None
    return s

def calculate_expression(text):
    """Try to safely evaluate a math expression. Returns a reply string or None."""
    # extract a potential math expression from text - naive approach:
    # If text contains "=" or starts with typical math words, try to evaluate the whole text
    cand = text.strip()
    # remove 'calculate' or 'what is' prefix if present
    cand = re.sub(r"^(calculate|what is|what's|compute)\s*", "", cand, flags=re.I)

    cand = cand.strip()
    # sanitize
    s = _sanitize_expr(cand)
    if s is None or s == '':
        return None
    try:
        # sympify for safe math parse
        val = sympify(s).evalf()
        # pretty formatting: integer vs float
        if val.is_Integer:
            res = int(val)
        else:
            # limit float precision for display
            res = float(round(val, 6))
        return f"The answer is {res}"
    except (SympifyError, Exception):
        return None

def compare_logic(text):
    """Handle simple logical checks: is 5 > 3, is 10 equal 10 etc."""
    m = re.search(r'is\s*([\d\.]+)\s*(>=|<=|>|<|==|=)\s*([\d\.]+)', text)
    if not m:
        # also try "is 5 greater than 3" style
        m2 = re.search(r'is\s*([\d\.]+)\s*(greater than|less than|equal to|equals)\s*([\d\.]+)', text, re.I)
        if m2:
            a = float(m2.group(1))
            op = m2.group(2).lower()
            b = float(m2.group(3))
            if 'greater' in op:
                return f"Yes, {a} > {b} is {a > b}."
            if 'less' in op:
                return f"Yes, {a} < {b} is {a < b}."
            if 'equal' in op or 'equals' in op:
                return f"{a} == {b} is {a == b}."
        return None
    a = float(m.group(1))
    op = m.group(2)
    b = float(m.group(3))
    if op in ('==','='):
        ok = (a == b)
    elif op == '>':
        ok = (a > b)
    elif op == '<':
        ok = (a < b)
    elif op == '>=':
        ok = (a >= b)
    elif op == '<=':
        ok = (a <= b)
    else:
        ok = False
    return f"That is {ok}."
