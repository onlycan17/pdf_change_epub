from __future__ import annotations

from html import escape
import re
from typing import Match

from latex2mathml.converter import convert as latex_to_mathml


_INLINE_OR_DISPLAY_PATTERN = re.compile(
    r"(?P<display_dollar>(?<!\\)\$\$(?P<display_dollar_body>.+?)(?<!\\)\$\$)"
    r"|(?P<display_bracket>\\\[(?P<display_bracket_body>.+?)\\\])"
    r"|(?P<inline_paren>\\\((?P<inline_paren_body>.+?)\\\))"
    r"|(?P<inline_dollar>(?<![\\\$])\$(?P<inline_dollar_body>.+?)(?<!\\)\$)",
    re.DOTALL,
)

_SUPER_MAP = {
    "¹": "1",
    "²": "2",
    "³": "3",
    "⁰": "0",
    "⁴": "4",
    "⁵": "5",
    "⁶": "6",
    "⁷": "7",
    "⁸": "8",
    "⁹": "9",
    "⁺": "+",
    "⁻": "-",
    "⁼": "=",
    "⁽": "(",
    "⁾": ")",
    "ⁿ": "n",
}

_SUB_MAP = {
    "₀": "0",
    "₁": "1",
    "₂": "2",
    "₃": "3",
    "₄": "4",
    "₅": "5",
    "₆": "6",
    "₇": "7",
    "₈": "8",
    "₉": "9",
    "₊": "+",
    "₋": "-",
    "₌": "=",
    "₍": "(",
    "₎": ")",
}

_MATH_OPERATORS = set("=+-*/^_<>±×÷∑∏∫√∞≈≠≤≥")
_MATH_GREEK = set("αβγδεζηθικλμνξοπρστυφχψωΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩπΠ")


def _normalize_unicode_scripts(expr: str) -> str:
    out: list[str] = []
    i = 0
    while i < len(expr):
        char = expr[i]
        if char in _SUPER_MAP:
            run: list[str] = []
            while i < len(expr) and expr[i] in _SUPER_MAP:
                run.append(_SUPER_MAP[expr[i]])
                i += 1
            out.append("^{" + "".join(run) + "}")
            continue
        if char in _SUB_MAP:
            run = []
            while i < len(expr) and expr[i] in _SUB_MAP:
                run.append(_SUB_MAP[expr[i]])
                i += 1
            out.append("_{" + "".join(run) + "}")
            continue
        out.append(char)
        i += 1
    return "".join(out)


def _looks_like_math_expression(text: str) -> bool:
    stripped = text.strip()
    if not stripped or len(stripped) > 160:
        return False
    if stripped.startswith(("#", "- ", "* ", ">")):
        return False
    if any("가" <= char <= "힣" for char in stripped):
        return False
    if not any(
        char in _MATH_OPERATORS
        or char in _MATH_GREEK
        or char in _SUPER_MAP
        or char in _SUB_MAP
        for char in stripped
    ):
        return False
    allowed = sum(
        1
        for char in stripped
        if char.isalnum()
        or char.isspace()
        or char in _MATH_OPERATORS
        or char in _MATH_GREEK
        or char in _SUPER_MAP
        or char in _SUB_MAP
        or char in r"()[]{}.,:;|\\"
    )
    return allowed / max(1, len(stripped)) >= 0.75


def convert_latex_to_mathml(latex: str, *, display: bool) -> str | None:
    normalized = _normalize_unicode_scripts(latex.strip())
    if not normalized:
        return None
    try:
        mathml = latex_to_mathml(normalized)
    except Exception:
        return None
    wanted_display = "block" if display else "inline"
    return mathml.replace('display="inline"', f'display="{wanted_display}"', 1)


def render_text_with_math(text: str) -> str:
    parts: list[str] = []
    cursor = 0

    for match in _INLINE_OR_DISPLAY_PATTERN.finditer(text):
        start, end = match.span()
        if start > cursor:
            parts.append(escape(text[cursor:start]))
        parts.append(_render_match(match))
        cursor = end

    if cursor < len(text):
        parts.append(escape(text[cursor:]))

    return "".join(parts)


def render_block_with_math(text: str) -> str:
    stripped = text.strip()
    if not stripped:
        return ""

    if stripped.startswith("$$") and stripped.endswith("$$") and len(stripped) > 4:
        mathml = convert_latex_to_mathml(stripped[2:-2], display=True)
        if mathml is not None:
            return f'<div class="math-display">{mathml}</div>'

    if stripped.startswith(r"\[") and stripped.endswith(r"\]") and len(stripped) > 4:
        mathml = convert_latex_to_mathml(stripped[2:-2], display=True)
        if mathml is not None:
            return f'<div class="math-display">{mathml}</div>'

    if _looks_like_math_expression(stripped):
        mathml = convert_latex_to_mathml(stripped, display=True)
        if mathml is not None:
            return f'<div class="math-display">{mathml}</div>'

    return render_text_with_math(text)


def _render_match(match: Match[str]) -> str:
    latex = ""
    if match.group("display_dollar_body") is not None:
        latex = match.group("display_dollar_body")
    elif match.group("display_bracket_body") is not None:
        latex = match.group("display_bracket_body")
    elif match.group("inline_paren_body") is not None:
        latex = match.group("inline_paren_body")
    elif match.group("inline_dollar_body") is not None:
        latex = match.group("inline_dollar_body")

    mathml = convert_latex_to_mathml(latex, display=False)
    if mathml is None:
        return escape(match.group(0))
    return mathml
