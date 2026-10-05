# Calculator
Python Example to learn to work with PyQt6 - GUI emulation of my CASIO fx-85v.

Right-click to use the secondary functions of the keys (as an alternative to the SHIFT key)

## Fractions

- Enter `1`, `a b/c`, `2`, `=` to display `1/2`.
- Enter `2`, `a b/c`, `1`, `a b/c`, `3`, `=` to display the mixed number `2 + 1/3`.
- After a result, press `a b/c` to switch between fraction and decimal display.
- Press `SHIFT` + `a b/c`, or right-click the key, to display an improper fraction, such as `7/3` instead of `2 + 1/3`.

Entered fractions and rational arithmetic retain exact numerators and denominators. Decimal-to-fraction conversion uses a maximum denominator of 1,000,000 and may be approximate. Fractions that exceed the 13-character display are shown as decimals; the internal value is retained.

If you want to build this calculator as a Windows executable, it's best to use the following commands:

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Run tests:

```powershell
python -m pytest -q
```

Build a Windows EXE

```powershell
python -m PyInstaller --clean --noconfirm --noconsole --onefile --name fx-85v --add-data "pictures;pictures" --add-data "fonts;fonts" calculator.py
```

The finished file will then be located in `dist/fx-85v.exe`.
