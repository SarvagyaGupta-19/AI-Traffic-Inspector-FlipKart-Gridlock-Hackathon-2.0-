git add backend/models backend/requirements.txt backend/yolov8s.pt backend/config.py backend/utils
git commit -m "feat(ai): integrate YOLOv8 and cascade detection pipeline"
git add backend/logic backend/ocr backend/evidence
git commit -m "feat(logic): add spatial violation rules engine and PaddleOCR"
git add backend/app backend/run.py backend/Dockerfile backend/test_verify.py backend/test_video.mp4
git commit -m "feat(backend): implement FastAPI async server and SQLite storage"
git add frontend/package.json frontend/next.config.ts frontend/tsconfig.json frontend/eslint.config.mjs frontend/postcss.config.mjs
git commit -m "chore(ui): initialize Next.js dashboard framework"
git add frontend
git commit -m "feat(ui): build cinematic traffic dashboard pages and SSE feed"
git add .
git commit -m "docs: add hackathon solution framework and project overview"
