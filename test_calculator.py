import math

import pytest

from calculator_core import apply_function, evaluate_expression, format_display, format_result


@pytest.mark.parametrize(
    ("expression", "expected"),
    [("2 + 3 * 4", 14), ("(8 - 3) / 2", 2.5), ("2 ** 3", 8), ("-4 + 10", 6)],
)
def test_evaluate_expression(expression, expected):
    assert evaluate_expression(expression) == expected


def test_format_result_avoids_unhelpful_float_noise():
    assert format_result(0.1 + 0.2) == "0.3"


@pytest.mark.parametrize("value", [math.pi, -math.pi, 1 / 3, -1 / 3, 1.234567890123456e100, -1.234567890123456e-100, 1e308, 5e-324, 0])
def test_display_numbers_fit_thirteen_characters(value):
    text = format_display(value)
    assert len(text) <= 13
    assert float(text) == pytest.approx(value)


def test_display_precision_and_copyable_history(monkeypatch):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    from PyQt6.QtWidgets import QApplication

    from calculator import CalculatorWindow

    app = QApplication.instance() or QApplication([])
    window = CalculatorWindow()
    try:
        assert window.history_panel.isHidden()
        for key in ["1", "/", "3"]:
            window.buttons[key].click()
        assert window.history_panel.isHidden()
        window.buttons["="].click()
        assert not window.history_panel.isHidden()
        assert window.answer == 1 / 3
        assert window.expression == repr(1 / 3)
        for key in ["X", "3", "="]:
            window.buttons[key].click()
            assert len(window.display.text()) <= 13
        assert window.answer == 1
        assert window.display.text() == "1"
        transcript = window.history_text.toPlainText()
        assert len(transcript.splitlines()) == 2
        assert "1/3" in transcript
        assert repr(1 / 3) in transcript
        assert repr(1.0) in transcript
        assert window.history_text.isReadOnly()
        window.history_text.selectAll()
        window.history_text.copy()
        assert app.clipboard().text() == transcript
        window.history_toggle.click()
        window.buttons[">"].click()
        assert not window.history_panel.isHidden()
        assert window.history_text.toPlainText() == transcript
    finally:
        window.close()


@pytest.mark.parametrize(
    ("keys", "expected_answer"),
    [
        (list("12345678901234567890"), 0),
        (list("1234567890123+9876543210987") + ["="], 11111111101110),
        (["SHIFT", "EXP", "+/-", "="], -math.pi),
        (["1", "/", "3", "=", "ENG", "X", "3", "="], 1),
        (["1", "/", "3", "=", "M+", "AC", "0", "MR", "X", "3", "="], 1),
        (["1", "/", "3", "=", "1/X"], 3),
        (["1", "EXP", "1", "0", "0", "=", "1/X"], 1e-100),
        (["5", "SHIFT", "1/X"], 120),
    ],
)
def test_display_limit_for_every_input_and_result(monkeypatch, keys, expected_answer):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    from PyQt6.QtWidgets import QApplication

    from calculator import CalculatorWindow

    app = QApplication.instance() or QApplication([])
    window = CalculatorWindow()
    try:
        for key in keys:
            window.buttons[key].click()
            assert len(window.display.text()) <= 13
        assert window.answer == expected_answer
        if keys == ["5", "SHIFT", "1/X"]:
            assert not window.history_panel.isHidden()
        app.processEvents()
    finally:
        window.close()


@pytest.mark.parametrize("confirm_pi", [False, True])
@pytest.mark.parametrize("operator, symbol, expected", [("X", "*", math.pi * 7), ("+", "+", math.pi + 7), ("X^Y", "**", math.pi ** 7)])
def test_pi_continuation_shows_only_pending_input(monkeypatch, confirm_pi, operator, symbol, expected):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    from PyQt6.QtWidgets import QApplication

    from calculator import CalculatorWindow

    app = QApplication.instance() or QApplication([])
    window = CalculatorWindow()
    try:
        for key in ["SHIFT", "EXP"]:
            window.buttons[key].click()
        if confirm_pi:
            window.buttons["="].click()
        window.buttons[operator].click()
        assert window.display.text() == symbol
        window.buttons["7"].click()
        assert window.display.text() == "7"
        assert window.expression == f"{math.pi}{symbol}7"
        assert len(window.history_text.toPlainText().splitlines()) == int(confirm_pi)
        window._press("DEL")
        assert window.display.text() == symbol
        window._press("DEL")
        if operator == "X^Y":
            window._press("DEL")
        assert window.display.text() == format_display(math.pi)
        for key in [operator, "7", "="]:
            window.buttons[key].click()
        assert window.answer == expected
        assert window.display.text() == format_display(expected)
        assert f"{math.pi}{symbol}7 = {repr(expected)}" in window.history_text.toPlainText()
        window.buttons["AC"].click()
        window.buttons["7"].click()
        assert window.display.text() == "7"
        app.processEvents()
    finally:
        window.close()


