@echo off
set /p version=<config\version
set "PYU_AWS_ID=AKIAIHVLDAEIBMV5WIQQ"
set "PYU_AWS_SECRET=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"
rem set /p version="Enter version:"
set CWD=%CD%
cd %~dp0
@echo on
pyupdater build -F --app-version=%version% win32.pyu.spec
pyupdater pkg --process --sign
pyupdater upload --service s3
cd %CWD%
echo "Deployment complete"