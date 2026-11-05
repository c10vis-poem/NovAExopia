# Supabase Authentication Guide

## Architecture Overview

Supabase Auth (GoTrue) handles:
- User registration and login (email, phone, OAuth, magic link)
- JWT token issuance and refresh
- Session management
- Multi-factor authentication (MFA)
- Server-side rendering (SSR) support via `@supabase/ssr`

## Auth Methods

### Email/Password

```typescript
// Sign up
const { data, error } = await supabase.auth.signUp({
  email: 'user@example.com',
  password: 'secure-password-here',
  options: {
    data: {
      full_name: 'John Doe',  // Goes to user_metadata (user-editable)
    }
  }
})

// Sign in
const { data, error } = await supabase.auth.signInWithPassword({
  email: 'user@example.com',
  password: 'secure-password-here',
})

// Sign out
await supabase.auth.signOut()
```

### Magic Link (Passwordless)

```typescript
const { data, error } = await supabase.auth.signInWithOtp({
  email: 'user@example.com',
  options: {
    emailRedirectTo: 'https://yourapp.com/auth/callback',
  }
})
```

### OAuth (Google, GitHub, etc.)

```typescript
const { data, error } = await supabase.auth.signInWithOAuth({
  provider: 'google',
  options: {
    redirectTo: 'https://yourapp.com/auth/callback',
    queryParams: {
      access_type: 'offline',
      prompt: 'consent',
    }
  }
})
```

### Phone/SMS

```typescript
// Send OTP
const { data, error } = await supabase.auth.signInWithOtp({
  phone: '+1234567890',
})

// Verify OTP
const { data, error } = await supabase.auth.verifyOtp({
  phone: '+1234567890',
  token: '123456',
  type: 'sms',
})
```

## Session Management

### Client-Side

```typescript
// Get current session (reads from local storage/cookie — no DB call)
const { data: { session } } = await supabase.auth.getSession()

// Get current user (makes a DB call — use for authorization)
const { data: { user } } = await supabase.auth.getUser()

// Listen to auth state changes
const { data: { subscription } } = supabase.auth.onAuthStateChange(
  (event, session) => {
    // event: 'SIGNED_IN' | 'SIGNED_OUT' | 'TOKEN_REFRESHED' | 'USER_UPDATED' | 'PASSWORD_RECOVERY'
    console.log(event, session)
  }
)

// Cleanup
subscription.unsubscribe()
```

### CRITICAL: getSession() vs getUser()

```typescript
// ❌ INSECURE for authorization — reads JWT without validating
const { data: { session } } = await supabase.auth.getSession()
if (session) { /* user might have a stale/tampered token */ }

// ✅ SECURE for authorization — validates token against the database
const { data: { user } } = await supabase.auth.getUser()
if (user) { /* confirmed valid user */ }
```

**Rule**: Use `getSession()` only for reading non-sensitive session data (like displaying UI). Use `getUser()` for any authorization decision.

## Server-Side Auth (SSR)

### Next.js App Router Setup

```typescript
// lib/supabase/server.ts
import { createServerClient } from '@supabase/ssr'
import { cookies } from 'next/headers'

export async function createClient() {
  const cookieStore = await cookies()
  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return cookieStore.getAll()
        },
        setAll(cookiesToSet) {
          try {
            cookiesToSet.forEach(({ name, value, options }) =>
              cookieStore.set(name, value, options)
            )
          } catch {
            // Called from Server Component — ignore
          }
        },
      },
    }
  )
}
```

### Middleware for Auth Protection

```typescript
// middleware.ts
import { createServerClient } from '@supabase/ssr'
import { NextResponse, type NextRequest } from 'next/server'

export async function middleware(request: NextRequest) {
  let supabaseResponse = NextResponse.next({ request })

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return request.cookies.getAll()
        },
        setAll(cookiesToSet) {
          cookiesToSet.forEach(({ name, value, options }) =>
            request.cookies.set(name, value)
          )
          supabaseResponse = NextResponse.next({ request })
          cookiesToSet.forEach(({ name, value, options }) =>
            supabaseResponse.cookies.set(name, value, options)
          )
        },
      },
    }
  )

  const { data: { user } } = await supabase.auth.getUser()

  if (!user && request.nextUrl.pathname.startsWith('/dashboard')) {
    const url = request.nextUrl.clone()
    url.pathname = '/login'
    return NextResponse.redirect(url)
  }

  return supabaseResponse
}

export const config = {
  matcher: ['/dashboard/:path*', '/api/:path*'],
}
```