def test_display_current_operand_and_calculation_only_history(monkeypatch):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    from PyQt6.QtWidgets import QApplication

    from calculator import CalculatorWindow

    app = QApplication.instance() or QApplication([])
    window = CalculatorWindow()
    try:
        for key, expected in [("2", "2"), ("2", "22"), ("X", "*"), ("5", "5"), ("5", "55")]:
            window.buttons[key].click()
            assert window.display.text() == expected
            assert window.history_text.toPlainText() == ""
        window.buttons["="].click()
        assert window.display.text() == "1210"
        assert window.history_text.toPlainText() == "22*55 = 1210.0"
        for key, expected in [("+", "+"), ("2", "2"), ("X", "*"), ("3", "3")]:
            window.buttons[key].click()
            assert window.display.text() == expected
            assert len(window.history_text.toPlainText().splitlines()) == 1
        window.buttons["="].click()
        assert window.answer == 1216
        assert len(window.history_text.toPlainText().splitlines()) == 2
        window.buttons["WURZEL"].click()
        assert len(window.history_text.toPlainText().splitlines()) == 3
        assert "sqrt(1216.0)" in window.history_text.toPlainText()
        transcript = window.history_text.toPlainText()
        for key in ["SHIFT", "SHIFT", "MODE", "ENG", "AC", ">"]:
            window.buttons[key].click()
        assert window.history_text.toPlainText() == transcript
        app.processEvents()
    finally:
        window.close()


def test_history_panel_can_collapse_and_expand_without_losing_state(monkeypatch):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    from PyQt6.QtWidgets import QApplication

    from calculator import CalculatorWindow

    app = QApplication.instance() or QApplication([])
    window = CalculatorWindow()
    try:
        window.show()
        app.processEvents()
        surface_size = window.calculator_surface.size()
        display_geometry = window.display.geometry()
        collapsed_width = window.width()
        assert window.history_panel.isHidden()
        for key in ["1", "="]:
            window.buttons[key].click()
        for _ in range(3):
            app.processEvents()
            assert window.history_panel.isVisible()
            assert not window.history_panel.isWindow()
            assert window.history_panel.x() == window.calculator_surface.width() + 24
            assert window.calculator_surface.size() == surface_size
            assert window.display.geometry() == display_geometry
            assert window.width() == collapsed_width + 360
            transcript = window.history_text.toPlainText()
            window.history_toggle.click()
            app.processEvents()
            assert window.history_panel.isHidden()
            assert window.history_toggle.isVisible()
            assert window.width() == collapsed_width
            assert window.calculator_surface.size() == surface_size
            for key in ["+", "2", "="]:
                window.buttons[key].click()
            assert window.history_panel.isHidden()
            assert window.history_text.toPlainText().startswith(transcript)
            answer = window.answer
            expression = window.expression
            window.history_toggle.click()
            assert window.answer == answer
            assert window.expression == expression
        window.move(70, 80)
        window.resize(1000, 900)
        app.processEvents()
        assert window.history_panel.x() == window.calculator_surface.width() + 24
        assert window.history_panel.height() == window.calculator_surface.height()
        assert window.calculator_surface.size() == surface_size
        assert window.height() == 750
        assert window.history_panel.width() == 566
        window.history_toggle.click()
        window.buttons[">"].click()
        app.processEvents()
        assert not window.history_panel.isHidden()
        assert window.width() == 1000
        assert window.history_panel.width() == 566
    finally:
        window.close()


