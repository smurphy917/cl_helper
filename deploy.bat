@echo off
set /p version=<config\version
FOR /F %%l IN (id.s3) DO
    set%%l
rem set /p version="Enter version:"
set CWD=%CD%
cd %~dp0
@echo on
pyupdater build -F --app-version=%version% win32.pyu.spec
pyupdater pkg --process --sign
pyupdater upload --service s3
cd %CWD%
echo "Deployment complete"