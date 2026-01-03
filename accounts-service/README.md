# Accounts Service API Reference

> **Version:** 1.0.0  
> **Base URL:** `https://api.xynes.com`

The Accounts Service manages user identity, workspace creation, membership, and workspace invitations. It serves as the foundation for multi-tenant workspace management in the Xynes platform.

---

## Table of Contents

- [Authentication](#authentication)
- [Response Format](#response-format)
- [Error Handling](#error-handling)
- [User Endpoints](#user-endpoints)
  - [Get or Create Current User](#get-or-create-current-user)
- [Workspace Endpoints](#workspace-endpoints)
  - [List User's Workspaces](#list-users-workspaces)
  - [Create Workspace](#create-workspace)
- [Workspace Invites Endpoints](#workspace-invites-endpoints)
  - [Create Workspace Invite](#create-workspace-invite)
  - [Resolve Workspace Invite](#resolve-workspace-invite)
  - [Accept Workspace Invite](#accept-workspace-invite)
- [Data Types](#data-types)
- [Action Keys Reference](#action-keys-reference)

---

## Authentication

The Accounts Service uses **Bearer Token** authentication via JWT (JSON Web Tokens). Tokens are obtained through your identity provider (e.g., Supabase Auth, Auth0, or custom OAuth).

```http
Authorization: Bearer <YOUR_JWT_TOKEN>
```

### JWT Claims

The following claims are extracted from the JWT and used for user identity:

| Claim | Description |
|-------|-------------|
| `sub` | User ID (required) |
| `email` | User's email address |
| `name` | User's display name |
| `avatar_url` / `picture` | User's avatar URL |

### Authentication Types

| Type | Description |
|------|-------------|
| 🌐 **Public** | No authentication required |
| 🔐 **Authenticated** | Requires valid JWT token |
| 🛡️ **RBAC Protected** | Requires specific workspace permission |

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
| `400` | `MISSING_CONTEXT` | Missing required context (e.g., workspaceId) |
| `401` | `UNAUTHORIZED` | Missing or invalid authentication token |
| `403` | `FORBIDDEN` | Access denied / insufficient permissions |
| `404` | `NOT_FOUND` | Resource not found |
| `409` | `CONFLICT` | Resource conflict (e.g., duplicate slug) |
| `410` | `GONE` | Resource expired or cancelled |
| `500` | `INTERNAL_ERROR` | Server error |
| `502` | `BAD_GATEWAY` | Upstream service error (e.g., authz service) |

---

## User Endpoints

### Get or Create Current User

🔐 **Authenticated**

Retrieves the current user's profile and workspace memberships. If the user doesn't exist in the database, they are automatically created (upsert behavior).

This is typically the first API call made after authentication to bootstrap the user session.

```http
GET /me
```

#### Headers

| Header | Required | Description |
|--------|----------|-------------|
| `Authorization` | ✅ | Bearer token with valid JWT |

#### Example Request

```bash
curl -X GET "https://api.xynes.com/me" \
  -H "Authorization: Bearer <YOUR_JWT_TOKEN>"
```

#### Example Response

```json
{
  "ok": true,
  "data": {
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "user@example.com",
      "displayName": "John Doe",
      "avatarUrl": "https://avatars.example.com/johndoe.jpg"
    },
    "workspaces": [
      {
        "id": "660e8400-e29b-41d4-a716-446655440001",
        "name": "My Workspace",
        "slug": "my-workspace",
        "planType": "free"
      },
      {
        "id": "770e8400-e29b-41d4-a716-446655440002",
        "name": "Team Project",
        "slug": "team-project",
        "planType": "pro"
      }
    ]
  }
}
```

#### Response Schema

| Field | Type | Description |
|-------|------|-------------|
| `user.id` | `uuid` | Unique user identifier |
| `user.email` | `string` | User's email address |
| `user.displayName` | `string\|null` | User's display name |
| `user.avatarUrl` | `string\|null` | URL to user's avatar |
| `workspaces` | `array` | List of workspaces user is a member of |
| `workspaces[].id` | `uuid` | Workspace identifier |
| `workspaces[].name` | `string` | Workspace display name |
| `workspaces[].slug` | `string\|null` | URL-friendly workspace slug |
| `workspaces[].planType` | `string` | Subscription plan type |

#### Behavior Notes

- **Upsert Logic:** If the user ID from JWT doesn't exist, a new user record is created
- **Profile Sync:** User's email, name, and avatar are synced from JWT claims on each call
- **Active Memberships Only:** Only workspaces where user's membership status is `active` are returned

#### Errors

| Status | Code | Description |
|--------|------|-------------|
| `401` | `UNAUTHORIZED` | Missing or invalid JWT token |
| `401` | `UNAUTHORIZED` | Missing or invalid email in JWT claims |

#### Action Key
`accounts.me.getOrCreate`

---

## Workspace Endpoints

### List User's Workspaces

🔐 **Authenticated**

Lists all workspaces that the current user is a member of.

```http
GET /workspaces
```

#### Headers

| Header | Required | Description |
|--------|----------|-------------|
| `Authorization` | ✅ | Bearer token with valid JWT |

#### Example Request

```bash
curl -X GET "https://api.xynes.com/workspaces" \
  -H "Authorization: Bearer <YOUR_JWT_TOKEN>"
```

#### Example Response

```json
{
  "ok": true,
  "data": {
    "workspaces": [
      {
        "id": "660e8400-e29b-41d4-a716-446655440001",
        "name": "My Workspace",
        "slug": "my-workspace",
        "planType": "free"
      },
      {
        "id": "770e8400-e29b-41d4-a716-446655440002",
        "name": "Team Project",
        "slug": "team-project",
        "planType": "pro"
      }
    ]
  }
}
```

#### Response Schema

| Field | Type | Description |
|-------|------|-------------|
| `workspaces` | `array` | List of user's workspaces |
| `workspaces[].id` | `uuid` | Workspace identifier |
| `workspaces[].name` | `string` | Workspace display name |
| `workspaces[].slug` | `string\|null` | URL-friendly workspace slug |
| `workspaces[].planType` | `string` | Subscription plan (`free`, `pro`, etc.) |

#### Errors

| Status | Code | Description |
|--------|------|-------------|
| `401` | `UNAUTHORIZED` | Missing or invalid JWT token |

#### Action Key
`accounts.workspaces.listForUser`

---

### Create Workspace

🔐 **Authenticated**

Creates a new workspace and assigns the current user as the workspace owner.

```http
POST /workspaces
```

#### Headers

| Header | Required | Description |
|--------|----------|-------------|
| `Authorization` | ✅ | Bearer token with valid JWT |
| `Content-Type` | ✅ | `application/json` |

#### Request Body

```json
{
  "name": "My New Workspace",
  "slug": "my-new-workspace"
}
```

#### Request Body Schema

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `name` | `string` | ✅ | 1-200 chars | Workspace display name |
| `slug` | `string` | ✅ | 3-63 chars, lowercase alphanumeric with dashes, no leading/trailing dash | URL-friendly unique identifier |

##### Slug Format Rules

- Must be 3-63 characters
- Lowercase letters (`a-z`), numbers (`0-9`), and dashes (`-`) only
- Must start and end with alphanumeric character
- No consecutive dashes
- Must be globally unique

**Valid examples:** `my-workspace`, `acme-corp`, `project-2025`  
**Invalid examples:** `-invalid`, `invalid-`, `My Workspace`, `ab`

#### Example Request

```bash
curl -X POST "https://api.xynes.com/workspaces" \
  -H "Authorization: Bearer <YOUR_JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Acme Corporation",
    "slug": "acme-corp"
  }'
```

#### Example Response

```json
{
  "ok": true,
  "data": {
    "id": "880e8400-e29b-41d4-a716-446655440003",
    "name": "Acme Corporation",
    "slug": "acme-corp",
    "planType": "free",
    "createdBy": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

#### Response Schema

| Field | Type | Description |
|-------|------|-------------|
| `id` | `uuid` | New workspace identifier |
| `name` | `string` | Workspace display name |
| `slug` | `string` | URL-friendly workspace slug |
| `planType` | `string` | Default plan type (`free`) |
| `createdBy` | `uuid` | User ID of workspace creator |

#### What Happens on Creation

1. Workspace record is created in the database
2. Workspace member record is created linking the user to the workspace
3. User is assigned the `workspace_owner` role via the authorization service
4. If role assignment fails, the workspace is rolled back (cleaned up)

#### Errors

| Status | Code | Description |
|--------|------|-------------|
| `400` | `VALIDATION_ERROR` | Invalid name or slug format |
| `401` | `UNAUTHORIZED` | Missing or invalid JWT token |
| `409` | `CONFLICT` | Workspace slug already exists |
| `502` | `BAD_GATEWAY` | Failed to assign owner role (authz service error) |

#### Action Key
`accounts.workspaces.create`

---

## Workspace Invites Endpoints

Workspace invites allow workspace owners/admins to invite users to join their workspace.

### Invite Flow Overview

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Create    │────▶│   Resolve   │────▶│   Accept    │
│   Invite    │     │   (Preview) │     │   Invite    │
└─────────────┘     └─────────────┘     └─────────────┘
  POST /invites      GET /token          POST /token/accept
  (Protected)        (Public)            (Authenticated)
```

1. **Create:** Workspace admin creates invite for an email
2. **Resolve:** Invitee previews invite details (public, no auth)
3. **Accept:** Invitee accepts and joins workspace

---

### Create Workspace Invite

🛡️ **RBAC Protected** — Requires `accounts.invites.create` permission

Creates an invitation for a user to join a workspace.

```http
POST /workspaces/{workspaceId}/invites
```

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `workspaceId` | `uuid` | ✅ | The workspace to invite the user to |

#### Headers

| Header | Required | Description |
|--------|----------|-------------|
| `Authorization` | ✅ | Bearer token with valid JWT |
| `Content-Type` | ✅ | `application/json` |

#### Request Body

```json
{
  "email": "newuser@example.com",
  "roleKey": "workspace_member"
}
```

#### Request Body Schema

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `email` | `string` | ✅ | Valid email, max 320 chars | Email of the user to invite |
| `roleKey` | `string` | ✅ | 1-128 chars | Role to assign on acceptance |

#### Available Roles

| Role Key | Description |
|----------|-------------|
| `workspace_owner` | Full workspace control |
| `workspace_member` | Standard member access |

#### Example Request

```bash
curl -X POST "https://api.xynes.com/workspaces/660e8400-e29b-41d4-a716-446655440001/invites" \
  -H "Authorization: Bearer <YOUR_JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "colleague@example.com",
    "roleKey": "workspace_member"
  }'
```

#### Example Response

```json
{
  "ok": true,
  "data": {
    "id": "990e8400-e29b-41d4-a716-446655440004",
    "workspaceId": "660e8400-e29b-41d4-a716-446655440001",
    "email": "colleague@example.com",
    "roleKey": "workspace_member",
    "status": "pending",
    "expiresAt": "2025-01-10T12:00:00.000Z",
    "token": "xyn_inv_a1b2c3d4e5f6..."
  }
}
```

#### Response Schema

| Field | Type | Description |
|-------|------|-------------|
| `id` | `uuid` | Invite identifier |
| `workspaceId` | `uuid` | Target workspace |
| `email` | `string` | Invitee's email (normalized to lowercase) |
| `roleKey` | `string` | Role to be assigned |
| `status` | `string` | Always `pending` on creation |
| `expiresAt` | `string` | ISO 8601 expiration datetime (7 days default) |
| `token` | `string` | **One-time visible** invite token for the URL |

#### Security Notes

- ⚠️ The `token` is only returned once at creation time
- The token should be sent to the invitee (e.g., via email)
- Tokens are stored as one-way hashes in the database
- Tokens expire after 7 days by default

#### Errors

| Status | Code | Description |
|--------|------|-------------|
| `400` | `VALIDATION_ERROR` | Invalid email or roleKey |
| `400` | `MISSING_CONTEXT` | Missing workspaceId |
| `401` | `UNAUTHORIZED` | Missing or invalid JWT token |
| `403` | `FORBIDDEN` | User lacks invite creation permission |

#### Action Key
`accounts.invites.create`

---

### Resolve Workspace Invite

🌐 **Public**

Retrieves details about an invite without accepting it. Used to display invite preview page.

```http
GET /workspace-invites/{token}
```

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `token` | `string` | ✅ | The invite token (32-512 chars) |

#### Example Request

```bash
curl -X GET "https://api.xynes.com/workspace-invites/xyn_inv_a1b2c3d4e5f6..."
```

#### Example Response

```json
{
  "ok": true,
  "data": {
    "workspaceName": "Acme Corporation",
    "inviterName": "John Doe",
    "roleKey": "workspace_member",
    "status": "pending",
    "expiresAt": "2025-01-10T12:00:00.000Z"
  }
}
```

#### Response Schema

| Field | Type | Description |
|-------|------|-------------|
| `workspaceName` | `string` | Name of the workspace |
| `inviterName` | `string\|null` | Display name of inviter |
| `roleKey` | `string` | Role that will be assigned |
| `status` | `string` | Invite status (see below) |
| `expiresAt` | `string` | ISO 8601 expiration datetime |

#### Invite Statuses

| Status | Description |
|--------|-------------|
| `pending` | Invite is active and can be accepted |
| `accepted` | Invite has been accepted |
| `expired` | Invite has passed its expiration date |
| `cancelled` | Invite was cancelled by an admin |

#### Use Case: Invite Preview Page

```html
<!-- Example invite preview page -->
<div class="invite-preview">
  <h1>You've been invited to join {{workspaceName}}</h1>
  <p>{{inviterName}} invited you as a {{roleKey}}</p>
  <p>Expires: {{expiresAt}}</p>
  <button onclick="acceptInvite()">Accept Invitation</button>
</div>
```

#### Errors

| Status | Code | Description |
|--------|------|-------------|
| `404` | `NOT_FOUND` | Invite not found (invalid token) |

#### Action Key
`accounts.invites.resolve`

---

### Accept Workspace Invite

🔐 **Authenticated**

Accepts a workspace invitation and adds the user to the workspace.

```http
POST /workspace-invites/{token}/accept
```

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `token` | `string` | ✅ | The invite token (32-512 chars) |

#### Headers

| Header | Required | Description |
|--------|----------|-------------|
| `Authorization` | ✅ | Bearer token with valid JWT |

#### Example Request

```bash
curl -X POST "https://api.xynes.com/workspace-invites/xyn_inv_a1b2c3d4e5f6.../accept" \
  -H "Authorization: Bearer <YOUR_JWT_TOKEN>"
```

#### Example Response

```json
{
  "ok": true,
  "data": {
    "accepted": true,
    "workspaceId": "660e8400-e29b-41d4-a716-446655440001",
    "roleKey": "workspace_member",
    "workspaceMemberCreated": true
  }
}
```

#### Response Schema

| Field | Type | Description |
|-------|------|-------------|
| `accepted` | `boolean` | Always `true` on success |
| `workspaceId` | `uuid` | The workspace joined |
| `roleKey` | `string` | Role assigned to the user |
| `workspaceMemberCreated` | `boolean` | `true` if new membership was created, `false` if user was already a member |

#### What Happens on Accept

1. Token is validated and invite record is found
2. Expiration is checked (expired invites are rejected)
3. User's email is verified to match invite email
4. Workspace membership is created (if not exists)
5. Invite status is set to `accepted`
6. User is assigned the specified role via authorization service
7. If any step fails, changes are rolled back

#### Email Verification

The accepting user's email (from JWT) **must match** the invite email exactly (case-insensitive). This prevents unauthorized users from accepting invites intended for others.

#### Errors

| Status | Code | Description |
|--------|------|-------------|
| `401` | `UNAUTHORIZED` | Missing or invalid JWT token |
| `403` | `FORBIDDEN` | User's email doesn't match invite email |
| `404` | `NOT_FOUND` | Invite not found |
| `409` | `CONFLICT` | Invite already processed (accepted/cancelled) |
| `410` | `GONE` | Invite expired or cancelled |
| `502` | `BAD_GATEWAY` | Failed to assign role (authz service error) |

#### Action Key
`accounts.invites.accept`

---

## Data Types

### User

```typescript
interface User {
  id: string;            // UUID from identity provider
  email: string;         // Primary email address
  displayName: string | null;  // Display name (max 200 chars)
  avatarUrl: string | null;    // Avatar image URL (max 2048 chars)
  createdAt: Date;       // Account creation timestamp
}
```

### Workspace

```typescript
interface Workspace {
  id: string;            // UUID
  name: string;          // Display name (1-200 chars)
  slug: string | null;   // URL-friendly identifier (3-63 chars)
  createdBy: string;     // User UUID of creator
  planType: string;      // Subscription plan (e.g., "free", "pro")
  createdAt: Date;       // Creation timestamp
}
```

### WorkspaceMember

```typescript
interface WorkspaceMember {
  workspaceId: string;   // Workspace UUID
  userId: string;        // User UUID
  status: 'active' | 'inactive';  // Membership status
  joinedAt: Date;        // When user joined
}
```

### WorkspaceInvite

```typescript
interface WorkspaceInvite {
  id: string;            // UUID
  workspaceId: string;   // Target workspace UUID
  email: string;         // Invitee email (normalized lowercase)
  roleKey: string;       // Role to assign on acceptance
  invitedBy: string;     // User UUID who created invite
  token: string;         // Hashed invite token (stored securely)
  status: 'pending' | 'accepted' | 'expired' | 'cancelled';
  expiresAt: Date;       // Expiration timestamp
  createdAt: Date;       // Creation timestamp
}
```

### Role Keys

| Role | Description | Typical Permissions |
|------|-------------|-------------------|
| `workspace_owner` | Full workspace control | All actions |
| `workspace_member` | Standard member | Read, create content |
| `super_admin` | Platform-wide admin | All actions on all workspaces |

---

## Action Keys Reference

| Action Key | Description | Auth | Scope |
|------------|-------------|------|-------|
| `accounts.me.getOrCreate` | Get/create current user profile | 🔐 Auth | Global |
| `accounts.workspaces.listForUser` | List user's workspaces | 🔐 Auth | Global |
| `accounts.workspaces.create` | Create new workspace | 🔐 Auth | Global |
| `accounts.invites.create` | Create workspace invite | 🛡️ RBAC | Workspace |
| `accounts.invites.resolve` | Preview invite details | 🌐 Public | Global |
| `accounts.invites.accept` | Accept workspace invite | 🔐 Auth | Global |

### Internal Actions (Not Exposed via Gateway)

| Action Key | Description |
|------------|-------------|
| `accounts.ping` | Health check ping |
| `accounts.user.readSelf` | Read current user (internal) |
| `accounts.workspace.readCurrent` | Read workspace by ID (internal) |
| `accounts.workspaceMember.ensure` | Ensure membership exists (internal) |

---

## Rate Limiting

The following rate limits apply to protect against abuse:

| Endpoint | Limit | Window |
|----------|-------|--------|
| `POST /workspaces` | 10 requests | 1 hour |
| `POST /workspaces/:id/invites` | 50 requests | 1 hour |
| `POST /workspace-invites/:token/accept` | 10 requests | 1 minute |

Rate limit headers are included in responses:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Remaining requests
- `X-RateLimit-Reset`: Unix timestamp when limit resets

---

## Security Considerations

### Token Security

- Invite tokens are generated using cryptographically secure random bytes
- Tokens are stored as SHA-256 hashes (never plain text)
- Raw tokens are only returned once at creation time
- Tokens expire after 7 days (configurable)

### Email Verification

- Invite acceptance requires exact email match (case-insensitive)
- Prevents unauthorized users from accepting invites

### Workspace Isolation

- Each workspace is completely isolated
- Users can only access workspaces they're members of
- RBAC enforces permission checks on all workspace-scoped operations

### Rollback Safety

- Workspace creation rolls back if role assignment fails
- Invite acceptance rolls back if role assignment fails
- Prevents partial state that could cause security issues

---

## Changelog

### v1.0.0 (2025-01-03)
- Initial API documentation
- User profile management (`/me`)
- Workspace CRUD operations
- Workspace invite flow (create, resolve, accept)
- RBAC integration documentation
