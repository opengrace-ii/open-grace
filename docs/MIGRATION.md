# Migration Guide

This document provides guidance for migrating between versions of Open Grace.

## Table of Contents

- [Upgrading to 1.0.0](#upgrading-to-100)
- [Database Migrations](#database-migrations)
- [Configuration Changes](#configuration-changes)
- [Breaking Changes](#breaking-changes)

---

## Upgrading to 1.0.0

### Prerequisites

Before upgrading:
1. Backup your data directory
2. Ensure Python 3.10+ is installed
3. Update Ollama to latest version

### Upgrade Steps

```bash
# 1. Stop running services
pkill -f "uvicorn open_grace.api.server"
pkill -f "npm run dev"

# 2. Backup data
cp -r ./data ./data-backup-$(date +%Y%m%d)

# 3. Pull latest code
git pull origin main

# 4. Update dependencies
pip install -e ".[dev]"
cd frontend && npm install

# 5. Run database migrations (if any)
grace migrate

# 6. Restart services
uvicorn open_grace.api.server:app --reload
cd frontend && npm run dev
```

### Post-Upgrade Checklist

- [ ] Verify API is accessible at http://localhost:8000/health
- [ ] Verify frontend loads at http://localhost:5173
- [ ] Test login functionality
- [ ] Verify agents are responding
- [ ] Check that existing tasks are visible

---

## Database Migrations

Open Grace uses SQLite for metadata storage. Migrations are handled automatically on startup.

### Manual Migration

If automatic migration fails:

```bash
# Export data
grace db export --output backup.json

# Reset database
rm ./data/grace.db

# Import data
grace db import --input backup.json
```

### Vector Store Migration

The vector store (FAISS/ChromaDB) may need re-indexing after major updates:

```bash
# Re-index all documents
grace knowledge reindex
```

---

## Configuration Changes

### v1.0.0 Configuration Updates

New environment variables in v1.0.0:

```bash
# New in v1.0.0
GRACE_ENABLE_WEBSOCKET=true
GRACE_MAX_CONCURRENT_TASKS=10
```

Deprecated variables (still work but will be removed):

```bash
# Deprecated, use GRACE_API_HOST instead
API_HOST

# Deprecated, use GRACE_API_PORT instead
API_PORT
```

### Migrating .env Files

```bash
# Old format
API_HOST=localhost
API_PORT=8000

# New format
GRACE_API_HOST=0.0.0.0
GRACE_API_PORT=8000
```

---

## Breaking Changes

### v1.0.0

#### CLI Commands

| Old Command | New Command | Notes |
|-------------|-------------|-------|
| `grace start` | `grace init` | Initialize instead of start |
| `grace agent list` | `grace agents list` | Plural form |
| `grace task create` | `grace task` | Simplified |

#### API Endpoints

| Old Endpoint | New Endpoint | Notes |
|--------------|--------------|-------|
| `POST /tasks/create` | `POST /tasks` | RESTful convention |
| `GET /agents/status` | `GET /agents` | Simplified |

#### Plugin API

Plugins built for v0.x need updates:

```python
# Old (v0.x)
from open_grace.plugins import BaseTool

class MyTool(BaseTool):
    def run(self, args):
        pass

# New (v1.0)
from grace_sdk import Tool

class MyTool(Tool):
    def execute(self, context):
        pass
```

---

## Rollback Procedure

If upgrade fails, rollback to previous version:

```bash
# 1. Stop services
pkill -f "uvicorn open_grace.api.server"
pkill -f "npm run dev"

# 2. Restore database
cp ./data-backup-YYYYMMDD/grace.db ./data/

# 3. Checkout previous version
git checkout v0.9.0

# 4. Reinstall dependencies
pip install -e ".[dev]"
cd frontend && npm install

# 5. Restart
uvicorn open_grace.api.server:app --reload
cd frontend && npm run dev
```

---

## Troubleshooting

### Migration Failed

```bash
# Check logs
tail -f logs/grace.log

# Verify database integrity
sqlite3 data/grace.db "PRAGMA integrity_check;"

# Reset if necessary (WARNING: Data loss!)
rm -rf ./data/*
grace init
```

### Agents Not Responding

```bash
# Restart agent workers
grace agents restart

# Check agent health
grace agents health
```

### Frontend Not Loading

```bash
# Clear npm cache
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

---

## Getting Help

- [GitHub Issues](https://github.com/opengrace-ii/open-grace/issues)
- [GitHub Discussions](https://github.com/opengrace-ii/open-grace/discussions)
- [Documentation](https://github.com/opengrace-ii/open-grace/wiki)

---

*Last updated: March 2026*