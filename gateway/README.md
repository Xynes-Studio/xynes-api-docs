# Gateway API Reference

> **Version:** 1.0.0  
> **Base URL:** `https://api.xynes.com`

The Gateway service provides platform-wide infrastructure endpoints including feature flags, rate limiting, and request routing to backend services.

---

## Table of Contents

- [Authentication](#authentication)
- [Response Format](#response-format)
- [Error Handling](#error-handling)
- [Feature Flags Endpoints](#feature-flags-endpoints)
  - [Get All Feature Flags](#get-all-feature-flags)
  - [Get Single Feature Flag](#get-single-feature-flag)
- [Data Types](#data-types)

---

## Authentication

The Gateway API uses **Bearer Token** authentication for protected endpoints.

```http
Authorization: Bearer <YOUR_ACCESS_TOKEN>
```

### Authentication Types

| Type | Description |
|------|-------------|
| 🔒 Protected | Requires valid JWT Bearer token |
| 🌐 Public | No authentication required |

---

## Response Format

All responses are returned in JSON format with consistent structure.

### Success Response

```json
{
  "flags": {
    "enableMFA": false,
    "enableInvites": true
  }
}
```

### Error Response

```json
{
  "error": "Unauthorized"
}
```

---

## Error Handling

| Status Code | Description |
|-------------|-------------|
| `200` | Success |
| `401` | Unauthorized - Invalid or missing token |
| `500` | Internal Server Error |

**Note:** Feature flag endpoints are designed to fail gracefully. If the upstream provider (PostHog) is unavailable, conservative defaults are returned instead of errors.

---

## Feature Flags Endpoints

Feature flags enable dynamic feature toggles based on user and workspace context. Powered by PostHog on the backend.

### Get All Feature Flags

🔒 **Protected**

Retrieve all feature flags for the authenticated user.

**Endpoint:** `GET /flags`

**Action Key:** `gateway.flags.getAll`

#### Headers

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `Authorization` | `string` | Yes | Bearer token |

#### Example Request

```bash
curl -X GET "https://api.xynes.com/flags" \
  -H "Authorization: Bearer <YOUR_ACCESS_TOKEN>" \
  -H "Content-Type: application/json"
```

#### Success Response (200)

```json
{
  "flags": {
    "enableMFA": false,
    "enableOAuthGoogle": true,
    "enableOAuthGitHub": true,
    "enableOAuthApple": false,
    "enableInvites": true,
    "enableMultipleWorkspaces": true,
    "enableWorkspaceCreation": true,
    "maintenanceMode": false,
    "enableRateLimitUI": true,
    "enablePasswordReset": true,
    "enableProfileEdit": true
  }
}
```

#### Error Response (401)

```json
{
  "error": "Unauthorized"
}
```

---

### Get Single Feature Flag

🔒 **Protected**

Retrieve a specific feature flag by key.

**Endpoint:** `GET /flags/:key`

**Action Key:** `gateway.flags.getByKey`

#### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `key` | `string` | Yes | The feature flag key (e.g., `enableMFA`) |

#### Headers

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `Authorization` | `string` | Yes | Bearer token |

#### Example Request

```bash
curl -X GET "https://api.xynes.com/flags/enableMFA" \
  -H "Authorization: Bearer <YOUR_ACCESS_TOKEN>" \
  -H "Content-Type: application/json"
```

#### Success Response (200)

```json
{
  "key": "enableMFA",
  "enabled": false,
  "variant": null
}
```

#### Multivariate Flag Response (200)

For flags with A/B test variants:

```json
{
  "key": "checkoutFlow",
  "enabled": true,
  "variant": "variant-b"
}
```

#### Error Response (401)

```json
{
  "error": "Unauthorized"
}
```

---

## Data Types

### AllFlagsResult

Response type for `GET /flags`.

```typescript
interface AllFlagsResult {
  /** Map of flag keys to their enabled state */
  flags: Record<string, boolean>;
}
```

### FeatureFlagResult

Response type for `GET /flags/:key`.

```typescript
interface FeatureFlagResult {
  /** The flag key that was evaluated */
  key: string;
  /** Whether the flag is enabled */
  enabled: boolean;
  /** Optional variant key for multivariate flags */
  variant?: string | null;
}
```

### Default Flags

The following flags are available by default. When PostHog is unavailable, these conservative defaults are returned:

| Flag Key | Default | Description |
|----------|---------|-------------|
| `enableMFA` | `false` | Multi-factor authentication |
| `enableOAuthGoogle` | `true` | Google OAuth login |
| `enableOAuthGitHub` | `true` | GitHub OAuth login |
| `enableOAuthApple` | `false` | Apple OAuth login |
| `enableInvites` | `true` | Workspace invitations |
| `enableMultipleWorkspaces` | `true` | Multiple workspace support |
| `enableWorkspaceCreation` | `true` | Allow creating new workspaces |
| `maintenanceMode` | `false` | Platform maintenance mode |
| `enableRateLimitUI` | `true` | Rate limit UI indicators |
| `enablePasswordReset` | `true` | Password reset functionality |
| `enableProfileEdit` | `true` | Profile editing |

---

## Security Considerations

1. **Authentication Required**: All feature flag endpoints require a valid JWT token
2. **User Context**: Flags are evaluated per-user, supporting personalization and A/B testing
3. **Workspace Scoping**: Flags can be targeted to specific workspaces
4. **Graceful Degradation**: If PostHog is unavailable, conservative defaults are returned
5. **No Sensitive Data**: Flag responses contain only boolean values and variant strings

---

## Related Documentation

- [DEVELOPER.md](../../xynes-gateway/DEVELOPER.md) - Gateway development guide
- [PostHog Feature Flags](https://posthog.com/docs/feature-flags) - Upstream provider docs