def test_scientific_functions_support_degrees_and_shift_variants():
    assert format_result(apply_function("sin", 90)) == "1"
    assert format_result(apply_function("asin", 1)) == "90"
    assert format_result(apply_function("sqrt", 81)) == "9"


def test_combinatorial_functions_support_permutations_and_combinations():
    from calculator_core import combinatorial

    assert combinatorial("nPr", 5, 2) == 20
    assert combinatorial("nCr", 5, 2) == 10


@pytest.mark.parametrize("expression", ["", "1 / 0", "__import__('os').system('whoami')", "2 ** 10000"])
def test_invalid_or_unsafe_expressions_are_rejected(expression):
    with pytest.raises((SyntaxError, ValueError, ZeroDivisionError, OverflowError)):
        evaluate_expression(expression)


@pytest.mark.parametrize(
    ("keys", "expected"),
    [
        (["5", "SHIFT", "1/X"], "120"),
        (["0", "SHIFT", "1/X"], "1"),
        (["-", "1", "SHIFT", "1/X"], "Error"),
        (["1", ".", "5", "SHIFT", "1/X"], "Error"),
        (["1", "+", "SHIFT", "1/X"], "Error"),
        (["SHIFT", "EXP", "="], format_result(math.pi)),
        (["2", "X", "SHIFT", "EXP", "="], format_result(2 * math.pi)),
        (["2", "=", "SHIFT", "EXP", "="], format_result(math.pi)),
        (["1", "SHIFT", "sin"], "90"),
        (["MODE", "1", "SHIFT", "sin"], format_result(math.pi / 2)),
        (["2", "SHIFT", "sin"], "Error"),
        (["4", "1/X"], "0.25"),
        (["2", "EXP", "3", "="], "2000"),
        (["9", "0", "sin"], "1"),
        (["5", "SHIFT", "SHIFT", "1/X"], "0.2"),
        (["5", "SHIFT", "1/X", "1/X"], format_display(1 / 120)),
    ],
)
def test_shift_key_bindings(monkeypatch, keys, expected):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    from PyQt6.QtWidgets import QApplication

    from calculator import CalculatorWindow

    app = QApplication.instance() or QApplication([])
    window = CalculatorWindow()
    try:
        for key in keys:
            window.buttons[key].click()
        app.processEvents()
        assert window.display.text() == expected
        assert not window.shift
        assert window.buttons["SHIFT"].property("role") == "action"
        assert "SHIFT OFF" in window.status.text()
    finally:
        window.close()


@pytest.mark.parametrize("size", [(816, 1494), (410, 750), (1000, 1800)])
@pytest.mark.parametrize("expanded", [False, True])
def test_resize_only_changes_history_width(monkeypatch, size, expanded):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    from PyQt6.QtCore import QRect
    from PyQt6.QtWidgets import QApplication

    from calculator import CalculatorWindow

    app = QApplication.instance() or QApplication([])
    window = CalculatorWindow()
    try:
        window.show()
        if expanded:
            window.history_toggle.click()
        app.processEvents()
        button_geometry = {key: button.geometry() for key, button in window.buttons.items()}
        window.resize(*size)
        app.processEvents()
        assert window.height() == 750
        assert window.calculator_surface.width() == 410
        assert window.calculator_surface.height() == 750
        assert window.background.geometry() == QRect(0, 0, 410, 750)
        if expanded:
            assert window.width() == max(size[0], 674)
            assert window.history_panel.width() == window.width() - 434
            assert window.history_panel.height() == 750
        else:
            assert window.width() == 434
            assert window.history_panel.isHidden()
        scale_x = 410 / 816
        scale_y = 750 / 1494
        assert window.display.geometry() == QRect(
            round(99 * scale_x), round(100 * scale_y),
            round(650 * scale_x), round(128 * scale_y),
        )
        assert window.status.geometry() == window._scaled_rect(215, 65, 390, 32, scale_x, scale_y)
        assert window.notice.geometry() == window._scaled_rect(130, 320, 556, 54, scale_x, scale_y)
        assert {key: button.geometry() for key, button in window.buttons.items()} == button_geometry
    finally:
        window.close()