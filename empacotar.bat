@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

echo ================================
echo EMPACOTANDO CONTROLE FINANCEIRO
echo ================================

REM Verifica Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python não encontrado!
    pause & exit /b
)

REM Verifica PyInstaller
where pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Instalando PyInstaller...
    pip install pyinstaller || (echo [ERRO] Falha; pause & exit /b)
)

REM Verifica dependências
python -c "import tkinter, PIL, ttkbootstrap" 2>nul || (
    echo [ERRO] Dependencias faltando!
    echo Execute: pip install pillow ttkbootstrap
    pause & exit /b
)

REM Limpa builds antigos
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM Backup do executável anterior
if exist "dist\Controle Financeiro\Controle Financeiro.exe" (
    echo Criando backup...
    if not exist backup mkdir backup
    copy "dist\Controle Financeiro\Controle Financeiro.exe" "backup\Controle_Backup_%date:~-10,2%-%date:~-7,2%-%date:~-4,4%.exe"
)

REM Empacota usando o .spec
echo Empacotando...
pyinstaller --clean Controle_Financeiro.spec

REM Verifica se funcionou
if exist "dist\Controle Financeiro\Controle Financeiro.exe" (
    echo.
    echo ✅ Empacotado com sucesso!
) else (
    echo ❌ Falha no empacotamento!
)

pause
