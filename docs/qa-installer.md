# QA — Installer Test Results

**Date:** 2026-03-20 23:30:23
**Platform:** Darwin arm64 — macOS 26.3.1
**Python:** Python 3.14.3
**Node.js:** v24.13.0
**Ollama:** Warning: could not connect to a running Ollama instance

## Summary

- ✅ **Passed:** 36
- ❌ **Failed:** 0
- ⏭️ **Skipped:** 1

## Test Results

- ✅ install.sh exists
- ✅ install.sh syntax is valid
- ✅ install.sh has proper shebang
- ✅ Python 3.14 found (python3)
- ✅ Ollama installed: Warning: could not connect to a running Ollama instance
- ⏭️ Ollama server — Not running (expected for dry-run test)
- ✅ Node.js v24.13.0 found
- ✅ scripts/install.sh exists
- ✅ src/api/main.py exists
- ✅ src/llm/ollama_client.py exists
- ✅ src/llm/onboarding_agent.py exists
- ✅ src/llm/phrase_predictor.py exists
- ✅ src/system/file_manager.py exists
- ✅ src/system/browser_control.py exists
- ✅ src/system/app_launcher.py exists
- ✅ src/channels/base.py exists
- ✅ src/channels/telegram_channel.py exists
- ✅ src/channels/channel_manager.py exists
- ✅ src/web/src/app/page.tsx exists
- ✅ src/web/src/components/AppShell.tsx exists
- ✅ src/web/src/components/GazeTracker.tsx exists
- ✅ src/web/src/components/OnboardingScreen.tsx exists
- ✅ src/web/src/components/modules/CommunicationModule.tsx exists
- ✅ src/web/src/components/modules/ControlModule.tsx exists
- ✅ src/web/src/components/modules/ProductivityModule.tsx exists
- ✅ src/web/src/components/modules/ChannelsModule.tsx exists
- ✅ src/landing/hardware.js exists
- ✅ src/landing/index.html exists
- ✅ All 37 Python files have valid syntax
- ✅ Next.js build successful
- ✅ Installer has --uninstall flag
- ✅ Installer has --skip-ollama flag
- ✅ Installer uses port 8765
- ✅ hardware.js exists
- ✅ hardware.js has detection functions
- ✅ No leaked tokens/passwords in source
- ✅ API CORS restricted to localhost

## Notes

- Tests run on macOS Apple Silicon (arm64)
- Installer syntax verified (not executed)
- Next.js build verified
- All Python files syntax-checked
- Security scan: no leaked credentials in source
