# Calculator
Python Example to learn to work with PyQt6 - GUI emulation of my CASIO fx-85v.

Right-click to use the secondary functions of the keys (as an alternative to the SHIFT key)

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
