# CMS Core API Reference

> **Version:** 1.0.0  
> **Base URL:** `https://api.xynes.com`

The CMS Core service provides a headless content management system for creating, managing, and delivering content across your applications. It supports blog posts, generic content types, comments, and templates.

---

## Table of Contents

- [Authentication](#authentication)
- [Response Format](#response-format)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [Blog Entry Endpoints](#blog-entry-endpoints)
  - [List Published Blog Entries](#list-published-blog-entries)
  - [Get Published Blog Entry by Slug](#get-published-blog-entry-by-slug)
  - [Create Blog Entry](#create-blog-entry)
  - [Read Blog Entry](#read-blog-entry)
  - [List Blog Entries (Admin)](#list-blog-entries-admin)
  - [Update Blog Entry Metadata](#update-blog-entry-metadata)
- [Generic Content Endpoints](#generic-content-endpoints)
  - [List Published Content](#list-published-content)
  - [Get Published Content by Slug](#get-published-content-by-slug)
  - [Create Content Entry](#create-content-entry)
- [Comments Endpoints](#comments-endpoints)
  - [Create Comment](#create-comment)
  - [List Comments for Entry](#list-comments-for-entry)
- [Content Types Endpoints](#content-types-endpoints)
  - [List Content Types for Workspace](#list-content-types-for-workspace)
  - [Ensure Default Content Types](#ensure-default-content-types)
- [Templates Endpoints](#templates-endpoints)
  - [List Global Templates](#list-global-templates)
- [Data Types](#data-types)

---

## Authentication

The CMS API uses **Bearer Token** authentication for protected endpoints. Public endpoints (marked with 🌐) do not require authentication.

```http
Authorization: Bearer <YOUR_ACCESS_TOKEN>
```

### Authentication Types

| Type | Description |
|------|-------------|
| 🌐 **Public** | No authentication required |
| 🔐 **Authenticated** | Requires valid JWT token |
| 🛡️ **RBAC Protected** | Requires specific capability/permission |

---

## Response Format

All responses follow a consistent envelope format:

### Success Response

```json
{
  "ok": true,
  "data": { ... },
  "meta": {
    "requestId": "req-abc123"
  }
}
```

### Error Response

```json
{
  "ok": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": { ... }
  },
  "meta": {
    "requestId": "req-abc123"
  }
}
```

---

## Error Handling

| HTTP Status | Error Code | Description |
|-------------|------------|-------------|
| `400` | `VALIDATION_ERROR` | Invalid request payload or parameters |
| `401` | `UNAUTHORIZED` | Missing or invalid authentication |
| `403` | `FORBIDDEN` | Access denied / insufficient permissions |
| `404` | `ENTRY_NOT_FOUND` | Content entry not found |
| `404` | `CONTENT_TYPE_NOT_FOUND` | Content type not found |
| `404` | `CONTENT_TYPE_ROUTE_SEGMENT_NOT_FOUND` | Route segment not found |
| `404` | `COMMENT_NOT_FOUND` | Comment not found |
| `429` | `RATE_LIMIT_EXCEEDED` | Too many requests |
| `500` | `INTERNAL_ERROR` | Server error |

---

## Rate Limiting

Certain endpoints are rate-limited to prevent abuse:

| Endpoint | Limit |
|----------|-------|
| Comment creation | Configurable per workspace |
| Public content listing | Higher limits for read operations |

Rate limit headers are included in responses:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Remaining requests
- `X-RateLimit-Reset`: Unix timestamp when limit resets

---

## Blog Entry Endpoints

Blog entries are a specialized content type designed for blog posts and articles.

### List Published Blog Entries

🌐 **Public**

Retrieves a paginated list of published blog entries for a workspace.

```http
GET /workspaces/{workspaceId}/blog
```

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `workspaceId` | `uuid` | ✅ | The workspace identifier |

#### Query Parameters

| Parameter | Type | Default | Max | Description |
|-----------|------|---------|-----|-------------|
| `limit` | `integer` | `10` | `100` | Number of entries to return |
| `offset` | `integer` | `0` | - | Pagination offset |
| `tag` | `string` | - | - | Filter by tag |

#### Example Request

```bash
curl -X GET "https://api.xynes.com/workspaces/550e8400-e29b-41d4-a716-446655440000/blog?limit=10&offset=0&tag=technology" \
  -H "Content-Type: application/json"
```

#### Example Response

```json
{
  "ok": true,
  "data": {
    "entries": [
      {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "slug": "getting-started-with-xynes",
        "title": "Getting Started with Xynes",
        "excerpt": "Learn how to build your first application...",
        "tags": ["tutorial", "getting-started"],
        "coverImageUrl": "https://cdn.example.com/cover.jpg",
        "publishedAt": "2025-01-01T12:00:00.000Z",
        "documentId": "doc-uuid-here"
      }
    ]
  }
}
```

#### Action Key
`cms.blog_entry.listPublished`

---

### Get Published Blog Entry by Slug

🌐 **Public**

Retrieves a single published blog entry by its slug.

```http
GET /workspaces/{workspaceId}/blog/{slug}
```

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `workspaceId` | `uuid` | ✅ | The workspace identifier |
| `slug` | `string` | ✅ | The entry's URL-friendly slug |

#### Example Request

```bash
curl -X GET "https://api.xynes.com/workspaces/550e8400-e29b-41d4-a716-446655440000/blog/getting-started-with-xynes" \
  -H "Content-Type: application/json"
```

#### Example Response

```json
{
  "ok": true,
  "data": {
    "entry": {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "slug": "getting-started-with-xynes",
      "title": "Getting Started with Xynes",
      "excerpt": "Learn how to build your first application...",
      "tags": ["tutorial", "getting-started"],
      "coverImageUrl": "https://cdn.example.com/cover.jpg",
      "publishedAt": "2025-01-01T12:00:00.000Z",
      "documentId": "doc-uuid-here"
    }
  }
}
```

#### Errors

| Status | Code | Description |
|--------|------|-------------|
| `404` | `ENTRY_NOT_FOUND` | No published entry found with the given slug |

#### Action Key
`cms.blog_entry.getPublishedBySlug`

---

### Create Blog Entry

🛡️ **RBAC Protected** — Requires `cms.blog_entry.create`

Creates a new blog entry in the specified content type.

```http
POST /workspaces/{workspaceId}/content-types/{contentTypeId}/entries
```

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `workspaceId` | `uuid` | ✅ | The workspace identifier |
| `contentTypeId` | `uuid` | ✅ | The content type identifier |

#### Request Body

```json
{
  "documentId": "doc-uuid-optional",
  "publishNow": false,
  "data": {
    "slug": "my-new-blog-post",
    "title": "My New Blog Post",
    "excerpt": "A brief description of the post",
    "tags": ["news", "update"],
    "coverImageUrl": "https://cdn.example.com/image.jpg",
    "publishedAt": "2025-01-15T10:00:00.000Z"
  }
}
```

#### Request Body Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `contentTypeId` | `uuid` | ✅ | Target content type UUID |
| `documentId` | `uuid` | ❌ | Optional linked document UUID |
| `publishNow` | `boolean` | ❌ | Publish immediately if `true` |
| `data.slug` | `string` | ✅ | URL-friendly identifier (min 1 char) |
| `data.title` | `string` | ✅ | Entry title (min 1 char) |
| `data.excerpt` | `string` | ❌ | Short description |
| `data.tags` | `string[]` | ❌ | Array of tag strings |
| `data.coverImageUrl` | `string` | ❌ | Valid URL to cover image |
| `data.publishedAt` | `string\|null` | ❌ | ISO 8601 datetime for scheduled publishing |

#### Example Request

```bash
curl -X POST "https://api.xynes.com/workspaces/550e8400-e29b-41d4-a716-446655440000/content-types/660e8400-e29b-41d4-a716-446655440000/entries" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <YOUR_TOKEN>" \
  -d '{
    "publishNow": true,
    "data": {
      "slug": "introducing-new-features",
      "title": "Introducing New Features",
      "excerpt": "We are excited to announce...",
      "tags": ["announcement", "features"]
    }
  }'
```

#### Example Response

```json
{
  "ok": true,
  "data": {
    "success": true,
    "entry": {
      "id": "789e4567-e89b-12d3-a456-426614174000",
      "workspaceId": "550e8400-e29b-41d4-a716-446655440000",
      "contentTypeId": "660e8400-e29b-41d4-a716-446655440000",
      "status": "published",
      "publishedAt": "2025-01-03T15:30:00.000Z",
      "documentId": null,
      "data": {
        "slug": "introducing-new-features",
        "title": "Introducing New Features",
        "excerpt": "We are excited to announce...",
        "tags": ["announcement", "features"]
      }
    }
  }
}
```

#### Errors

| Status | Code | Description |
|--------|------|-------------|
| `403` | `CONTENT_TYPE_ACCESS_DENIED` | Content type doesn't belong to workspace |
| `400` | `VALIDATION_ERROR` | Invalid payload |

#### Action Key
`cms.blog_entry.create`

---

### Read Blog Entry

🛡️ **RBAC Protected** — Requires `cms.blog_entry.read`

Reads a blog entry by slug or lists all entries for a content type (admin use).

```http
GET /workspaces/{workspaceId}/content-types/{contentTypeId}/entries
```

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `workspaceId` | `uuid` | ✅ | The workspace identifier |
| `contentTypeId` | `uuid` | ✅ | The content type identifier |

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `slug` | `string` | ❌ | If provided, returns single entry |

#### Example Request

```bash
# Get single entry by slug
curl -X GET "https://api.xynes.com/workspaces/550e8400-e29b-41d4-a716-446655440000/content-types/660e8400-e29b-41d4-a716-446655440000/entries?slug=my-post" \
  -H "Authorization: Bearer <YOUR_TOKEN>"

# List all entries
curl -X GET "https://api.xynes.com/workspaces/550e8400-e29b-41d4-a716-446655440000/content-types/660e8400-e29b-41d4-a716-446655440000/entries" \
  -H "Authorization: Bearer <YOUR_TOKEN>"
```

#### Example Response (Single Entry)

```json
{
  "ok": true,
  "data": {
    "entry": {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "slug": "my-post",
      "title": "My Post",
      "status": "draft",
      "data": { ... }
    }
  }
}
```

#### Example Response (List)

```json
{
  "ok": true,
  "data": {
    "entries": [
      { "id": "...", "slug": "post-1", ... },
      { "id": "...", "slug": "post-2", ... }
    ]
  }
}
```

#### Action Key
`cms.blog_entry.read`

---

### List Blog Entries (Admin)

🛡️ **RBAC Protected** — Requires `cms.blog_entry.listAdmin`

Lists blog entries for administrators with filtering and search capabilities.

#### Payload Schema

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `status` | `enum` | `"all"` | Filter by status: `draft`, `published`, `archived`, `all` |
| `limit` | `integer` | `20` | Max 100 |
| `offset` | `integer` | `0` | Pagination offset |
| `search` | `string` | - | Search in title/content (1-200 chars) |

#### Example Request

```bash
curl -X POST "https://api.xynes.com/internal/cms-actions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <YOUR_TOKEN>" \
  -H "X-Workspace-Id: 550e8400-e29b-41d4-a716-446655440000" \
  -d '{
    "actionKey": "cms.blog_entry.listAdmin",
    "payload": {
      "status": "draft",
      "limit": 20,
      "offset": 0,
      "search": "getting started"
    }
  }'
```

#### Example Response

```json
{
  "ok": true,
  "data": {
    "items": [
      {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "slug": "getting-started",
        "title": "Getting Started Guide",
        "status": "draft",
        "publishedAt": null,
        "updatedAt": "2025-01-02T10:00:00.000Z",
        "documentId": "doc-123",
        "data": { ... }
      }
    ]
  }
}
```

#### Action Key
`cms.blog_entry.listAdmin`

---

### Update Blog Entry Metadata

🛡️ **RBAC Protected** — Requires `cms.blog_entry.updateMeta`

Updates metadata fields and/or publish state of a blog entry without modifying document content.

#### Payload Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `uuid` | ✅ | Entry UUID to update |
| `data` | `object` | ❌ | Metadata fields to update |
| `data.title` | `string` | ❌ | New title (min 1 char) |
| `data.slug` | `string` | ❌ | New slug (min 1 char) |
| `data.excerpt` | `string` | ❌ | New excerpt (max 2000 chars) |
| `data.tags` | `string[]` | ❌ | New tags (max 50 tags, 80 chars each) |
| `data.coverImageUrl` | `string` | ❌ | New cover image URL |
| `publishNow` | `boolean` | ❌ | Set to `true` to publish |
| `unpublish` | `boolean` | ❌ | Set to `true` to unpublish (revert to draft) |

> ⚠️ **Note:** `publishNow` and `unpublish` cannot both be `true`. At least one of `data`, `publishNow`, or `unpublish` must be provided.

#### Example Request

```bash
curl -X POST "https://api.xynes.com/internal/cms-actions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <YOUR_TOKEN>" \
  -H "X-Workspace-Id: 550e8400-e29b-41d4-a716-446655440000" \
  -d '{
    "actionKey": "cms.blog_entry.updateMeta",
    "payload": {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "data": {
        "title": "Updated Title",
        "tags": ["updated", "modified"]
      },
      "publishNow": true
    }
  }'
```

#### Example Response

```json
{
  "ok": true,
  "data": {
    "success": true,
    "entry": {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "status": "published",
      "publishedAt": "2025-01-03T16:00:00.000Z",
      "data": {
        "title": "Updated Title",
        "tags": ["updated", "modified"],
        ...
      }
    }
  }
}
```

#### Action Key
`cms.blog_entry.updateMeta`

---

## Generic Content Endpoints

Generic content endpoints support any content type (programs, events, pages, etc.) identified by their route segment.

### List Published Content

🌐 **Public**

Retrieves published content entries for any content type by route segment.

```http
GET /workspaces/{workspaceId}/content/{routeSegment}
```

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `workspaceId` | `uuid` | ✅ | The workspace identifier |
| `routeSegment` | `string` | ✅ | Content type's URL segment (e.g., `programs`, `events`) |

#### Query Parameters

| Parameter | Type | Default | Max | Description |
|-----------|------|---------|-----|-------------|
| `limit` | `integer` | `10` | `100` | Number of entries to return |
| `offset` | `integer` | `0` | `10000` | Pagination offset |
| `tag` | `string` | - | `100` chars | Filter by tag |

#### Example Request

```bash
curl -X GET "https://api.xynes.com/workspaces/550e8400-e29b-41d4-a716-446655440000/content/programs?limit=10" \
  -H "Content-Type: application/json"
```

#### Example Response

```json
{
  "ok": true,
  "data": {
    "entries": [
      {
        "id": "abc-123",
        "slug": "summer-camp-2025",
        "title": "Summer Camp 2025",
        "excerpt": "Join us for an exciting summer...",
        "tags": ["summer", "camp"],
        "coverImageUrl": "https://cdn.example.com/program.jpg",
        "publishedAt": "2025-01-01T00:00:00.000Z",
        "documentId": null
      }
    ]
  }
}
```

#### Errors

| Status | Code | Description |
|--------|------|-------------|
| `404` | `CONTENT_TYPE_ROUTE_SEGMENT_NOT_FOUND` | No content type with given route segment |

#### Action Key
`cms.content.listPublished`

---

### Get Published Content by Slug

🌐 **Public**

Retrieves a single published content entry by route segment and slug.

```http
GET /workspaces/{workspaceId}/content/{routeSegment}/{slug}
```

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `workspaceId` | `uuid` | ✅ | The workspace identifier |
| `routeSegment` | `string` | ✅ | Content type's URL segment |
| `slug` | `string` | ✅ | Entry's URL-friendly slug |

#### Example Request

```bash
curl -X GET "https://api.xynes.com/workspaces/550e8400-e29b-41d4-a716-446655440000/content/programs/summer-camp-2025" \
  -H "Content-Type: application/json"
```

#### Example Response

```json
{
  "ok": true,
  "data": {
    "entry": {
      "id": "abc-123",
      "slug": "summer-camp-2025",
      "title": "Summer Camp 2025",
      "excerpt": "Join us for an exciting summer...",
      "tags": ["summer", "camp"],
      "coverImageUrl": "https://cdn.example.com/program.jpg",
      "publishedAt": "2025-01-01T00:00:00.000Z",
      "documentId": "doc-456",
      "data": {
        "slug": "summer-camp-2025",
        "title": "Summer Camp 2025",
        "customField": "Custom value",
        ...
      }
    }
  }
}
```

#### Action Key
`cms.content.getPublishedBySlug`

---

### Create Content Entry

🛡️ **RBAC Protected** — Requires `cms.content.create`

Creates a new content entry for any content type.

#### Payload Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `contentTypeId` | `uuid` | ✅ | Target content type UUID |
| `documentId` | `uuid\|null` | ❌ | Optional linked document |
| `publishNow` | `boolean` | ❌ | Publish immediately |
| `data.slug` | `string` | ✅ | URL-friendly identifier |
| `data.title` | `string` | ✅ | Entry title |
| `data.publishedAt` | `string\|null` | ❌ | Scheduled publish date |
| `data.*` | `any` | ❌ | Custom fields (passthrough) |

#### Example Response

```json
{
  "ok": true,
  "data": {
    "entry": {
      "id": "new-entry-uuid",
      "contentTypeId": "content-type-uuid",
      "routeSegment": "programs",
      "slug": "new-program",
      "status": "draft",
      "publishedAt": null,
      "documentId": null,
      "data": {
        "slug": "new-program",
        "title": "New Program"
      }
    }
  }
}
```

#### Action Key
`cms.content.create`

---

## Comments Endpoints

Comments allow users to engage with content entries. Supports threaded replies and moderation.

### Create Comment

🔐 **Authenticated** (or 🌐 **Public** with restrictions)

Creates a new comment on a content entry.

```http
POST /workspaces/{workspaceId}/content-entries/{entryId}/comments
```

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `workspaceId` | `uuid` | ✅ | The workspace identifier |
| `entryId` | `uuid` | ✅ | The content entry to comment on |

#### Request Body

```json
{
  "content": "Great article! Thanks for sharing.",
  "parentId": null,
  "displayName": "John Doe"
}
```

#### Request Body Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `entryId` | `uuid` | ✅ | Content entry UUID |
| `content` | `string` | ✅ | Comment text (1-4000 chars, 1000 for anonymous) |
| `parentId` | `uuid\|null` | ❌ | Parent comment ID for replies |
| `displayName` | `string\|null` | ⚠️ | Display name (required for anonymous, max 100 chars) |

#### Security Notes

- **Anonymous users**: Can only comment on **published** entries
- **Anonymous users**: Limited to 1000 character comments
- **Anonymous users**: Must provide a display name
- **All comments**: Default to `pending` status for moderation

#### Example Request

```bash
curl -X POST "https://api.xynes.com/workspaces/550e8400-e29b-41d4-a716-446655440000/content-entries/abc-123/comments" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "This is a helpful article!",
    "displayName": "Anonymous User"
  }'
```

#### Example Response

```json
{
  "ok": true,
  "data": {
    "id": "comment-uuid",
    "entryId": "abc-123",
    "parentId": null,
    "userId": null,
    "displayName": "Anonymous User",
    "content": "This is a helpful article!",
    "status": "pending",
    "createdAt": "2025-01-03T16:30:00.000Z"
  }
}
```

#### Errors

| Status | Code | Description |
|--------|------|-------------|
| `404` | `ENTRY_NOT_FOUND` | Entry not found (or not published for anonymous) |
| `404` | `COMMENT_NOT_FOUND` | Parent comment not found |
| `400` | `VALIDATION_ERROR` | Content too long or missing display name |

#### Action Key
`cms.comments.create`

---

### List Comments for Entry

🌐 **Public** (with restrictions) / 🔐 **Authenticated**

Lists comments for a content entry with pagination.

```http
GET /workspaces/{workspaceId}/content-entries/{entryId}/comments
```

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `workspaceId` | `uuid` | ✅ | The workspace identifier |
| `entryId` | `uuid` | ✅ | The content entry ID |

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | `integer` | `20` | Max 100 |
| `offset` | `integer` | `0` | Pagination offset |
| `statusFilter` | `enum` | `approved` | Filter: `approved`, `pending`, `all` |
| `includeReplies` | `boolean` | `true` | Include reply comments |

#### Security Notes

- **Anonymous users**: Can only list comments on **published** entries
- **Anonymous users**: Forced to `approved` status filter only

#### Example Request

```bash
curl -X GET "https://api.xynes.com/workspaces/550e8400-e29b-41d4-a716-446655440000/content-entries/abc-123/comments?limit=20&statusFilter=approved" \
  -H "Content-Type: application/json"
```

#### Example Response

```json
{
  "ok": true,
  "data": [
    {
      "id": "comment-1",
      "parentId": null,
      "displayName": "Jane Doe",
      "userId": "user-123",
      "content": "Great post!",
      "status": "approved",
      "createdAt": "2025-01-02T10:00:00.000Z"
    },
    {
      "id": "comment-2",
      "parentId": "comment-1",
      "displayName": "John Smith",
      "userId": null,
      "content": "I agree!",
      "status": "approved",
      "createdAt": "2025-01-02T11:00:00.000Z"
    }
  ]
}
```

#### Action Key
`cms.comments.listForEntry`

---

## Content Types Endpoints

Content types define the structure and routing for different kinds of content.

### List Content Types for Workspace

🛡️ **RBAC Protected** — Requires `cms.content_types.listForWorkspace`

Lists all content types configured for a workspace.

#### Payload Schema

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `includeTemplates` | `boolean` | `false` | Include full template definitions |

#### Example Response

```json
{
  "ok": true,
  "data": [
    {
      "id": "ct-123",
      "name": "Blog Post",
      "slug": "blog-post",
      "routeSegment": "blog",
      "templateKey": "blog_post",
      "templateId": "template-uuid"
    },
    {
      "id": "ct-456",
      "name": "Program",
      "slug": "program",
      "routeSegment": "programs",
      "templateKey": "program"
    }
  ]
}
```

#### Response with Templates

```json
{
  "ok": true,
  "data": [
    {
      "id": "ct-123",
      "name": "Blog Post",
      "slug": "blog-post",
      "routeSegment": "blog",
      "templateKey": "blog_post",
      "templateId": "template-uuid",
      "template": {
        "id": "template-uuid",
        "key": "blog_post",
        "name": "Blog Post",
        "fieldsSchema": { ... }
      }
    }
  ]
}
```

#### Action Key
`cms.content_types.listForWorkspace`

---

### Ensure Default Content Types

🛡️ **RBAC Protected** — Requires `cms.content_types.ensureDefaults`

Seeds default templates and content types for a workspace.

#### Payload Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `templateKeys` | `string[]` | ❌ | Specific templates to seed (defaults to all) |

#### Default Templates

| Key | Name | Route Segment |
|-----|------|---------------|
| `blog_post` | Blog Post | `blog` |
| `program` | Program | `programs` |
| `event` | Event | `events` |

#### Example Request

```bash
curl -X POST "https://api.xynes.com/internal/cms-actions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <YOUR_TOKEN>" \
  -H "X-Workspace-Id: 550e8400-e29b-41d4-a716-446655440000" \
  -d '{
    "actionKey": "cms.content_types.ensureDefaults",
    "payload": {
      "templateKeys": ["blog_post", "program"]
    }
  }'
```

#### Example Response

```json
{
  "ok": true,
  "data": {
    "templates": {
      "created": 2,
      "skipped": 0
    },
    "contentTypes": {
      "created": 2,
      "skipped": 0
    },
    "processedTemplateKeys": ["blog_post", "program"]
  }
}
```

#### Action Key
`cms.content_types.ensureDefaults`

---

## Templates Endpoints

Global templates define the schema and structure for content types.

### List Global Templates

🛡️ **RBAC Protected** — Requires `cms.templates.listGlobal`

Lists all available global content templates.

#### Example Response

```json
{
  "ok": true,
  "data": [
    {
      "id": "template-123",
      "key": "blog_post",
      "name": "Blog Post",
      "fieldsSchema": {
        "type": "object",
        "properties": {
          "slug": { "type": "string" },
          "title": { "type": "string" },
          "excerpt": { "type": "string" },
          "tags": { "type": "array", "items": { "type": "string" } },
          "coverImageUrl": { "type": "string", "format": "uri" }
        },
        "required": ["slug", "title"]
      }
    },
    {
      "id": "template-456",
      "key": "program",
      "name": "Program",
      "fieldsSchema": { ... }
    }
  ]
}
```

#### Action Key
`cms.templates.listGlobal`

---

## Data Types

### BlogEntryData

```typescript
interface BlogEntryData {
  slug: string;          // Required, min 1 char
  title: string;         // Required, min 1 char
  excerpt?: string;      // Optional description
  tags?: string[];       // Optional array of tags
  coverImageUrl?: string; // Optional valid URL
  publishedAt?: string | null; // Optional ISO 8601 datetime
}
```

### ContentEntry

```typescript
interface ContentEntry {
  id: string;            // UUID
  workspaceId: string;   // UUID
  contentTypeId: string; // UUID
  documentId?: string;   // Optional linked document UUID
  status: 'draft' | 'published' | 'archived';
  publishedAt: Date | null;
  createdAt: Date;
  updatedAt: Date;
  data: Record<string, unknown>;
}
```

### Comment

```typescript
interface Comment {
  id: string;            // UUID
  entryId: string;       // Content entry UUID
  parentId: string | null; // Parent comment for replies
  userId: string | null; // User UUID (null for anonymous)
  displayName: string | null;
  content: string;
  status: 'pending' | 'approved' | 'rejected';
  createdAt: Date;
}
```

### ContentType

```typescript
interface ContentType {
  id: string;            // UUID
  workspaceId: string;   // UUID
  name: string;          // Display name
  slug: string;          // URL-friendly identifier
  routeSegment: string;  // URL path segment
  templateKey: string;   // Reference to global template
  templateId?: string;   // Template UUID
}
```

### GlobalTemplate

```typescript
interface GlobalTemplate {
  id: string;            // UUID
  key: string;           // Unique template key
  name: string;          // Display name
  fieldsSchema: object;  // JSON Schema for fields
}
```

---

## Action Keys Reference

| Action Key | Description | Auth |
|------------|-------------|------|
| `cms.blog_entry.listPublished` | List published blog entries | 🌐 Public |
| `cms.blog_entry.getPublishedBySlug` | Get published blog entry | 🌐 Public |
| `cms.blog_entry.create` | Create blog entry | 🛡️ RBAC |
| `cms.blog_entry.read` | Read blog entry/entries | 🛡️ RBAC |
| `cms.blog_entry.listAdmin` | Admin list with filters | 🛡️ RBAC |
| `cms.blog_entry.updateMeta` | Update entry metadata | 🛡️ RBAC |
| `cms.content.listPublished` | List published content | 🌐 Public |
| `cms.content.getPublishedBySlug` | Get published content | 🌐 Public |
| `cms.content.create` | Create content entry | 🛡️ RBAC |
| `cms.comments.create` | Create comment | 🔐 Auth |
| `cms.comments.listForEntry` | List comments | 🌐 Public* |
| `cms.templates.listGlobal` | List global templates | 🛡️ RBAC |
| `cms.content_types.listForWorkspace` | List workspace content types | 🛡️ RBAC |
| `cms.content_types.ensureDefaults` | Seed default content types | 🛡️ RBAC |

*Public with restrictions (approved comments only on published entries)

---

## Changelog

### v1.0.0 (2025-01-03)
- Initial API documentation
- Blog entry CRUD operations
- Generic content support with route segments
- Comments with moderation support
- Content type and template management
