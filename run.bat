@echo off
title NewsPulse & FactVerify Dashboard
echo ========================================================
echo    NewsPulse & FactVerify - News Scraper Dashboard
echo ========================================================
echo Membuka server di http://127.0.0.1:7000 ...
echo Tekan CTRL+C untuk menghentikan server.
echo.
python -m uvicorn app:app --host 127.0.0.1 --port 7000 --reload
pause
