@echo off
chcp 65001 >nul
setlocal

echo === FMECA: сборка .exe ===
cd /d "%~dp0"

python --version >nul 2>&1
if errorlevel 1 (
    echo Ошибка: Python не найден в PATH.
    exit /b 1
)

echo Установка зависимостей...
pip install -r requirements.txt -r requirements-build.txt -q
if errorlevel 1 (
    echo Ошибка установки пакетов.
    exit /b 1
)

echo Запуск PyInstaller...
pyinstaller fmeca_app.spec --noconfirm --clean
if errorlevel 1 (
    echo Сборка не удалась.
    exit /b 1
)

echo.
echo Готово:
echo   dist\FMECA_Analysis\FMECA_Analysis.exe
echo.
echo Скопируйте всю папку dist\FMECA_Analysis на целевой ПК.
echo База данных создастся в подпапке data\ рядом с .exe
echo.

endlocal
