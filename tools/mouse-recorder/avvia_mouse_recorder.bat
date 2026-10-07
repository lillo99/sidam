@echo off
rem Avvia il Mouse Recorder con AutoHotkey v2 portable (stessa cartella).
if not exist "%~dp0AutoHotkey64.exe" (
    echo AutoHotkey64.exe non trovato in questa cartella.
    echo Scarica la versione Portable .ZIP di AutoHotkey v2 da
    echo https://www.autohotkey.com/download e copia qui AutoHotkey64.exe
    pause
    exit /b 1
)
start "" "%~dp0AutoHotkey64.exe" "%~dp0mouse_recorder.ahk"
