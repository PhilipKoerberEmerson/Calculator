"""PyQt6 calculator with the scientific keyboard of the CASIO fx-85v."""

from __future__ import annotations

import sys
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QFontDatabase, QPixmap
from PyQt6.QtWidgets import QApplication, QLabel, QMainWindow, QPushButton, QWidget

from calculator_core import apply_function, evaluate_expression, format_result


ERROR_TEXT = "Error"


def resource_path(relative_path: str) -> str:
    """Resolve resources both from source and from a PyInstaller bundle."""
    bundle_root = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
    return str(bundle_root / relative_path)


class CalculatorWindow(QMainWindow):
    """Calculator window with SHIFT, angle mode, memory and history."""

    def __init__(self) -> None:
        super().__init__()
        self.expression = ""
        self.answer = 0.0
        self.memory = 0.0
        self.angle_mode = "DEG"
        self.shift = False
        self.just_calculated = False
        self.history: list[str] = []
        self.history_index = -1
        self.display_font_family = "Consolas"
        font_id = QFontDatabase.addApplicationFont(resource_path("fonts/DSEG7Classic-Regular.ttf"))
        if font_id >= 0:
            font_families = QFontDatabase.applicationFontFamilies(font_id)
            if font_families:
                self.display_font_family = font_families[0]
        self.setWindowTitle("Philip's CASIO fx-85v")
        self.setMinimumSize(410, 750)
        self.setStyleSheet(
            """
            QMainWindow { background: #202522; }
            QPushButton { background: transparent; color: transparent; border: 1px solid transparent;
                border-radius: 8px; }
            QPushButton:hover { background: rgba(126, 157, 131, 70); border: 2px solid rgba(126, 157, 131, 210);
                color: #17241f; font-size: 17px; font-weight: 700; }
            QPushButton:pressed { background: rgba(126, 157, 131, 120); color: #17241f; font-size: 17px; font-weight: 700; }
            QPushButton[role="active"] { background: rgba(126, 157, 131, 125); border: 2px solid #d5e0d0; }
            QLabel#display { background: rgba(184, 201, 174, 220); color: #17241f; border: 2px solid #63766b;
                border-radius: 5px; padding: 8px 12px; font-size: 26px; }
            QLabel#status { background: rgba(232, 224, 208, 180); color: #31443d; padding: 2px 7px;
                border-radius: 3px; font-size: 11px; font-weight: 700; }
            QLabel#notice { background: rgba(49, 68, 61, 230); color: #fffaf0; padding: 8px 12px;
                border-radius: 4px; font-size: 12px; }
            """
        )
        self._build_ui()

    def _build_ui(self) -> None:
        root = QWidget()
        self.background = QLabel(root)
        self.background.setPixmap(QPixmap(resource_path("pictures/CASIO_fx-85v.jpg")))
        self.background.setScaledContents(True)
        self.background.lower()

        self.status = QLabel("DEG  |  SHIFT OFF  |  M: 0", root)
        self.status.setObjectName("status")
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.display = QLabel("0", root)
        self.display.setObjectName("display")
        self.display.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.display.setFont(QFont(self.display_font_family, 27))
        self.notice = QLabel("Diese Funktion geht noch nicht", root)
        self.notice.setObjectName("notice")
        self.notice.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.notice.hide()

        upper_rows = [
            [("SHIFT", "action"), ("Kin", "function"), ("Kout", "function"), ("ENG", "function"), ("ENG<-", "function"), ("MODE", "function")],
            [("1/X", "function"), ("WURZEL", "function"), ("X^2", "function"), ("log", "function"), ("ln", "function"), ("X^Y", "operator")],
            [("AB/C", "function"), ("O'\"", "function"), ("hyp", "function"), ("sin", "function"), ("cos", "function"), ("tan", "function")],
            [("+/-", "operator"), (">", "function"), ("[(--", "operator"), ("--)]", "operator"), ("Min", "function"), ("MR", "function")],
        ]
        lower_rows = [
            [("7", "number"), ("8", "number"), ("9", "number"), ("C", "danger"), ("AC", "danger")],
            [("4", "number"), ("5", "number"), ("6", "number"), ("X", "operator"), ("/", "operator")],
            [("1", "number"), ("2", "number"), ("3", "number"), ("+", "operator"), ("-", "operator")],
            [("0", "number"), (".", "number"), ("EXP", "function"), ("=", "action"), ("M+", "function")],
        ]
        self.buttons: dict[str, QPushButton] = {}
        for row_keys in upper_rows + lower_rows:
            for column, (key, role) in enumerate(row_keys):
                button = QPushButton(key, root)
                button.setProperty("role", role)
                button.setToolTip(f"Symbol: {key}")
                button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
                button.clicked.connect(lambda _checked=False, value=key: self._press(value))
                self.buttons[key] = button
        self.setCentralWidget(root)
        self._position_overlay()

    def resizeEvent(self, event) -> None:  # noqa: N802 - Qt API name
        super().resizeEvent(event)
        self._position_overlay()

    def _position_overlay(self) -> None:
        if not hasattr(self, "background"):
            return
        width, height = self.centralWidget().size().width(), self.centralWidget().size().height()
        self.background.setGeometry(0, 0, width, height)
        scale_x, scale_y = width / 816, height / 1494
        self.display.setGeometry(self._scaled_rect(100, 100, 600, 128, scale_x, scale_y))
        self.status.setGeometry(self._scaled_rect(215, 65, 390, 32, scale_x, scale_y))
        self.notice.setGeometry(self._scaled_rect(130, 320, 556, 54, scale_x, scale_y))

        self._position_key_matrix(list(self.buttons.values())[:24], 6, 60, 560, 90, 70, 32, scale_x, scale_y)
        self._position_key_matrix(list(self.buttons.values())[24:], 5, 60, 985, 115, 88, 30, scale_x, scale_y)

    def _position_key_matrix(self, buttons, columns, start_x, start_y, key_width, key_height, gap, scale_x, scale_y):
        for index, button in enumerate(buttons):
            row, column = divmod(index, columns)
            button.setGeometry(self._scaled_rect(
                start_x + column * (key_width + gap),
                start_y + row * (key_height + gap),
                key_width,
                key_height,
                scale_x,
                scale_y,
            ))

    @staticmethod
    def _scaled_rect(x, y, width, height, scale_x, scale_y):
        from PyQt6.QtCore import QRect

        return QRect(round(x * scale_x), round(y * scale_y), round(width * scale_x), round(height * scale_y))

    def _press(self, key: str) -> None:
        if key == "SHIFT":
            self.shift = not self.shift
            self.buttons[key].setProperty("role", "active" if self.shift else "action")
            self.buttons[key].style().unpolish(self.buttons[key])
            self.buttons[key].style().polish(self.buttons[key])
            self._refresh_status()
            return
        if key in {"Kin", "Kout", "ENG<-", "AB/C", "O'\"", "hyp"}:
            self._show_message(f"{key}: Diese Funktion geht noch nicht")
            self.shift = False
            self._refresh_status()
            return
        elif key == "MODE":
            self.angle_mode = "RAD" if self.angle_mode == "DEG" else "DEG"
        elif key in {"ON", "AC", "C"}:
            self.expression = ""
            self.shift = False
            if key == "ON":
                self.memory = 0.0
        elif key == "DEL":
            self.expression = self.expression[:-1]
        elif key == "=":
            self._calculate()
            return
        elif key == ">":
            self._navigate_history(1)
            return
        elif key in {"sin", "cos", "tan", "WURZEL", "log", "ln", "1/X", "X^2"}:
            self._apply_scientific(key)
            return
        elif key in {"Min", "MR", "M+"}:
            self._memory_action(key)
            return
        elif key == "Ans":
            self.expression += format_result(self.answer)
        elif key == "EXP":
            self.expression += "*10**"
        elif key == "ENG":
            self._engineering_format()
            return
        elif key == "+/-":
            self.expression = f"-({self.expression})" if self.expression else "-"
        elif key == "[(--":
            self.expression += "("
        elif key == "--)]":
            self.expression += ")"
        else:
            if self.just_calculated and key not in "+-*/%)":
                self.expression = ""
            self.expression += "*" if key == "X" else ("**" if key == "X^Y" else key)
            self.just_calculated = False
        self.shift = False
        self._refresh_status()
        self._refresh_display()

    def _calculate(self) -> None:
        try:
            self.answer = evaluate_expression(self.expression)
            self.expression = format_result(self.answer)
            self.history.append(self.expression)
            self.history_index = len(self.history)
        except (SyntaxError, ValueError, TypeError, ZeroDivisionError, OverflowError):
            self.expression = ERROR_TEXT
        self.just_calculated = True
        self.shift = False
        self._refresh_status()
        self._refresh_display()

    def _apply_scientific(self, key: str) -> None:
        try:
            value = evaluate_expression(self.expression)
            function_map = {
                "WURZEL": "sqrt", "X^2": "square", "1/X": "reciprocal",
                "sin": "asin" if self.shift else "sin",
                "cos": "acos" if self.shift else "cos", "tan": "atan" if self.shift else "tan",
                "log": "10^x" if self.shift else "log", "ln": "e^x" if self.shift else "ln",
            }
            self.answer = apply_function(function_map[key], value, self.angle_mode)
            self.expression = format_result(self.answer)
        except (ValueError, TypeError, OverflowError, ZeroDivisionError):
            self.expression = ERROR_TEXT
        self.just_calculated = True
        self.shift = False
        self._refresh_status()
        self._refresh_display()

    def _memory_action(self, key: str) -> None:
        try:
            value = evaluate_expression(self.expression)
            if key == "M+":
                self.memory += value
            elif key == "Min":
                self.memory -= value
            elif key == "MR":
                self.expression = format_result(self.memory)
        except (SyntaxError, ValueError, TypeError, ZeroDivisionError):
            self.expression = ERROR_TEXT
        self._refresh_status()
        self._refresh_display()

    def _engineering_format(self) -> None:
        try:
            value = evaluate_expression(self.expression)
            self.expression = f"{value:.3e}"
        except (SyntaxError, ValueError, TypeError, ZeroDivisionError):
            self.expression = ERROR_TEXT
        self._refresh_display()

    def _navigate_history(self, step: int) -> None:
        if self.history:
            self.history_index = max(0, min(len(self.history) - 1, self.history_index + step))
            self.expression = self.history[self.history_index]
            self._refresh_display()

    def _show_message(self, message: str) -> None:
        self.notice.setText(message)
        self.notice.show()
        self.display.setText("-")

    def _refresh_display(self) -> None:
        self.notice.hide()
        self.display.setText(self.expression or "0")

    def _refresh_status(self) -> None:
        self.status.setText(f"{self.angle_mode}  |  SHIFT {'ON' if self.shift else 'OFF'}  |  M: {format_result(self.memory)}")

    def keyPressEvent(self, event) -> None:  # noqa: N802 - Qt API name
        key = event.key()
        text = event.text()
        shortcuts = {Qt.Key.Key_Return: "=", Qt.Key.Key_Enter: "=", Qt.Key.Key_Backspace: "DEL", Qt.Key.Key_Escape: "AC"}
        if key in shortcuts:
            self._press(shortcuts[key])
        elif text in "0123456789.+-*/()%":
            self._press(text)
        else:
            super().keyPressEvent(event)


def main() -> int:
    app = QApplication(sys.argv)
    window = CalculatorWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
