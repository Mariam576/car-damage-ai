@echo off
rem Development server with live reload on http://localhost:5173 (needs Node.js 18+).
rem Start the backend first (backend\run.bat); /api calls are forwarded to it.
cd /d "%~dp0"
if not exist node_modules call npm install
call npm run dev
