@echo off
title CKRMacro Warrior - Ana Derleyici
color 0B

echo ===================================================
echo   CKRMacro Warrior Tam Donanimli Derleme Asistani
echo ===================================================
echo.
echo [1/3] Eski kalintilar temizleniyor...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "CKRMacro-Warrior.spec" del /q "CKRMacro-Warrior.spec"
echo Temizlik bitti!
echo.

echo [2/3] PyInstaller ile CKRMacro-Warrior.exe olusturuluyor...
echo Lutfen bekleyin, bu islem 1-2 dakika surebilir...
echo.

:: PyInstaller dogrudan ana dosyayi paketler
pyinstaller --clean --noconfirm --onefile --windowed --uac-admin --icon "anahatar.ico" --add-data "anahatar.ico;." --collect-all customtkinter --collect-all certifi --hidden-import pyautogui --hidden-import mss --hidden-import numpy --hidden-import cv2 --hidden-import PIL --hidden-import pynput --hidden-import requests --hidden-import encodings main_warrior.py --name "CKRMacro-Warrior"

echo.
echo [3/3] EXE "Yayinla" klasorune tasiniyor ve kalintilar siliniyor...
if not exist "Yayinla" mkdir "Yayinla"
move /y "dist\CKRMacro-Warrior.exe" "Yayinla\" > NUL
rmdir /s /q "build"
rmdir /s /q "dist"
del /q "CKRMacro-Warrior.spec"

echo.
echo [BASARILI] Muazzam! Yonetici izinli, tam donanimli EXE hazir!
echo "CKRMacro-Warrior.exe" dosyasi basariyla "Yayinla" klasorune cikarildi.
echo.
pause