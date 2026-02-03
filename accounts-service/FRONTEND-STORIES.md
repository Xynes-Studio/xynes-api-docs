# Accounts Frontend - User Stories & Architecture

> **Version:** 2.0.0  
> **Last Updated:** 2026-01-03  
> **Sprint Duration:** 2 weeks  
> **Team Size:** 2 developers  
> **Target Consumer:** CMS Admin (Phase 1)

## Table of Contents

- [Architecture Decision](#architecture-decision)
- [Modular Architecture](#modular-architecture)
- [Sprint 1 Backlog](#sprint-1-backlog)
- [Epic: AUTH-FE-1 — Authentication Core](#epic-auth-fe-1--authentication-core)
- [Epic: AUTH-FE-2 — Workspace Management](#epic-auth-fe-2--workspace-management)
- [Epic: AUTH-FE-3 — Invite System](#epic-auth-fe-3--invite-system)
- [Epic: SEC-FE-1 — Security Hardening](#epic-sec-fe-1--security-hardening)
- [Technical Requirements](#technical-requirements)
- [Environment Configuration](#environment-configuration)
- [Definition of Done](#definition-of-done)

---

## Architecture Decision

### The Problem

Multiple frontend applications (CMS Admin, Doc Editor, Marketing Site, etc.) need:
- Shared authentication flow (Supabase)
- Consistent onboarding experience
- Workspace switching/management
- User profile management

### Options Considered

| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| **A: Separate Auth App Only** | Single entry point, easy to secure | No shared code, duplicate logic | ❌ |
| **B: Published NPM Package + Auth App** | Reusable, versioned, independent repos | Need to publish, version management | ✅ **Chosen** |
| **C: Micro-frontend** | Independent deployments, tech agnostic | Complex setup, runtime overhead | ❌ |

### Recommended Approach

## **Option B: Published NPM Package** + **Dedicated Auth App**

A two-part solution that keeps repositories independent:

### Part 1: `@xynes/auth-sdk` - Published NPM Package

```
xynes-auth-sdk/                    # Separate repo: github.com/xynes/auth-sdk
├── src/
│   ├── hooks/
│   │   ├── useAuth.ts             # Core auth state & methods
│   │   ├── useWorkspace.ts        # Workspace selection
│   │   └── useInvite.ts           # Invite resolution/acceptance
│   ├── providers/
│   │   ├── AuthProvider.tsx       # Supabase + API integration
│   │   └── WorkspaceProvider.tsx  # Workspace context
│   ├── api/
│   │   └── accounts-client.ts     # Type-safe API client
│   ├── types/
│   │   └── index.ts               # User, Workspace, Invite types
│   └── index.ts                   # Public exports
├── package.json
├── tsconfig.json
├── tsup.config.ts                 # Bundle config
├── .env.example
└── README.md
```

### Part 2: `xynes-auth-app` - Dedicated Auth Application

```
xynes-auth-app/                    # Separate repo: github.com/xynes/auth-app
├── src/
│   ├── app/
│   │   ├── login/page.tsx
│   │   ├── signup/page.tsx
│   │   ├── logout/page.tsx
│   │   ├── invite/[token]/page.tsx
│   │   ├── onboarding/page.tsx
│   │   ├── reset-password/page.tsx
│   │   └── callback/page.tsx      # OAuth callback handler
│   ├── components/
│   │   ├── LoginForm.tsx
│   │   ├── SignupForm.tsx
│   │   ├── WorkspaceCreator.tsx
│   │   ├── WorkspaceSelector.tsx
│   │   └── InviteAcceptor.tsx
│   └── lib/
│       └── supabase.ts
├── package.json                   # Uses @xynes/auth-sdk
├── .env.local
└── next.config.js
```

### Part 3: Consumer Apps (CMS, Docs, etc.)

```
xynes-cms-admin/                   # Separate repo
├── src/
│   └── ...
├── package.json
│   └── dependencies:
│       └── "@xynes/auth-sdk": "^1.0.0"  # 👈 Install from npm
└── .env.local
```

### How It Works

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            AUTHENTICATION FLOW                               │
└─────────────────────────────────────────────────────────────────────────────┘

     Consumer App (cms.xynes.com)              Auth App (auth.xynes.com)
     ─────────────────────────────             ───────────────────────────
              │                                          │
              │  User not authenticated                  │
              │─────────────────────────────────────────▶│
              │  redirect to auth.xynes.com/login        │
              │  ?redirect=cms.xynes.com/dashboard       │
              │                                          │
              │                                          │  User logs in
              │                                          │  via Supabase
              │                                          │
              │                                          │  GET /me → bootstrap
              │                                          │
              │                                          │  workspaces.length === 0?
              │                                          │  → /onboarding
              │                                          │
              │◀─────────────────────────────────────────│
              │  redirect back with session cookie       │
              │  (shared .xynes.com domain)              │
              │                                          │
              │  @xynes/auth-sdk reads cookie            │
              │  useAuth() → user, workspaces            │
              │                                          │
              ▼                                          │
        [Dashboard]                                      │
```

### Why This Approach?

1. **Independent Repositories**: Each app has its own repo, CI/CD, deployment
2. **Versioned SDK**: `@xynes/auth-sdk` published to npm with semantic versioning
3. **Single Auth Entry Point**: All login/signup flows through `auth.xynes.com`
4. **Shared Session**: Cookie on `.xynes.com` domain works across all subdomains
5. **SDK for Integration**: Consumer apps use hooks for workspace context, user state
6. **No Monorepo Complexity**: Teams can work independently

---

## Modular Architecture

### Design Principles

The auth system is built with **maximum modularity** in mind:

| Principle | Implementation |
|-----------|----------------|
| **Plugin-based Routes** | Dynamic route registration via manifest |
| **Feature Flags** | Enable/disable auth features per consumer app |
| **Lazy Loading** | Code-split auth modules for performance |
| **Dependency Injection** | Swap implementations without code changes |

### Module Registry Pattern

```typescript
// @xynes/auth-sdk/src/core/module-registry.ts

export interface AuthModule {
  id: string;
  name: string;
  routes?: RouteConfig[];
  providers?: React.ComponentType[];
  hooks?: Record<string, unknown>;
  enabled: boolean;
}

export const MODULE_IDS = {
  CORE_AUTH: 'core-auth',        // Login, Signup, Logout
  WORKSPACE: 'workspace',        // Workspace CRUD, selection
  INVITE: 'invite',              // Invite system
  PASSWORD_RESET: 'password-reset',
  OAUTH_PROVIDERS: 'oauth-providers',
  SESSION_MANAGEMENT: 'session-management',
  SECURITY: 'security',          // Rate limiting UI, CSP, etc.
} as const;

class ModuleRegistry {
  private modules: Map<string, AuthModule> = new Map();
  
  register(module: AuthModule): void {
    this.modules.set(module.id, module);
  }
  
  get(id: string): AuthModule | undefined {
    return this.modules.get(id);
  }
  
  getEnabled(): AuthModule[] {
    return Array.from(this.modules.values()).filter(m => m.enabled);
  }
  
  getRoutes(): RouteConfig[] {
    return this.getEnabled().flatMap(m => m.routes ?? []);
  }
}

export const moduleRegistry = new ModuleRegistry();
```

### Feature Flags Configuration

```typescript
// @xynes/auth-sdk/src/config/feature-flags.ts

export interface AuthFeatureFlags {
  // Core Auth
  enableEmailAuth: boolean;
  enableOAuthGoogle: boolean;
  enableOAuthGitHub: boolean;
  enableOAuthApple: boolean;
  
  // Workspace Features
  enableWorkspaceCreation: boolean;
  enableWorkspaceSwitching: boolean;
  enableMultipleWorkspaces: boolean;
  
  // Invite System
  enableInvites: boolean;
  enableInviteRevocation: boolean;
  
  // Security
  enableMFA: boolean;
  enableSessionManagement: boolean;
  enableRateLimitUI: boolean;
  enableCSPReporting: boolean;
  
  // UX
  enableRememberMe: boolean;
  enablePasswordReset: boolean;
  enableProfileEdit: boolean;
}

export const DEFAULT_FLAGS: AuthFeatureFlags = {
  enableEmailAuth: true,
  enableOAuthGoogle: true,
  enableOAuthGitHub: true,
  enableOAuthApple: false,
  enableWorkspaceCreation: true,
  enableWorkspaceSwitching: true,
  enableMultipleWorkspaces: true,
  enableInvites: true,
  enableInviteRevocation: true,
  enableMFA: false,
  enableSessionManagement: false,
  enableRateLimitUI: true,
  enableCSPReporting: true,
  enableRememberMe: true,
  enablePasswordReset: true,
  enableProfileEdit: true,
};
```

### Dynamic Route Registration

```typescript
// @xynes/auth-sdk/src/router/dynamic-router.ts

export interface RouteConfig {
  path: string;
  component: React.LazyExoticComponent<React.ComponentType>;
  layout?: 'auth' | 'app' | 'minimal';
  guard?: 'public' | 'authenticated' | 'unauthenticated';
  preload?: boolean;
  featureFlag?: keyof AuthFeatureFlags;
}

// Routes are registered dynamically based on enabled modules
export const AUTH_ROUTES: RouteConfig[] = [
  // Core Auth Module
  {
    path: '/login',
    component: lazy(() => import('../pages/LoginPage')),
    layout: 'auth',
    guard: 'unauthenticated',
    preload: true,
  },
  {
    path: '/signup',
    component: lazy(() => import('../pages/SignupPage')),
    layout: 'auth',
    guard: 'unauthenticated',
    featureFlag: 'enableEmailAuth',
  },
  {
    path: '/logout',
    component: lazy(() => import('../pages/LogoutPage')),
    layout: 'minimal',
    guard: 'authenticated',
  },
  {
    path: '/callback',
    component: lazy(() => import('../pages/OAuthCallbackPage')),
    layout: 'minimal',
    guard: 'public',
  },
  
  // Workspace Module
  {
    path: '/onboarding',
    component: lazy(() => import('../pages/OnboardingPage')),
    layout: 'auth',
    guard: 'authenticated',
    featureFlag: 'enableWorkspaceCreation',
  },
  {
    path: '/workspaces',
    component: lazy(() => import('../pages/WorkspaceSelectorPage')),
    layout: 'app',
    guard: 'authenticated',
    featureFlag: 'enableWorkspaceSwitching',
  },
  
  // Invite Module
  {
    path: '/invite/:token',
    component: lazy(() => import('../pages/InvitePage')),
    layout: 'auth',
    guard: 'public',
    featureFlag: 'enableInvites',
  },
  
  // Password Reset Module
  {
    path: '/reset-password',
    component: lazy(() => import('../pages/ResetPasswordPage')),
    layout: 'auth',
    guard: 'unauthenticated',
    featureFlag: 'enablePasswordReset',
  },
  {
    path: '/reset-password/confirm',
    component: lazy(() => import('../pages/ResetPasswordConfirmPage')),
    layout: 'auth',
    guard: 'public',
    featureFlag: 'enablePasswordReset',
  },
];
```

### Lazy Loading Strategy

```typescript
// @xynes/auth-sdk/src/core/lazy-loader.ts

// Preload critical routes on app init
export function preloadCriticalRoutes(): void {
  const criticalRoutes = AUTH_ROUTES.filter(r => r.preload);
  criticalRoutes.forEach(route => {
    // Webpack magic comment for prefetch
    route.component.preload?.();
  });
}

// Lazy load modules on demand
export const AuthModules = {
  CoreAuth: lazy(() => import('../modules/core-auth')),
  Workspace: lazy(() => import('../modules/workspace')),
  Invite: lazy(() => import('../modules/invite')),
  Security: lazy(() => import('../modules/security')),
  PasswordReset: lazy(() => import('../modules/password-reset')),
};
```

### SDK Configuration with Feature Flags

```typescript
// Consumer app configuration
import { AuthProvider } from '@xynes/auth-sdk';

const authConfig = {
  supabaseUrl: process.env.NEXT_PUBLIC_SUPABASE_URL!,
  supabaseKey: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
  apiBaseUrl: process.env.NEXT_PUBLIC_API_URL!,
  authAppUrl: process.env.NEXT_PUBLIC_AUTH_APP_URL!,
  cookieDomain: '.xynes.com',
  
  // Feature flags for this consumer app
  features: {
    enableOAuthGoogle: true,
    enableOAuthGitHub: true,
    enableOAuthApple: false,        // Not enabled for CMS
    enableMFA: false,               // Phase 2
    enableSessionManagement: false, // Phase 2
    enableInvites: true,
    enableMultipleWorkspaces: true,
  },
  
  // Module overrides
  modules: {
    'core-auth': { enabled: true },
    'workspace': { enabled: true },
    'invite': { enabled: true },
    'security': { enabled: true },
  },
};

export function Providers({ children }) {
  return (
    <AuthProvider config={authConfig}>
      {children}
    </AuthProvider>
  );
}
```

---

## Sprint 1 Backlog

> **Sprint Goal:** Deliver secure, modular auth foundation with login/signup flows integrated into CMS Admin  
> **Capacity:** 2 developers × 2 weeks = ~40 story points  
> **Focus:** Security-first, modular architecture, CMS Admin integration

### Sprint Summary

| Epic | Stories | Points | Status |
|------|---------|--------|--------|
| AUTH-FE-1: Auth Core | 7 | 18 | 🟡 In Progress |
| AUTH-FE-2: Workspace | 4 | 10 | ⬜ Not Started |
| SEC-FE-1: Security | 5 | 12 | ⬜ Not Started |
| **Total** | **16** | **40** | |

### Sprint 1 Stories (Priority Order)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  WEEK 1: Foundation + Security                                               │
├─────────────────────────────────────────────────────────────────────────────┤
│  Day 1-2:  SDK Setup + Auth Provider + Security Module                      │
│  Day 3-4:  Login Page + OAuth + Secure Cookies                              │
│  Day 5:    Error Handling + Rate Limit UI                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│  WEEK 2: Features + Integration                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│  Day 6-7:  Onboarding + Workspace Creation                                  │
│  Day 8-9:  Workspace Selector + CMS Admin Integration                       │
│  Day 10:   Testing + Security Audit + Deploy                                │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Epic: AUTH-FE-1 — Authentication Core

> **Status:** 🟡 In Progress  
> **Total Points:** 18

### ✅ AUTH-FE-1.1 — New User Sign Up
**Status:** `COMPLETE` ✅  
**Points:** 5  
**Assignee:** —

Implementation complete. Email/password and OAuth (Google, GitHub) working.

---

### AUTH-FE-1.2 — SDK Project Setup
**Status:** `TODO`  
**Priority:** P0 — Sprint 1  
**Points:** 3  
**Assignee:** Dev 1

**As a** developer  
**I want** a properly configured SDK package  
**So that** I can build auth features on a solid foundation

**Acceptance Criteria:**
- [ ] Repository `xynes-auth-sdk` created with TypeScript
- [ ] tsup configured for ESM/CJS dual build
- [ ] Module registry pattern implemented
- [ ] Feature flags system in place
- [ ] Package exports configured (`@xynes/auth-sdk`)
- [ ] Unit test framework (Vitest) configured
- [ ] README with usage examples

**Technical Tasks:**
```bash
# Package structure
xynes-auth-sdk/
├── src/
│   ├── core/
│   │   ├── module-registry.ts
│   │   └── feature-flags.ts
│   ├── config/
│   │   └── index.ts
│   ├── types/
│   │   └── index.ts
│   └── index.ts
├── package.json
├── tsconfig.json
├── tsup.config.ts
└── vitest.config.ts
```

---

### AUTH-FE-1.3 — Auth Provider Implementation
**Status:** `TODO`  
**Priority:** P0 — Sprint 1  
**Points:** 3  
**Assignee:** Dev 1  
**Depends On:** AUTH-FE-1.2

**As a** consumer app developer  
**I want** an AuthProvider component  
**So that** I can wrap my app and access auth state everywhere

**Acceptance Criteria:**
- [ ] `AuthProvider` component with Supabase client
- [ ] Session state management (loading, authenticated, error)
- [ ] Automatic session refresh on expiry
- [ ] Context exposes user, session, loading state
- [ ] `useAuth()` hook for consuming auth state
- [ ] TypeScript types for all exports
- [ ] Unit tests for provider logic

**API Design:**
```typescript
// Usage
const { user, session, isLoading, isAuthenticated, error } = useAuth();
```

---

### AUTH-FE-1.4 — Login Page (Email)
**Status:** `TODO`  
**Priority:** P0 — Sprint 1  
**Points:** 2  
**Assignee:** Dev 2  
**Depends On:** AUTH-FE-1.3

**As a** returning user  
**I want to** log in with my email and password  
**So that** I can access my account

**Acceptance Criteria:**
- [ ] Login form with email/password fields
- [ ] Client-side validation (email format, password required)
- [ ] Loading state during submission
- [ ] Error display (invalid credentials, network error)
- [ ] "Forgot password" link (navigates to reset page)
- [ ] Redirect to `?redirect=` param or default route
- [ ] Form is accessible (labels, focus, keyboard nav)

**UI Wireframe:**
```
┌─────────────────────────────────────────┐
│           🔐 Welcome Back               │
│                                         │
│  Email                                  │
│  ┌─────────────────────────────────────┐│
│  │ user@example.com                    ││
│  └─────────────────────────────────────┘│
│                                         │
│  Password                               │
│  ┌─────────────────────────────────────┐│
│  │ ••••••••                            ││
│  └─────────────────────────────────────┘│
│  [Forgot password?]                     │
│                                         │
│  ┌─────────────────────────────────────┐│
│  │           Sign In →                 ││
│  └─────────────────────────────────────┘│
│                                         │
│  ─────────────── or ───────────────    │
│                                         │
│  [G] Continue with Google               │
│  [GH] Continue with GitHub              │
│                                         │
│  Don't have an account? [Sign up]       │
└─────────────────────────────────────────┘
```

---

### AUTH-FE-1.5 — OAuth Login (Google/GitHub)
**Status:** `TODO`  
**Priority:** P0 — Sprint 1  
**Points:** 3  
**Assignee:** Dev 2  
**Depends On:** AUTH-FE-1.3

**As a** user  
**I want to** log in with my Google or GitHub account  
**So that** I don't need to remember another password

**Acceptance Criteria:**
- [ ] "Continue with Google" button triggers OAuth flow
- [ ] "Continue with GitHub" button triggers OAuth flow
- [ ] OAuth callback page handles redirect from provider
- [ ] Session established after successful OAuth
- [ ] User bootstrapped via `GET /me` after OAuth
- [ ] OAuth errors displayed clearly
- [ ] Feature flag controls which providers are shown

**Technical Notes:**
- Use Supabase `signInWithOAuth({ provider: 'google' | 'github' })`
- Callback URL: `{AUTH_APP_URL}/callback`
- Store `redirect` param in sessionStorage before OAuth

---

### AUTH-FE-1.6 — OAuth Callback Handler
**Status:** `TODO`  
**Priority:** P0 — Sprint 1  
**Points:** 2  
**Assignee:** Dev 2  
**Depends On:** AUTH-FE-1.5

**As a** user completing OAuth  
**I want** the callback to be handled automatically  
**So that** I'm logged in seamlessly

**Acceptance Criteria:**
- [ ] `/callback` route extracts tokens from URL hash
- [ ] Supabase session established from OAuth tokens
- [ ] `GET /me` called to bootstrap user in accounts service
- [ ] Redirect to stored `redirect` URL or `/onboarding` (if new user)
- [ ] Error page shown if OAuth failed
- [ ] Loading state while processing

**Flow:**
```
Provider → /callback#access_token=xxx → Parse → Set Session → GET /me → Redirect
```

---

### AUTH-FE-1.7 — Logout Flow
**Status:** `TODO`  
**Priority:** P0 — Sprint 1  
**Points:** 1  
**Assignee:** Dev 1

**As a** logged-in user  
**I want to** log out of my account  
**So that** my session is terminated securely

**Acceptance Criteria:**
- [ ] `/logout` route clears Supabase session
- [ ] httpOnly cookie cleared server-side
- [ ] Local state cleared (workspace context, etc.)
- [ ] Redirect to login page
- [ ] Works from any consumer app (via redirect to auth app)

---

### AUTH-FE-1.8 — Auth Loading States
**Status:** `TODO`  
**Priority:** P1 — Sprint 1  
**Points:** 2  
**Assignee:** Dev 2

**As a** user  
**I want to** see loading indicators during auth operations  
**So that** I know the system is working

**Acceptance Criteria:**
- [ ] Full-page skeleton during initial auth check
- [ ] Button spinners during form submission
- [ ] Inline loading states for async validation
- [ ] Smooth transitions (no flash of wrong content)
- [ ] Accessible loading announcements (aria-live)

---

### AUTH-FE-1.9 — Auth Error Handling
**Status:** `TODO`  
**Priority:** P1 — Sprint 1  
**Points:** 2  
**Assignee:** Dev 1

**As a** user  
**I want to** see clear error messages when something goes wrong  
**So that** I can understand and fix the issue

**Acceptance Criteria:**
- [ ] Inline validation errors on form fields
- [ ] Toast notifications for API errors
- [ ] Specific error messages (not generic "Something went wrong")
- [ ] Network error detection with retry option
- [ ] Session expiry detection with re-login prompt
- [ ] Error boundary for unexpected crashes

**Error Types:**
| Error | User Message |
|-------|--------------|
| Invalid credentials | "Invalid email or password. Please try again." |
| Email already exists | "An account with this email already exists." |
| Weak password | "Password must be at least 8 characters." |
| Network error | "Unable to connect. Check your internet and try again." |
| Rate limited | "Too many attempts. Please wait 60 seconds." |
| Session expired | "Your session has expired. Please sign in again." |

---

## Epic: AUTH-FE-2 — Workspace Management

> **Status:** ⬜ Not Started  
> **Total Points:** 10

### AUTH-FE-2.1 — Workspace Provider
**Status:** `TODO`  
**Priority:** P0 — Sprint 1  
**Points:** 2  
**Assignee:** Dev 1  
**Depends On:** AUTH-FE-1.3

**As a** developer  
**I want** a WorkspaceProvider component  
**So that** I can access workspace state throughout the app

**Acceptance Criteria:**
- [ ] `WorkspaceProvider` component manages workspace context
- [ ] Stores selected workspace ID in secure cookie
- [ ] `useWorkspace()` hook for consuming workspace state
- [ ] Auto-selects workspace if user has only one
- [ ] Redirects to selector if multiple workspaces
- [ ] Clears workspace on logout

**API Design:**
```typescript
const { 
  currentWorkspace,  // Workspace | null
  workspaces,        // Workspace[]
  isLoading,         // boolean
  selectWorkspace,   // (id: string) => void
  clearWorkspace,    // () => void
} = useWorkspace();
```

---

### AUTH-FE-2.2 — Onboarding Page (Create Workspace)
**Status:** `TODO`  
**Priority:** P0 — Sprint 1  
**Points:** 3  
**Assignee:** Dev 2  
**Depends On:** AUTH-FE-2.1

**As a** new user with no workspaces  
**I want to** create my first workspace  
**So that** I can start using the platform

**Acceptance Criteria:**
- [ ] Friendly onboarding UI with clear instructions
- [ ] Workspace name input field
- [ ] Workspace slug input with auto-generation from name
- [ ] Live slug validation (format, availability)
- [ ] Slug format rules displayed
- [ ] Error handling for duplicate slugs (409)
- [ ] Success redirects to workspace dashboard
- [ ] Alternative: "Have an invite?" link

**Slug Validation:**
```typescript
// Rules
- 3-50 characters
- Lowercase letters, numbers, hyphens only
- Must start with a letter
- No consecutive hyphens
- Real-time availability check (debounced)
```

---

### AUTH-FE-2.3 — Workspace Selector Page
**Status:** `TODO`  
**Priority:** P0 — Sprint 1  
**Points:** 2  
**Assignee:** Dev 2  
**Depends On:** AUTH-FE-2.1

**As a** user with multiple workspaces  
**I want to** select which workspace to use  
**So that** I can switch between projects

**Acceptance Criteria:**
- [ ] List of user's workspaces from `GET /me`
- [ ] Each workspace shows name and slug
- [ ] Click to select and navigate to that workspace
- [ ] "Create new workspace" option at bottom
- [ ] Accessible keyboard navigation
- [ ] Empty state if no workspaces (shouldn't happen)

---

### AUTH-FE-2.4 — Workspace Switcher Component
**Status:** `TODO`  
**Priority:** P1 — Sprint 1  
**Points:** 3  
**Assignee:** Dev 1  
**Depends On:** AUTH-FE-2.1

**As a** user in a consumer app  
**I want** a dropdown to switch workspaces  
**So that** I don't need to go to a separate page

**Acceptance Criteria:**
- [ ] Dropdown component showing current workspace
- [ ] List of other workspaces on expand
- [ ] Click to switch (updates cookie, refreshes data)
- [ ] "Create new workspace" option
- [ ] Accessible (keyboard, screen reader)
- [ ] Exported from SDK for use in consumer apps

**Component Export:**
```typescript
// @xynes/auth-sdk
export { WorkspaceSwitcher } from './components/WorkspaceSwitcher';
```

---

## Epic: AUTH-FE-3 — Invite System

> **Status:** ⬜ Not Started — Sprint 2  
> **Total Points:** 8

### AUTH-FE-3.1 — Invite Preview Page
**Status:** `BACKLOG`  
**Priority:** P1 — Sprint 2  
**Points:** 2

**As a** user with an invite link  
**I want to** preview the invite details  
**So that** I know what workspace I'm joining

---

### AUTH-FE-3.2 — Invite Accept Flow (Authenticated)
**Status:** `BACKLOG`  
**Priority:** P1 — Sprint 2  
**Points:** 2

**As a** logged-in user viewing an invite  
**I want to** accept the invite with one click  
**So that** I can join the workspace immediately

---

### AUTH-FE-3.3 — Invite Accept Flow (Unauthenticated)
**Status:** `BACKLOG`  
**Priority:** P1 — Sprint 2  
**Points:** 2

**As a** user without an account viewing an invite  
**I want to** sign up and automatically accept the invite  
**So that** the flow is seamless

---

### AUTH-FE-3.4 — Invite Error States
**Status:** `BACKLOG`  
**Priority:** P1 — Sprint 2  
**Points:** 2

**As a** user with an invalid invite  
**I want to** see a clear error message  
**So that** I know what went wrong

---

## Epic: SEC-FE-1 — Security Hardening

> **Status:** ⬜ Not Started  
> **Total Points:** 12  
> **Priority:** P0 — MUST be completed in Sprint 1

### SEC-FE-1.1 — Secure Cookie Configuration
**Status:** `TODO`  
**Priority:** P0 — Sprint 1  
**Points:** 2  
**Assignee:** Dev 1

**As a** platform  
**I need** cookies configured securely  
**So that** sessions cannot be hijacked

**Acceptance Criteria:**
- [ ] Session cookie is `httpOnly` (not accessible via JS)
- [ ] Session cookie is `Secure` (HTTPS only)
- [ ] Session cookie has `SameSite=Lax` (CSRF protection)
- [ ] Cookie domain set to `.xynes.com` for subdomain sharing
- [ ] Cookie expiry aligns with Supabase session expiry
- [ ] Refresh token stored in separate httpOnly cookie

**Implementation:**
```typescript
const COOKIE_OPTIONS = {
  httpOnly: true,
  secure: process.env.NODE_ENV === 'production',
  sameSite: 'lax' as const,
  path: '/',
  domain: process.env.COOKIE_DOMAIN || '.xynes.com',
  maxAge: 60 * 60 * 24 * 7, // 7 days
};
```

---

### SEC-FE-1.2 — Secure Redirect Validation
**Status:** `TODO`  
**Priority:** P0 — Sprint 1  
**Points:** 2  
**Assignee:** Dev 1

**As a** platform  
**I need** redirect URLs validated  
**So that** users cannot be redirected to malicious sites

**Acceptance Criteria:**
- [ ] Whitelist of allowed redirect domains configured
- [ ] All `?redirect=` params validated against whitelist
- [ ] Invalid redirects fall back to default route
- [ ] Open redirect attempts logged for security monitoring
- [ ] URL parsing handles edge cases (encoded chars, etc.)

**Implementation:**
```typescript
const ALLOWED_DOMAINS = [
  'xynes.com',
  'localhost:3000',
  'localhost:3001',
];

function validateRedirectUrl(url: string): string | null {
  try {
    const parsed = new URL(url);
    const isAllowed = ALLOWED_DOMAINS.some(domain => 
      parsed.host === domain || parsed.host.endsWith(`.${domain}`)
    );
    return isAllowed ? url : null;
  } catch {
    return null;
  }
}
```

---

### SEC-FE-1.3 — CSRF Token Implementation
**Status:** `TODO`  
**Priority:** P0 — Sprint 1  
**Points:** 3  
**Assignee:** Dev 1

**As a** platform  
**I need** CSRF protection on state-changing requests  
**So that** malicious sites cannot perform actions on behalf of users

**Acceptance Criteria:**
- [ ] CSRF token generated on page load (server-side)
- [ ] Token included in all POST/PUT/DELETE requests
- [ ] Token validated on backend before processing
- [ ] Token regenerated after login (session fixation prevention)
- [ ] Works with SPA architecture (token in meta tag or header)

**Implementation:**
```typescript
// Middleware to inject CSRF token
export async function middleware(req: NextRequest) {
  const res = NextResponse.next();
  
  // Generate token if not present
  let csrfToken = req.cookies.get('csrf_token')?.value;
  if (!csrfToken) {
    csrfToken = crypto.randomUUID();
    res.cookies.set('csrf_token', csrfToken, {
      httpOnly: true,
      secure: true,
      sameSite: 'strict',
    });
  }
  
  // Expose for client via header
  res.headers.set('x-csrf-token', csrfToken);
  return res;
}
```

---

### SEC-FE-1.4 — Rate Limit UI Handling
**Status:** `TODO`  
**Priority:** P0 — Sprint 1  
**Points:** 2  
**Assignee:** Dev 2

**As a** user who triggered rate limiting  
**I want to** see a clear message and countdown  
**So that** I know when I can try again

**Acceptance Criteria:**
- [ ] Detect 429 responses from API
- [ ] Parse `Retry-After` header for cooldown duration
- [ ] Show user-friendly message with countdown timer
- [ ] Disable submit button during cooldown
- [ ] Auto-enable when cooldown expires
- [ ] Different messages for different rate limit types

**UI:**
```
┌──────────────────────────────────────────┐
│  ⚠️ Too Many Attempts                     │
│                                          │
│  Please wait 45 seconds before trying    │
│  again.                                  │
│                                          │
│  ┌────────────────────────────────────┐  │
│  │         Try Again (45s)            │  │
│  └────────────────────────────────────┘  │
└──────────────────────────────────────────┘
```

---

### SEC-FE-1.5 — Content Security Policy Setup
**Status:** `TODO`  
**Priority:** P0 — Sprint 1  
**Points:** 3  
**Assignee:** Dev 1

**As a** platform  
**I need** a strict Content Security Policy  
**So that** XSS attacks are mitigated

**Acceptance Criteria:**
- [ ] CSP headers configured in Next.js config
- [ ] Scripts restricted to self + trusted CDNs
- [ ] Styles restricted to self + inline (with nonce)
- [ ] Images restricted to self + trusted sources
- [ ] Frame ancestors restricted (clickjacking prevention)
- [ ] Report-uri configured for CSP violation monitoring
- [ ] Nonce-based inline scripts for Supabase

**Implementation:**
```typescript
// next.config.js
const securityHeaders = [
  {
    key: 'Content-Security-Policy',
    value: [
      "default-src 'self'",
      "script-src 'self' 'nonce-{NONCE}' https://cdn.supabase.io",
      "style-src 'self' 'unsafe-inline'",
      "img-src 'self' data: https:",
      "font-src 'self'",
      "connect-src 'self' https://*.supabase.co https://api.xynes.com",
      "frame-ancestors 'none'",
      "base-uri 'self'",
      "form-action 'self'",
      "report-uri /api/csp-report",
    ].join('; '),
  },
  {
    key: 'X-Frame-Options',
    value: 'DENY',
  },
  {
    key: 'X-Content-Type-Options',
    value: 'nosniff',
  },
  {
    key: 'Referrer-Policy',
    value: 'strict-origin-when-cross-origin',
  },
];
```

---

### SEC-FE-1.6 — Input Sanitization Utilities
**Status:** `TODO`  
**Priority:** P1 — Sprint 1  
**Points:** 2  
**Assignee:** Dev 2

**As a** developer  
**I need** input sanitization utilities  
**So that** user input is safe to display and process

**Acceptance Criteria:**
- [ ] Sanitize function for HTML content (DOMPurify)
- [ ] Escape function for rendering user content
- [ ] Validation schemas for all form inputs (Zod)
- [ ] Utilities exported from SDK
- [ ] Unit tests for edge cases (XSS payloads)

**Implementation:**
```typescript
// @xynes/auth-sdk/src/utils/sanitize.ts
import DOMPurify from 'dompurify';
import { z } from 'zod';

export const sanitizeHtml = (dirty: string): string => {
  return DOMPurify.sanitize(dirty, { ALLOWED_TAGS: [] });
};

export const emailSchema = z.string().email().max(255);
export const passwordSchema = z.string().min(8).max(128);
export const workspaceNameSchema = z.string().min(2).max(100).trim();
export const workspaceSlugSchema = z.string()
  .min(3).max(50)
  .regex(/^[a-z][a-z0-9-]*[a-z0-9]$/, 'Invalid slug format')
  .refine(s => !s.includes('--'), 'No consecutive hyphens');
```

---

### SEC-FE-1.7 — Security Headers Audit
**Status:** `TODO`  
**Priority:** P1 — Sprint 1  
**Points:** 1  
**Assignee:** Dev 1

**As a** platform  
**I need** all security headers properly configured  
**So that** common web vulnerabilities are mitigated

**Acceptance Criteria:**
- [ ] `Strict-Transport-Security` header (HSTS)
- [ ] `X-Frame-Options: DENY`
- [ ] `X-Content-Type-Options: nosniff`
- [ ] `Referrer-Policy: strict-origin-when-cross-origin`
- [ ] `Permissions-Policy` restricting sensitive APIs
- [ ] Verify with securityheaders.com score A+

---

## Technical Requirements

### Modular Package Structure: `@xynes/auth-sdk`

```
xynes-auth-sdk/
├── src/
│   ├── core/                          # 🔒 Core (always loaded)
│   │   ├── module-registry.ts         # Plugin registration
│   │   ├── feature-flags.ts           # Feature toggle system
│   │   └── config.ts                  # SDK configuration
│   │
│   ├── modules/                       # 📦 Lazy-loaded modules
│   │   ├── core-auth/                 # Login, Signup, Logout
│   │   │   ├── index.ts
│   │   │   ├── AuthProvider.tsx
│   │   │   ├── useAuth.ts
│   │   │   └── pages/
│   │   │       ├── LoginPage.tsx
│   │   │       ├── SignupPage.tsx
│   │   │       └── LogoutPage.tsx
│   │   │
│   │   ├── workspace/                 # Workspace CRUD
│   │   │   ├── index.ts
│   │   │   ├── WorkspaceProvider.tsx
│   │   │   ├── useWorkspace.ts
│   │   │   └── components/
│   │   │       ├── WorkspaceSelector.tsx
│   │   │       ├── WorkspaceSwitcher.tsx
│   │   │       └── WorkspaceCreator.tsx
│   │   │
│   │   ├── invite/                    # Invite system
│   │   │   ├── index.ts
│   │   │   ├── useInvite.ts
│   │   │   └── components/
│   │   │       ├── InvitePreview.tsx
│   │   │       └── InviteAcceptor.tsx
│   │   │
│   │   ├── password-reset/            # Password reset
│   │   │   ├── index.ts
│   │   │   └── pages/
│   │   │       ├── ResetRequestPage.tsx
│   │   │       └── ResetConfirmPage.tsx
│   │   │
│   │   └── security/                  # Security utilities
│   │       ├── index.ts
│   │       ├── csrf.ts
│   │       ├── sanitize.ts
│   │       ├── rate-limit-ui.ts
│   │       └── secure-redirect.ts
│   │
│   ├── api/                           # API client layer
│   │   ├── accounts-client.ts
│   │   ├── http-client.ts
│   │   └── interceptors/
│   │       ├── auth-interceptor.ts
│   │       ├── csrf-interceptor.ts
│   │       └── rate-limit-interceptor.ts
│   │
│   ├── router/                        # Dynamic routing
│   │   ├── dynamic-router.ts
│   │   ├── route-config.ts
│   │   └── guards/
│   │       ├── AuthGuard.tsx
│   │       ├── UnauthGuard.tsx
│   │       └── WorkspaceGuard.tsx
│   │
│   ├── components/                    # Shared UI components
│   │   ├── LoadingSpinner.tsx
│   │   ├── ErrorBoundary.tsx
│   │   ├── Toast.tsx
│   │   └── UserMenu.tsx
│   │
│   ├── utils/                         # Utilities
│   │   ├── storage.ts
│   │   ├── cookies.ts
│   │   └── validation.ts
│   │
│   ├── types/                         # TypeScript types
│   │   ├── index.ts
│   │   ├── user.ts
│   │   ├── workspace.ts
│   │   ├── invite.ts
│   │   └── config.ts
│   │
│   └── index.ts                       # Public exports
│
├── package.json
├── tsconfig.json
├── tsup.config.ts                     # Build: ESM + CJS
├── vitest.config.ts
└── README.md
```

### Public API Exports

```typescript
// @xynes/auth-sdk/src/index.ts

// ─────────────────────────────────────────────────────────────────
// CORE (always available)
// ─────────────────────────────────────────────────────────────────
export { createAuthConfig, type AuthConfig } from './core/config';
export { moduleRegistry, MODULE_IDS } from './core/module-registry';
export { type AuthFeatureFlags, DEFAULT_FLAGS } from './core/feature-flags';

// ─────────────────────────────────────────────────────────────────
// PROVIDERS
// ─────────────────────────────────────────────────────────────────
export { AuthProvider, useAuth, type AuthState } from './modules/core-auth';
export { WorkspaceProvider, useWorkspace, type WorkspaceState } from './modules/workspace';

// ─────────────────────────────────────────────────────────────────
// HOOKS (lazy-loaded internally)
// ─────────────────────────────────────────────────────────────────
export { useInvite } from './modules/invite';

// ─────────────────────────────────────────────────────────────────
// COMPONENTS (tree-shakeable)
// ─────────────────────────────────────────────────────────────────
export { WorkspaceSwitcher } from './modules/workspace/components/WorkspaceSwitcher';
export { WorkspaceSelector } from './modules/workspace/components/WorkspaceSelector';
export { UserMenu } from './components/UserMenu';
export { AuthGuard } from './router/guards/AuthGuard';
export { WorkspaceGuard } from './router/guards/WorkspaceGuard';
export { ErrorBoundary } from './components/ErrorBoundary';

// ─────────────────────────────────────────────────────────────────
// API CLIENT
// ─────────────────────────────────────────────────────────────────
export { createAccountsClient, type AccountsClient } from './api/accounts-client';

// ─────────────────────────────────────────────────────────────────
// SECURITY UTILITIES
// ─────────────────────────────────────────────────────────────────
export { 
  sanitizeHtml, 
  validateRedirectUrl,
  getCsrfToken,
} from './modules/security';

// ─────────────────────────────────────────────────────────────────
// VALIDATION SCHEMAS (Zod)
// ─────────────────────────────────────────────────────────────────
export {
  emailSchema,
  passwordSchema,
  workspaceNameSchema,
  workspaceSlugSchema,
} from './utils/validation';

// ─────────────────────────────────────────────────────────────────
// TYPES
// ─────────────────────────────────────────────────────────────────
export type { User, UserProfile } from './types/user';
export type { Workspace, WorkspaceMember } from './types/workspace';
export type { WorkspaceInvite, InviteStatus } from './types/invite';
```

### Hook APIs

```typescript
// ─────────────────────────────────────────────────────────────────
// useAuth() — Core authentication state
// ─────────────────────────────────────────────────────────────────
const { 
  // State
  user,              // User | null
  session,           // Session | null
  isLoading,         // boolean — initial check in progress
  isAuthenticated,   // boolean — user is logged in
  error,             // Error | null
  
  // Actions
  signOut,           // () => Promise<void>
  refreshSession,    // () => Promise<void>
  
  // Navigation helpers
  redirectToLogin,   // (returnUrl?: string) => void
  redirectToSignup,  // (returnUrl?: string) => void
} = useAuth();

// ─────────────────────────────────────────────────────────────────
// useWorkspace() — Workspace context
// ─────────────────────────────────────────────────────────────────
const {
  // State
  currentWorkspace,  // Workspace | null
  workspaces,        // Workspace[]
  isLoading,         // boolean
  error,             // Error | null
  
  // Actions
  selectWorkspace,   // (workspaceId: string) => void
  clearWorkspace,    // () => void
  refreshWorkspaces, // () => Promise<void>
} = useWorkspace();

// ─────────────────────────────────────────────────────────────────
// useInvite(token) — Invite resolution/acceptance
// ─────────────────────────────────────────────────────────────────
const {
  // State
  invite,           // InviteDetails | null
  isLoading,        // boolean
  error,            // Error | null
  status,           // 'idle' | 'loading' | 'resolved' | 'accepted' | 'error'
  
  // Actions
  acceptInvite,     // () => Promise<void>
  refetch,          // () => Promise<void>
} = useInvite(token);
```

### Consumer App Integration Pattern

```typescript
// ─────────────────────────────────────────────────────────────────
// CMS Admin App — src/app/layout.tsx
// ─────────────────────────────────────────────────────────────────
import { 
  AuthProvider, 
  WorkspaceProvider,
  createAuthConfig,
} from '@xynes/auth-sdk';

const authConfig = createAuthConfig({
  supabase: {
    url: process.env.NEXT_PUBLIC_SUPABASE_URL!,
    anonKey: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
  },
  api: {
    baseUrl: process.env.NEXT_PUBLIC_API_URL!,
  },
  auth: {
    appUrl: process.env.NEXT_PUBLIC_AUTH_APP_URL!,
    cookieDomain: '.xynes.com',
  },
  features: {
    enableOAuthGoogle: true,
    enableOAuthGitHub: true,
    enableWorkspaceCreation: true,
    enableInvites: true,
  },
});

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <AuthProvider config={authConfig}>
          <WorkspaceProvider>
            {children}
          </WorkspaceProvider>
        </AuthProvider>
      </body>
    </html>
  );
}

// ─────────────────────────────────────────────────────────────────
// Protected Page — src/app/(dashboard)/page.tsx
// ─────────────────────────────────────────────────────────────────
'use client';

import { useAuth, useWorkspace, AuthGuard, WorkspaceGuard } from '@xynes/auth-sdk';

export default function DashboardPage() {
  return (
    <AuthGuard fallback={<RedirectToLogin />}>
      <WorkspaceGuard fallback={<RedirectToWorkspaceSelector />}>
        <DashboardContent />
      </WorkspaceGuard>
    </AuthGuard>
  );
}

function DashboardContent() {
  const { user } = useAuth();
  const { currentWorkspace } = useWorkspace();
  
  return (
    <div>
      <h1>Welcome, {user?.displayName}</h1>
      <p>Workspace: {currentWorkspace?.name}</p>
    </div>
  );
}
```

---

## Security Considerations

### Environment Variables

```bash
# .env.example for apps consuming @xynes/auth-ui

# ─────────────────────────────────────────────────────────────────
# PUBLIC (exposed to browser - NEXT_PUBLIC_ prefix required)
# ─────────────────────────────────────────────────────────────────

# Supabase Project URL (safe to expose)
NEXT_PUBLIC_SUPABASE_URL=https://xxxx.supabase.co

# Supabase Anon Key (safe to expose - RLS protects data)
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# API Gateway URL
NEXT_PUBLIC_API_URL=https://api.xynes.com

# App URL (for redirects)
NEXT_PUBLIC_APP_URL=https://app.xynes.com

# ─────────────────────────────────────────────────────────────────
# SERVER-ONLY (never expose to browser)
# ─────────────────────────────────────────────────────────────────

# Supabase Service Role Key (DANGER: full DB access)
# Only use in server-side code (API routes, middleware)
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# JWT Secret for verifying tokens server-side
JWT_SECRET=your-super-secret-jwt-key

# Internal Service Token (for service-to-service auth)
INTERNAL_SERVICE_TOKEN=your-internal-token
```

### Security Checklist

| Concern | Mitigation |
|---------|------------|
| **XSS** | Use httpOnly cookies for session, sanitize all inputs |
| **CSRF** | Supabase uses SameSite cookies, add CSRF tokens for mutations |
| **Token Storage** | Never store tokens in localStorage; use httpOnly cookies |
| **Secret Exposure** | Only `NEXT_PUBLIC_*` vars in client bundle |
| **Session Hijacking** | Short token expiry, refresh token rotation |
| **Rate Limiting** | Backend enforces, frontend shows errors gracefully |
| **Email Enumeration** | Generic "check email" messages for password reset |

### Cookie Configuration

```typescript
// Recommended cookie settings for auth
const cookieOptions = {
  httpOnly: true,        // Not accessible via JavaScript
  secure: true,          // HTTPS only
  sameSite: 'lax',       // CSRF protection
  maxAge: 60 * 60 * 24 * 7, // 7 days
  path: '/',
  domain: '.xynes.com',  // Shared across subdomains
};
```

### Auth Middleware (Next.js Example)

```typescript
// middleware.ts
import { createMiddlewareClient } from '@supabase/auth-helpers-nextjs';
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export async function middleware(req: NextRequest) {
  const res = NextResponse.next();
  const supabase = createMiddlewareClient({ req, res });
  
  // Refresh session if expired
  const { data: { session } } = await supabase.auth.getSession();
  
  // Protect routes
  const protectedPaths = ['/dashboard', '/settings', '/workspaces'];
  const isProtected = protectedPaths.some(p => req.nextUrl.pathname.startsWith(p));
  
  if (isProtected && !session) {
    const loginUrl = new URL('/login', req.url);
    loginUrl.searchParams.set('redirect', req.nextUrl.pathname);
    return NextResponse.redirect(loginUrl);
  }
  
  return res;
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
};
```

---

## Environment Configuration

### Auth SDK Package (for consumers to configure)

```bash
# .env.example for apps using @xynes/auth-sdk

# ─────────────────────────────────────────────────────────────────
# PUBLIC (exposed to browser - NEXT_PUBLIC_ prefix required)
# ─────────────────────────────────────────────────────────────────

# Supabase Project URL (safe to expose)
NEXT_PUBLIC_SUPABASE_URL=https://xxxx.supabase.co

# Supabase Anon Key (safe to expose - RLS protects data)
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# API Gateway URL
NEXT_PUBLIC_API_URL=https://api.xynes.com

# Auth App URL (for redirects)
NEXT_PUBLIC_AUTH_APP_URL=https://auth.xynes.com

# This App's URL (for redirect callbacks)
NEXT_PUBLIC_APP_URL=https://cms.xynes.com
```

### Auth App (xynes-auth-app)

```bash
# .env.local for auth app (auth.xynes.com)

# ─────────────────────────────────────────────────────────────────
# PUBLIC
# ─────────────────────────────────────────────────────────────────
NEXT_PUBLIC_SUPABASE_URL=https://xxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
NEXT_PUBLIC_API_URL=https://api.xynes.com
NEXT_PUBLIC_APP_URL=https://auth.xynes.com

# Allowed redirect domains (security: only redirect to these)
NEXT_PUBLIC_ALLOWED_REDIRECT_DOMAINS=xynes.com,localhost:3000,localhost:3001

# ─────────────────────────────────────────────────────────────────
# SERVER-ONLY (never expose to browser)
# ─────────────────────────────────────────────────────────────────

# Supabase Service Role Key (DANGER: full DB access)
# Only use in server-side code (API routes, middleware)
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### NPM Package Publishing

```bash
# In xynes-auth-sdk repo

# .env (for local development/testing only)
# These are used when running the SDK's test suite

TEST_SUPABASE_URL=http://localhost:54321
TEST_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
TEST_API_URL=http://localhost:3000
```

### Per-Environment Configuration

| Environment | Auth App URL | API URL | Cookie Domain |
|-------------|--------------|---------|---------------|
| **Local Dev** | `http://localhost:3000` | `http://localhost:4000` | `localhost` |
| **Staging** | `https://auth.staging.xynes.com` | `https://api.staging.xynes.com` | `.staging.xynes.com` |
| **Production** | `https://auth.xynes.com` | `https://api.xynes.com` | `.xynes.com` |

### Secrets Management

| Environment | Approach |
|-------------|----------|
| Local Dev | `.env.local` (git-ignored) |
| CI/CD | GitHub Secrets / GitLab CI Variables |
| Production | AWS Secrets Manager / Doppler / Vault |

---

## Definition of Done

### Story Completion Checklist

Every story must meet these criteria before being marked complete:

**Code Quality:**
- [ ] Code passes TypeScript strict mode (no `any`)
- [ ] ESLint passes with zero warnings
- [ ] Prettier formatting applied
- [ ] No console.log statements (use proper logging)

**Testing:**
- [ ] Unit tests written for business logic (≥80% coverage)
- [ ] Integration tests for API calls
- [ ] Edge cases tested (error states, empty states)
- [ ] Manual QA on Chrome, Firefox, Safari

**Security:**
- [ ] No secrets in client bundle
- [ ] User input sanitized
- [ ] XSS vectors reviewed
- [ ] CSRF protection verified

**Accessibility:**
- [ ] Keyboard navigation works
- [ ] Screen reader compatible (ARIA labels)
- [ ] Color contrast meets WCAG AA
- [ ] Focus indicators visible

**Documentation:**
- [ ] JSDoc comments on exported functions
- [ ] README updated if API changed
- [ ] Changelog entry added

**Performance:**
- [ ] No unnecessary re-renders
- [ ] Bundle size impact reviewed
- [ ] Lighthouse score ≥90

---

## Sprint 2 Preview (Backlog)

> **Planned for:** Weeks 3-4  
> **Focus:** Invite system, Password reset, Profile management

| Story ID | Title | Points | Epic |
|----------|-------|--------|------|
| AUTH-FE-3.1 | Invite Preview Page | 2 | Invite |
| AUTH-FE-3.2 | Invite Accept (Authenticated) | 2 | Invite |
| AUTH-FE-3.3 | Invite Accept (Unauthenticated) | 2 | Invite |
| AUTH-FE-3.4 | Invite Error States | 2 | Invite |
| AUTH-FE-4.1 | Password Reset Request | 2 | Password |
| AUTH-FE-4.2 | Password Reset Confirm | 2 | Password |
| AUTH-FE-5.1 | User Profile Page | 3 | Profile |
| AUTH-FE-5.2 | User Menu Component | 2 | Profile |
| SEC-FE-1.8 | Session Expiry Handling | 2 | Security |
| SEC-FE-1.9 | Audit Logging (Client) | 3 | Security |
| **Total** | | **22** | |

---

## Repository Structure Summary

```
github.com/xynes/
│
├── auth-sdk/                    # NPM: @xynes/auth-sdk
│   ├── src/
│   │   ├── core/                # Module registry, feature flags
│   │   ├── modules/             # Lazy-loaded feature modules
│   │   ├── api/                 # HTTP client + interceptors
│   │   ├── router/              # Dynamic routing + guards
│   │   ├── components/          # Shared UI components
│   │   └── types/               # TypeScript definitions
│   ├── package.json
│   └── README.md
│
├── auth-app/                    # Next.js: auth.xynes.com
│   ├── src/app/
│   │   ├── login/
│   │   ├── signup/
│   │   ├── logout/
│   │   ├── callback/
│   │   ├── onboarding/
│   │   ├── workspaces/
│   │   ├── invite/[token]/
│   │   └── reset-password/
│   └── package.json             # depends on @xynes/auth-sdk
│
├── cms-admin/                   # Next.js: cms.xynes.com
│   └── package.json             # depends on @xynes/auth-sdk
│
└── (future apps...)
```

---

## Related Documentation

- [Accounts Service API Reference](./README.md)
- [CMS Core API Reference](../cms-core/README.md)
- [Supabase Auth Documentation](https://supabase.com/docs/guides/auth)
- [Next.js Auth Helpers](https://supabase.com/docs/guides/auth/auth-helpers/nextjs)
- [OWASP Authentication Cheatsheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