### Auth Callback Route

```typescript
// app/auth/callback/route.ts
import { createClient } from '@/lib/supabase/server'
import { NextResponse } from 'next/server'

export async function GET(request: Request) {
  const { searchParams, origin } = new URL(request.url)
  const code = searchParams.get('code')
  const next = searchParams.get('next') ?? '/'

  if (code) {
    const supabase = await createClient()
    const { error } = await supabase.auth.exchangeCodeForSession(code)
    if (!error) {
      return NextResponse.redirect(`${origin}${next}`)
    }
  }

  return NextResponse.redirect(`${origin}/auth/error`)
}
```

## Custom Claims & Roles

### Setting Roles (Server-Side Only)

```typescript
// Use supabaseAdmin (service_role) — NEVER on client
const { data, error } = await supabaseAdmin.auth.admin.updateUserById(
  userId,
  {
    app_metadata: { role: 'admin' }  // Goes to raw_app_meta_data
  }
)
```

### Reading Roles in RLS

```sql
-- In RLS policies
auth.jwt() -> 'app_metadata' ->> 'role'

-- Example policy
CREATE POLICY "admin_only"
ON public.admin_settings
FOR ALL
TO authenticated
USING (auth.jwt() -> 'app_metadata' ->> 'role' = 'admin');
```

### Reading Roles in Application Code

```typescript
const { data: { user } } = await supabase.auth.getUser()
const role = user?.app_metadata?.role
```

## Multi-Factor Authentication (MFA)

```typescript
// Enroll MFA (TOTP)
const { data, error } = await supabase.auth.mfa.enroll({
  factorType: 'totp',
  friendlyName: 'My Authenticator App'
})
// data.totp.qr_code — show to user
// data.totp.uri — for manual entry

// Verify MFA challenge
const { data: challenge } = await supabase.auth.mfa.challenge({
  factorId: factor.id
})

const { data, error } = await supabase.auth.mfa.verify({
  factorId: factor.id,
  challengeId: challenge.id,
  code: '123456' // from authenticator app
})

// Check MFA status in RLS
// auth.jwt() -> 'aal' = 'aal2' means MFA verified
CREATE POLICY "mfa_required"
ON public.sensitive_data
FOR ALL
TO authenticated
USING (auth.jwt() ->> 'aal' = 'aal2');
```

## User Management (Admin)

```typescript
// List users (requires service_role)
const { data, error } = await supabaseAdmin.auth.admin.listUsers()

// Get user by ID
const { data, error } = await supabaseAdmin.auth.admin.getUserById(userId)

// Delete user
const { data, error } = await supabaseAdmin.auth.admin.deleteUser(userId)

// Invite user by email
const { data, error } = await supabaseAdmin.auth.admin.inviteUserByEmail(
  'newuser@example.com'
)
```

## Common Auth Mistakes

1. **Using `getSession()` for authorization** — always use `getUser()` server-side
2. **Not setting up auth callback route** — OAuth and magic links need `/auth/callback`
3. **Missing middleware** — SSR apps need middleware to refresh tokens
4. **Exposing service_role key** — NEVER in client code or environment variables prefixed with `NEXT_PUBLIC_`
5. **Not handling auth state changes** — use `onAuthStateChange` to react to login/logout
6. **Storing role in user_metadata** — users can modify this; use `app_metadata`
7. **Not enabling email confirmation** — allows fake email signups in production
8. **Missing PKCE flow for SSR** — use `@supabase/ssr`, not `@supabase/auth-helpers` (deprecated)

## Email Templates

Configure in Supabase Dashboard → Authentication → Email Templates:
- Confirm signup
- Magic link
- Change email
- Reset password

Custom SMTP recommended for production (Dashboard → Project Settings → Auth → SMTP).

## Rate Limiting

Supabase applies default rate limits:
- Sign up: 30/hour per IP
- Sign in: 30/hour per IP
- Token refresh: 360/hour per IP
- Magic links: 4/hour per email

Configure in Dashboard → Authentication → Rate Limits.
