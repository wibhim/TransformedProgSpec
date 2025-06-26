@echo off
echo ===================================================
echo Collect 20 Representative Programs from Each Repository
echo ===================================================
echo.

python collect_code.py --target 200 --max-per-repo 20 --min-lines 15

echo.
echo Collection process complete!
pause
