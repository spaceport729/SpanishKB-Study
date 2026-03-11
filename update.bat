@echo off
echo ========================================
echo SpanishKB Study - Update Data
echo ========================================

echo.
echo Running export...
"C:\Users\stace\AppData\Local\Programs\Python\Python39\python" "%~dp0build\export_data.py"

echo.
echo Copying to root for GitHub Pages...
copy /Y "%~dp0app\index.html" "%~dp0index.html"
copy /Y "%~dp0app\app.js" "%~dp0app.js"
copy /Y "%~dp0app\styles.css" "%~dp0styles.css"
copy /Y "%~dp0app\data.json" "%~dp0data.json"
copy /Y "%~dp0app\sw.js" "%~dp0sw.js"
copy /Y "%~dp0app\manifest.json" "%~dp0manifest.json"

echo.
echo Done! Files ready for GitHub Pages.
pause
