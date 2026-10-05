import pytest

from calculator_core import apply_function, evaluate_expression, format_result


@pytest.mark.parametrize(
    ("expression", "expected"),
    [("2 + 3 * 4", 14), ("(8 - 3) / 2", 2.5), ("2 ** 3", 8), ("-4 + 10", 6)],
)
def test_evaluate_expression(expression, expected):
    assert evaluate_expression(expression) == expected


def test_format_result_avoids_unhelpful_float_noise():
    assert format_result(0.1 + 0.2) == "0.3"


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


@pytest.mark.parametrize("size", [(816, 1494), (410, 750), (1000, 1800)])
def test_display_geometry_scales_on_resize(monkeypatch, size):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    from PyQt6.QtCore import QRect
    from PyQt6.QtWidgets import QApplication

    from calculator import CalculatorWindow

    app = QApplication.instance() or QApplication([])
    window = CalculatorWindow()
    try:
        window.show()
        window.resize(*size)
        app.processEvents()
        scale_x = window.centralWidget().width() / 816
        scale_y = window.centralWidget().height() / 1494
        assert window.display.geometry() == QRect(
            round(120 * scale_x), round(100 * scale_y),
            round(650 * scale_x), round(128 * scale_y),
        )
        assert window.status.geometry() == window._scaled_rect(215, 65, 390, 32, scale_x, scale_y)
        assert window.notice.geometry() == window._scaled_rect(130, 320, 556, 54, scale_x, scale_y)
    finally:
        window.close()