@echo off
REM Create an executable
pushd
cd "%~dp0.."
IF "%VIRTUAL_ENV%"=="" (set pshell=poetry run) else (set pshell=)

REM Generate .ui files to .py files
%pshell% python build-ui.py

copy /y Assets\PathOfBuilding_v2.png Assets\PathOfBuilding.png
REM --disable-console
%pshell% pyinstaller --clean --noconfirm --onefile src/PathOfBuilding.py --add-data src/data;data --icon Assets/Icons/PathOfBuilding.ico -p src/dialogs -p src/PoB -p src/ui -p src/widgets -p src/windows
dir dist\PathOfBuilding.exe
copy /y dist\PathOfBuilding.exe c:\_complete\_new  
rmdir /q /s PathOfBuilding.dist PathOfBuilding.build >nul 2>&1

popd
pause
