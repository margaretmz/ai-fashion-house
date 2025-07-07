lsof -ti :8000 | xargs -r kill -9 && ai-fashion-house start --workers 1
