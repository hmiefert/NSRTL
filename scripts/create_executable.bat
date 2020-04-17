pyinstaller -i "res\newman-icon.ico" -n "NSRTL" --clean --hidden-import="PyQt5.QtNetwork" --onefile --noconsole main.py
