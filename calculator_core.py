"""Pure arithmetic logic for the fx-85v calculator."""

from __future__ import annotations

import ast
import math
import operator
from typing import Callable


MAX_EXPRESSION_LENGTH = 120

_BINARY_OPERATORS: dict[type[ast.operator], Callable[[float, float], float]] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
}
_UNARY_OPERATORS: dict[type[ast.unaryop], Callable[[float], float]] = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def evaluate_expression(expression: str) -> float:
    """Evaluate a basic arithmetic expression without executing arbitrary code."""
    if not expression or len(expression) > MAX_EXPRESSION_LENGTH:
        raise ValueError("invalid expression")

    tree = ast.parse(expression, mode="eval")
    return _evaluate_node(tree.body)


def _evaluate_node(node: ast.AST) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.BinOp) and type(node.op) in _BINARY_OPERATORS:
        left = _evaluate_node(node.left)
        right = _evaluate_node(node.right)
        result = _BINARY_OPERATORS[type(node.op)](left, right)
        if abs(result) == float("inf"):
            raise ValueError("result out of range")
        return result
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPERATORS:
        return _UNARY_OPERATORS[type(node.op)](_evaluate_node(node.operand))
    raise ValueError("unsupported expression")


def format_result(value: float) -> str:
    """Keep the display readable while retaining useful precision."""
    if value == 0:
        return "0"
    return f"{value:.12g}"


def format_display(value: float) -> str:
    for precision in range(12, 0, -1):
        text = f"{value:.{precision}g}"
        if len(text) <= 13:
            return text
    raise ValueError("value does not fit the display")


def apply_function(name: str, value: float, angle_mode: str = "DEG") -> float:
    """Apply one scientific calculator function to a numeric value."""
    value = float(value)
    angle_factor = math.pi / 180 if angle_mode == "DEG" else 1
    if name == "sin":
        result = math.sin(value * angle_factor)
    elif name == "cos":
        result = math.cos(value * angle_factor)
    elif name == "tan":
        result = math.tan(value * angle_factor)
    elif name == "asin":
        result = math.asin(value)
        result = math.degrees(result) if angle_mode == "DEG" else result
    elif name == "acos":
        result = math.acos(value)
        result = math.degrees(result) if angle_mode == "DEG" else result
    elif name == "atan":
        result = math.atan(value)
        result = math.degrees(result) if angle_mode == "DEG" else result
    elif name == "sqrt":
        result = math.sqrt(value)
    elif name == "cbrt":
        result = math.copysign(abs(value) ** (1 / 3), value)
    elif name == "log":
        result = math.log10(value)
    elif name == "ln":
        result = math.log(value)
    elif name == "10^x":
        result = 10**value
    elif name == "e^x":
        result = math.exp(value)
    elif name == "reciprocal":
        result = 1 / value
    elif name == "square":
        result = value**2
    elif name == "cube":
        result = value**3
    elif name == "factorial":
        if value < 0 or not value.is_integer():
            raise ValueError("factorial needs a non-negative integer")
        result = math.factorial(int(value))
    else:
        raise ValueError("unknown function")
    if not math.isfinite(result):
        raise ValueError("result out of range")
    return float(result)


def combinatorial(name: str, left: float, right: float) -> float:
    """Calculate nPr or nCr for non-negative integer operands."""
    left, right = float(left), float(right)
    if not left.is_integer() or not right.is_integer() or left < 0 or right < 0 or right > left:
        raise ValueError("invalid combinatorial operands")
    n, r = int(left), int(right)
    if name == "nPr":
        return float(math.factorial(n) // math.factorial(n - r))
    if name == "nCr":
        return float(math.comb(n, r))
    raise ValueError("unknown combinatorial function")