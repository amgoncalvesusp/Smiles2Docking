@echo off
setlocal
cd /d "%~dp0\..\.."
set BUILD_ROOT=%LOCALAPPDATA%\SMILES2DockingFULLBuild

C:\Users\adria\miniconda3\Scripts\conda.exe run -n smiles2docking pyinstaller --noconfirm --clean --distpath "%BUILD_ROOT%\dist" --workpath "%BUILD_ROOT%\build" packaging\windows\smiles2docking.spec

echo.
echo Build finished. See %BUILD_ROOT%\dist\SMILES2DockingFULL\
endlocal
