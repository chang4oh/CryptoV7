@echo off
REM Switch between local and cloud MeiliSearch configurations

if "%1"=="" (
    echo Usage: switch_meili_config.bat [local^|cloud]
    exit /b 1
)

if "%1"=="local" (
    echo Switching to local MeiliSearch configuration...
    python simple_meilisearch_fix.py local
    echo Done.
) else if "%1"=="cloud" (
    echo Switching to cloud MeiliSearch configuration...
    python simple_meilisearch_fix.py cloud
    echo Done.
) else (
    echo Invalid option. Use 'local' or 'cloud'.
    exit /b 1
)
