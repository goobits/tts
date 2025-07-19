# API Reference Guide

## Introduction

This document describes the core API endpoints for our data processing service.

## Authentication

All API requests require authentication using Bearer tokens:

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" https://api.example.com/v1/data
```

## Endpoints

### GET /api/v1/data

Retrieves data from the system.

**Parameters:**
- `limit` (integer): Maximum number of results to return
- `offset` (integer): Number of results to skip
- `filter` (string): Optional filter expression

**Response:**
```json
{
  "status": "success",
  "data": [...],
  "pagination": {
    "total": 1000,
    "limit": 50,
    "offset": 0
  }
}
```

### POST /api/v1/process

Processes input data according to specified configuration.

**Request Body:**
```json
{
  "input": {...},
  "config": {
    "mode": "async",
    "timeout": 300
  }
}
```

## Error Handling

The API uses standard HTTP status codes:
- `200` - Success
- `400` - Bad Request
- `401` - Unauthorized
- `500` - Internal Server Error

**Note:** Always check the `error` field in the response for detailed error messages.