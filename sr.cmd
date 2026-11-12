@echo off
rem Windows entry point for the contributor helper: `.\sr.cmd go` (cmd or PowerShell).
rem Finds Python 3.11+ or, when there is none, unpacks a private copy under .local\python, then runs
rem tools\contrib.py with the arguments given. It needs no administrator rights and changes nothing
rem outside this checkout: the private copy is the python.org NuGet package (a zip, no installer,
rem no registry entries), checked against a pinned SHA-256; delete .local\python to remove it.
rem A .cmd file is not subject to PowerShell's execution policy, so no policy change is needed.
rem Labels and gotos instead of parenthesized blocks: a checkout path containing ")" would end a
rem block early.
setlocal EnableExtensions
set "SR_ROOT=%~dp0"
set "SR_PRIVATE=%SR_ROOT%.local\python"
set "SR_PY=%SR_PRIVATE%\tools\python.exe"
set "SR_PYARGS="
set "SR_PKG_URL=https://www.nuget.org/api/v2/package/python/3.12.10"
set "SR_PKG_SHA256=0eb85c2dfccccf1b17352de4c397f69194035b7d37149eacc16f1147d93de3b8"
set "SR_PKG=%SR_ROOT%.local\downloads\python.3.12.10.nupkg"
rem Messages from contrib.py name this script as the command to run next.
set "SR_LAUNCHER=.\sr.cmd"
rem The tools read third-party text (community headers, compiler output); UTF-8 mode keeps that
rem independent of the console code page.
set "PYTHONUTF8=1"

if exist "%SR_PY%" goto run
rem An installed Python: the py launcher first, then python. The Microsoft Store alias fails this
rem probe without opening the Store, because it is given arguments.
py -3 -c "import sys; sys.exit(sys.version_info < (3, 11))" >nul 2>&1
if errorlevel 1 goto try_python
set "SR_PY=py"
set "SR_PYARGS=-3"
goto run
:try_python
python -c "import sys; sys.exit(sys.version_info < (3, 11))" >nul 2>&1
if errorlevel 1 goto fetch
set "SR_PY=python"
goto run

:fetch
echo No Python 3.11 or newer found; unpacking Python 3.12.10 from python.org's NuGet package
echo [about 15 MB download, 40 MB on disk] into "%SR_PRIVATE%"
if not exist "%SR_ROOT%.local\downloads" mkdir "%SR_ROOT%.local\downloads"
call :verify
if not errorlevel 1 goto unpack
rem -C - resumes a partial download after a dropped connection.
curl.exe -fL --retry 5 --retry-delay 5 --connect-timeout 30 -C - -o "%SR_PKG%" "%SR_PKG_URL%"
if not errorlevel 1 goto check
echo Download failed. Run .\sr.cmd again to resume it; if it keeps failing, delete
echo "%SR_PKG%" and retry, or install Python 3.11+ yourself.
exit /b 8
:check
call :verify
if not errorlevel 1 goto unpack
del "%SR_PKG%" >nul 2>&1
echo The downloaded package did not match its pinned SHA-256 and was deleted. Run .\sr.cmd again.
exit /b 1
:unpack
if exist "%SR_PRIVATE%" rmdir /s /q "%SR_PRIVATE%"
mkdir "%SR_PRIVATE%"
tar -xf "%SR_PKG%" -C "%SR_PRIVATE%" tools
if errorlevel 1 goto unpack_failed
if exist "%SR_PY%" goto run
:unpack_failed
echo Unpacking "%SR_PKG%" failed.
exit /b 1

:run
"%SR_PY%" %SR_PYARGS% "%SR_ROOT%tools\contrib.py" %*
exit /b %ERRORLEVEL%

:verify
rem Exit 0 when the package exists and matches the pinned SHA-256.
if not exist "%SR_PKG%" exit /b 1
set "SR_GOT="
for /f "skip=1 delims=" %%H in ('certutil -hashfile "%SR_PKG%" SHA256') do if not defined SR_GOT set "SR_GOT=%%H"
set "SR_GOT=%SR_GOT: =%"
if /i "%SR_GOT%"=="%SR_PKG_SHA256%" exit /b 0
exit /b 1
