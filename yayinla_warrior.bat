@echo off
:: YENİ: CMD ekranini modern UTF-8 formatina gecirerek karakter bozulmalarini onler
chcp 65001 > NUL
setlocal enabledelayedexpansion
title CKRMacro Warrior - Kusursuz Yayinlama Asistani
color 0A

echo ===================================================
echo       CKRMacro Warrior GitHub Surum Firlatici
echo ===================================================
echo.

set /p VERSIYON="Lutfen yeni versiyon numarasini girin (Orn: 1.0): "

echo.
echo [Bilgi] Girilen versiyon: v%VERSIYON%
echo.

echo [1/3] versiyon.txt dosyasi guncelleniyor...
<nul set /p="%VERSIYON%"> versiyon.txt
copy /y versiyon.txt "Yayinla\versiyon.txt" > NUL
echo Basarili!

echo.
echo [2/3] versiyon.txt GitHub 'main' dalina gonderiliyor...
git add versiyon.txt
git commit -m "Warrior Versiyon v%VERSIYON% olarak guncellendi"
git push origin main

echo.
echo [3/3] "Yayinla" ve alt klasorlerindeki DOSYALAR Release olarak yukleniyor...
set "DOSYALAR="
for /r "Yayinla" %%F in (*) do (
    set "DOSYALAR=!DOSYALAR! "%%F""
)

:: YENİ: Başlıktaki 'Sürüm' kelimesi GitHub'da bozulmasın diye 'Surum' yapıldı.
gh release create %VERSIYON% !DOSYALAR! --title "CKRMacro Warrior Surum %VERSIYON%" --notes "Yeni Warrior guncellemesi yayinlandi."

echo.
echo [BASARILI] Her sey kusursuz! Sürüm v%VERSIYON% tamamen yayinlandi!
echo Kullanicilar programi actiginda guncellemeyi aninda gorecekler.
echo.
pause