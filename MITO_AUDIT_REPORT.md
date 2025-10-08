# MITO Engine Audit Report

**Generated:** 2025-10-08T13:06:37.501955  
**Version:** 1.2.0  
**Total Time:** 0.19 seconds

## Summary
- **Tests Run:** 61
- **Tests Passed:** 36
- **Tests Failed:** 25
- **Success Rate:** 59.0%

## Modules Status
- ✗ app
- ✓ config
- ✗ models
- ✓ ai_providers
- ✓ mito_agent
- ✓ mito_weights
- ✓ memory_manager
- ✓ notification_manager
- ✗ admin_auth
- ✓ api_usage

## Files Status
- ✓ app.py (285588 bytes)
- ✓ main.py (278 bytes)
- ✓ config.py (1573 bytes)
- ✓ models.py (5091 bytes)
- ✓ ai_providers.py (13667 bytes)
- ✓ mito_agent.py (44621 bytes)
- ✓ mito_weights.py (8192 bytes)
- ✓ memory_manager.py (25033 bytes)
- ✓ notification_manager.py (14948 bytes)
- ✓ admin_auth.py (5557 bytes)
- ✓ api_usage.py (8289 bytes)
- ✓ unified_request_processor.py (13765 bytes)

## Errors
- ❌ Import app: No module named 'flask'
- ❌ Import models: No module named 'flask_sqlalchemy'
- ❌ Import admin_auth: No module named 'flask'
- ❌ ENV DATABASE_URL: Length: 0
- ❌ ENV OPENAI_API_KEY: Length: 0
- ❌ ENV PGDATABASE: Length: 0
- ❌ ENV PGHOST: Length: 0
- ❌ ENV PGUSER: Length: 0
- ❌ ENV PGPASSWORD: Length: 0
- ❌ ENV PGPORT: Length: 0
- ❌ Package flask: No module named 'flask'
- ❌ Package flask_sqlalchemy: No module named 'flask_sqlalchemy'
- ❌ Package psycopg2: No module named 'psycopg2'
- ❌ Package openai: No module named 'openai'
- ❌ Package anthropic: No module named 'anthropic'
- ❌ Package gunicorn: No module named 'gunicorn'
- ❌ Package werkzeug: No module named 'werkzeug'
- ❌ Package marshmallow: No module named 'marshmallow'
- ❌ AI Provider openai: missing_api_key
- ❌ AI Provider llama: missing_api_key
- ❌ AI Provider claude: missing_api_key
- ❌ Database Connection: No module named 'psycopg2'
- ❌ Memory System: cannot import name 'MemoryManager' from 'memory_manager' (/home/runner/work/mito_engine/mito_engine/memory_manager.py)
- ❌ Admin Auth: No module named 'flask'
- ❌ Performance Import: No module named 'flask'
