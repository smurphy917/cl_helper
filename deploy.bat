set "PYU_AWS_ID=AKIAIHVLDAEIBMV5WIQQ"
set "PYU_AWS_SECRET=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"
@echo off
set /p version="Enter version:"
set CWD=%CD%
cd %~dp0
pyupdater build -F --app-version=%version% win32.pyu.spec
pyupdater pkg --process --sign
pyupdater upload --service s3
cd %CWD%
echo "Deployment complete"