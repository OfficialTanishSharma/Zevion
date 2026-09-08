@echo off
title Zevion — AI Desktop Copilot
REM Zevion now launches through a clean GUI (launcher.pyw) — no terminal.
REM This .bat simply hands off to the GUI launcher silently.
start "" pythonw "%~dp0launcher.pyw"
exit
