# MITO Engine API Documentation

## Overview
Complete API reference for MITO Engine v1.2.0 endpoints and integrations.

## Core Endpoints

### AI Generation
- `POST /api/generate` - Generate AI responses with provider selection
- `GET /api/version` - Get MITO Engine version information
- `GET /api/system-status` - System health and status

### File Management
- `GET /api/get-project-files` - List all project files with metadata
- `GET /api/get-file-content` - Get content of specific file
- `POST /api/save-file` - Save file content

### Memory Management
- `GET /api/memory/list` - Get all memories
- `POST /api/memory/create` - Create new memory
- `PUT /api/memory/update/<id>` - Update memory
- `DELETE /api/memory/delete/<id>` - Delete memory

### Admin Endpoints
- `POST /admin-login` - Admin authentication
- `GET /api/admin/weights` - Get MITO weights (admin only)
- `POST /api/admin/weights/<category>` - Update weights (admin only)

### File Browser Integration
- `GET /mito-files` - Visual file browser interface
- `GET /api/get-project-files` - Enhanced file listing with metadata

## Authentication
Admin endpoints require authentication via session management.

## Response Formats
All endpoints return JSON with standard success/error structure:
```json
{
  "success": true/false,
  "data": {},
  "error": "Error message if applicable"
}
```