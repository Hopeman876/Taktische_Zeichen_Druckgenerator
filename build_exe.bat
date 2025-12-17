@echo off
setlocal enabledelayedexpansion
echo ================================================================================
echo TaktischeZeichenDruckgenerator - Optimierter Build (ohne UPX)
echo ================================================================================
echo.

echo [1/5] Loesche alte Build-Dateien...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo [2/5] Erstelle optimierte .pyc-Dateien...
python -O -m compileall -b . 2>nul

echo [3/5] Starte PyInstaller Build (ohne UPX fuer bessere Performance)...
pyinstaller TaktischeZeichenDruckgenerator.spec

echo [4/5] Kopiere zusaetzliche Dateien...
if not exist "dist\TaktischeZeichenDruckgenerator\Taktische_Zeichen_Grafikvorlagen" mkdir "dist\TaktischeZeichenDruckgenerator\Taktische_Zeichen_Grafikvorlagen"
copy /Y "README_BETA.md" "dist\TaktischeZeichenDruckgenerator\" 2>nul

echo [4b/5] Ermittle Version und kopiere passende Release Notes...
for /f "delims=" %%v in ('python -c "import constants; print(constants.PROGRAM_VERSION)"') do set VERSION=%%v
if exist "release_notes\RELEASE_NOTES_v%VERSION%.md" (
    copy /Y "release_notes\RELEASE_NOTES_v%VERSION%.md" "dist\TaktischeZeichenDruckgenerator\RELEASE_NOTES_v%VERSION%.md" >nul
    echo Release Notes kopiert: RELEASE_NOTES_v%VERSION%.md
) else (
    echo WARNUNG: Keine Release Notes gefunden fuer Version %VERSION%
)

echo [4b2/5] Kopiere PDF-Release-Notes falls vorhanden...
if exist "release_notes\RELEASE_NOTES_v%VERSION%.pdf" (
    copy /Y "release_notes\RELEASE_NOTES_v%VERSION%.pdf" "dist\TaktischeZeichenDruckgenerator\RELEASE_NOTES_v%VERSION%.pdf" >nul
    echo Release Notes PDF kopiert: RELEASE_NOTES_v%VERSION%.pdf
) else (
    echo INFO: Keine PDF-Release-Notes gefunden
)

echo [4b3/5] Kopiere Benutzerhandbuch...
if not exist "dist\TaktischeZeichenDruckgenerator\User-documentation" mkdir "dist\TaktischeZeichenDruckgenerator\User-documentation"
if exist "User-documentation\BENUTZERHANDBUCH.pdf" (
    copy /Y "User-documentation\BENUTZERHANDBUCH.pdf" "dist\TaktischeZeichenDruckgenerator\User-documentation\BENUTZERHANDBUCH.pdf" >nul
    echo Benutzerhandbuch PDF kopiert
) else (
    echo INFO: Benutzerhandbuch PDF nicht gefunden
)
if exist "BENUTZERHANDBUCH.md" (
    copy /Y "BENUTZERHANDBUCH.md" "dist\TaktischeZeichenDruckgenerator\BENUTZERHANDBUCH.md" >nul
    echo Benutzerhandbuch Markdown kopiert
) else (
    echo WARNUNG: BENUTZERHANDBUCH.md nicht gefunden
)

echo [4c/5] Verschiebe ImageMagick von _internal nach ROOT...
if exist "dist\TaktischeZeichenDruckgenerator\_internal\imagemagick" (
    move "dist\TaktischeZeichenDruckgenerator\_internal\imagemagick" "dist\TaktischeZeichenDruckgenerator\imagemagick" >nul
    echo ImageMagick verschoben: _internal\imagemagick =^> imagemagick\
) else (
    echo WARNUNG: ImageMagick nicht gefunden in _internal!
)

echo [4d/5] Verschiebe Resources von _internal nach ROOT...
if exist "dist\TaktischeZeichenDruckgenerator\_internal\resources" (
    move "dist\TaktischeZeichenDruckgenerator\_internal\resources" "dist\TaktischeZeichenDruckgenerator\resources" >nul
    echo Resources verschoben: _internal\resources =^> resources\
) else (
    echo WARNUNG: Resources nicht gefunden in _internal!
)

echo [5/5] Bereinige .pyc-Dateien...
del /s /q *.pyc 2>nul

echo.
echo ================================================================================
echo [6/8] Erstelle Release-Ordner (ohne Version fuer einfaches Update)...
echo ================================================================================
set RELEASE_DIR=releases\TaktischeZeichenDruckgenerator

if exist "%RELEASE_DIR%" (
    echo Loesche alten Release-Ordner: %RELEASE_DIR%
    rmdir /s /q "%RELEASE_DIR%"
)

echo Erstelle Release-Ordner: %RELEASE_DIR%
if not exist "releases" mkdir "releases"
xcopy /E /I /Y "dist\TaktischeZeichenDruckgenerator" "%RELEASE_DIR%" >nul
echo Release-Ordner erstellt!

echo.
echo ================================================================================
echo [7/8] Konvertiere Markdown-Dateien zu PDF...
echo ================================================================================
echo Installiere Markdown-zu-PDF Dependencies (falls noch nicht vorhanden)...
pip install -q markdown weasyprint 2>nul

if exist "%RELEASE_DIR%\README_BETA.md" (
    echo Konvertiere README_BETA.md zu PDF...
    python dev-tools\markdown_to_pdf.py "%RELEASE_DIR%\README_BETA.md"
)

if exist "%RELEASE_DIR%\RELEASE_NOTES_v%VERSION%.md" (
    echo Konvertiere RELEASE_NOTES_v%VERSION%.md zu PDF...
    python dev-tools\markdown_to_pdf.py "%RELEASE_DIR%\RELEASE_NOTES_v%VERSION%.md"
)

echo Markdown-zu-PDF Konvertierung abgeschlossen

echo.
echo ================================================================================
echo [8/8] Erstelle ZIP-Archiv...
echo ================================================================================
set ZIP_FILE=releases\TaktischeZeichenDruckgenerator_v%VERSION%.zip

if exist "%ZIP_FILE%" (
    echo Loesche altes ZIP: %ZIP_FILE%
    del /q "%ZIP_FILE%"
)

echo Erstelle ZIP-Archiv...
powershell -Command "Compress-Archive -Path '%RELEASE_DIR%' -DestinationPath '%ZIP_FILE%'"

if exist "%ZIP_FILE%" (
    echo ZIP-Archiv erstellt: %ZIP_FILE%
    for %%A in ("%ZIP_FILE%") do (
        set SIZE=%%~zA
        set /a SIZE_MB=%%~zA / 1048576
        echo Groesse: !SIZE_MB! MB
    )
) else (
    echo FEHLER: ZIP-Archiv konnte nicht erstellt werden!
)

echo.
echo ================================================================================
echo Build abgeschlossen! (Optimiert: UPX=False fuer 3-5x schnelleren Start)
echo ================================================================================
echo Version:        %VERSION%
echo Release-Ordner: %RELEASE_DIR% (ohne Versionsnummer fuer einfaches Update)
echo ZIP-Archiv:     %ZIP_FILE% (mit Version fuer Archivierung)
echo Hinweis: Die .exe ist groesser, aber deutlich schneller als mit UPX.
echo ================================================================================
pause
