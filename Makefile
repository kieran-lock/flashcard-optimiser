CHROME_PATH := "/home/kieran/.cache/ms-playwright/chromium-1194/chrome-linux/chrome"
VENV_PATH := "/home/kieran/workspace/kieran/flashcard-atomiser/.venv/bin/python"
ENTRYPOINT_PATH := "/home/kieran/workspace/kieran/flashcard-atomiser/main.py"
CLEANUP_ENTRYPOINT_PATH := "/home/kieran/workspace/kieran/flashcard-atomiser/cleanup.py"
BROWSER_PROFILE_PATH := "/tmp/chrome-debug-profile"
PORT := 9222

browser:
	$(CHROME_PATH) --remote-debugging-port=$(PORT) --user-data-dir=$(BROWSER_PROFILE_PATH)
flashcards:
	$(VENV_PATH) $(ENTRYPOINT_PATH)
cleanup:
	$(VENV_PATH) $(CLEANUP_ENTRYPOINT_PATH)
