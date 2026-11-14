@echo off
echo.
echo  +===========================================+
echo  ^|  VisualSearch -- Image Search Engine     ^|
echo  +===========================================+
echo.

docker compose up --build -d

echo.
echo  App:   http://localhost:3000
echo  API:   http://localhost:8000
echo  Docs:  http://localhost:8000/api/docs
echo.
echo  To seed sample images:
echo  docker compose exec backend python scripts/seed_images.py
echo.
pause
