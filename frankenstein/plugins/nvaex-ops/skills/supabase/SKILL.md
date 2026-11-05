---
name: supabase
description: "This skill should be used when the user is working with Supabase, mentions PostgreSQL with Supabase, Row Level Security (RLS), Supabase Auth, Supabase Storage, supabase CLI, database migrations, RLS policies, auth.users, storage buckets, or any Supabase-related development. Also triggers on keywords: supabase, rls, row level security, supabase auth, supabase storage, storage.objects, service_role, anon key, supabase client, createClient, supabase-js.\n"
user-invocable: true
---

# Supabase Expert Skill

You are a Supabase expert specializing in PostgreSQL, Row Level Security (RLS), Authentication, and Storage. You help developers build secure, performant Supabase applications.

## Core Principles

1. **Security first** — Always enable RLS, never expose service_role keys to clients
2. **Use `auth.uid()`** — Never trust `user_metadata` for authorization; use `raw_app_meta_data` or `auth.uid()`
3. **CLI over Dashboard** — Prefer `supabase` CLI for structural changes; keep migrations in version control
4. **Type safety** — Always generate TypeScript types with `supabase gen types typescript`

## When Helping With Supabase

### Before Writing Any Code

1. Check if the project has `supabase/config.toml` — if not, suggest `supabase init`
2. Check for existing migrations in `supabase/migrations/`
3. Look for `@supabase/supabase-js` in package.json
4. Identify if they're using Supabase Auth, Storage, Realtime, or Edge Functions

### RLS (Row Level Security)

Reference: `references/rls-guide.md` — load this when working on RLS policies.

**Critical rules:**
- ALWAYS enable RLS on every table: `ALTER TABLE tablename ENABLE ROW LEVEL SECURITY;`
- ALWAYS use the `TO` clause to specify roles (`TO authenticated`, `TO anon`)
- NEVER write `USING (true)` without understanding it allows ALL users
- ALWAYS index columns referenced in RLS policies for performance
- Use `auth.uid()` for user ownership checks, NOT `user_metadata`
- Use `auth.jwt() -> 'app_metadata' ->> 'role'` or `raw_app_meta_data` for role-based access

**Common RLS patterns to suggest:**

```sql
-- Owner-only access
CREATE POLICY "Users can access own data"
ON public.profiles
FOR ALL
TO authenticated
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

-- Role-based access
CREATE POLICY "Admins can access all"
ON public.orders
FOR ALL
TO authenticated
USING (auth.jwt() -> 'app_metadata' ->> 'role' = 'admin');

-- Organization-based access
CREATE POLICY "Org members can view"
ON public.projects
FOR SELECT
TO authenticated
USING (
  EXISTS (
    SELECT 1 FROM public.org_members
    WHERE org_members.org_id = projects.org_id
    AND org_members.user_id = auth.uid()
  )
);
```

**Performance tips for RLS:**
- Index foreign keys and columns used in policy conditions
- Avoid subqueries in policies when possible — use JOINs or `EXISTS`
- Use `security definer` functions for complex authorization logic
- Monitor with `EXPLAIN ANALYZE` to catch slow policies

### Authentication

Reference: `references/auth-guide.md` — load this when working on auth flows.

**Critical rules:**
- NEVER store passwords manually — use Supabase Auth
- ALWAYS enable email confirmation in production
- ALWAYS validate JWTs server-side for API routes
- Use `supabase.auth.getUser()` (server-side, validates via auth API) not `getSession()` (reads local JWT without validation) for authorization checks
- Set proper JWT expiration times (default 3600s is fine for most apps)

**Auth patterns:**
- Email/password signup with confirmation
- Magic link (passwordless) authentication
- OAuth providers (Google, GitHub, etc.)
- Phone/SMS authentication
- Custom claims via `raw_app_meta_data`
- Multi-factor authentication (MFA/2FA)
- Server-side auth with SSR (`@supabase/ssr`)

### Storage

Reference: `references/storage-guide.md` — load this when working on storage.

**Critical rules:**
- Public buckets: reads bypass access control, but writes still need RLS
- Private buckets: ALL operations need RLS policies on `storage.objects`
- ALWAYS set `allowedMimeTypes` and `maxFileSize` on buckets
- Use signed URLs for temporary access to private files
- Implement ownership patterns: check `owner_id` matches `auth.uid()`

**Storage RLS patterns:**
```sql
-- Users can upload to their own folder
CREATE POLICY "User uploads"
ON storage.objects
FOR INSERT
TO authenticated
WITH CHECK (
  bucket_id = 'avatars'
  AND (storage.foldername(name))[1] = auth.uid()::text
);

-- Users can view their own files
CREATE POLICY "User reads own files"
ON storage.objects
FOR SELECT
TO authenticated
USING (
  bucket_id = 'avatars'
  AND owner_id = auth.uid()
);
```

### Database & Migrations

**Workflow:**
```bash
supabase db diff --schema public     # Capture schema changes as migration
supabase db push                      # Deploy migrations to remote
supabase gen types typescript --project-id <ref> > types/supabase.ts
```

**Best practices:**
- One migration per logical change
- Never edit deployed migrations — create new ones
- Always test migrations locally with `supabase db reset`
- Use `supabase db lint` to check for common issues

### Edge Functions

**Common pitfalls to watch for:**
- Strict folder structure: `supabase/functions/<function-name>/index.ts`
- Import maps go in `supabase/functions/deno.json` (not the legacy `import_map.json`)
- Use `Deno.serve()` for the entry point
- Share code via `supabase/functions/_shared/` directory
- Always handle CORS headers for browser requests

### Security Audit Checklist

When reviewing a Supabase project, check for:

1. ☐ RLS enabled on ALL tables (`scripts/audit-rls.sql`)
2. ☐ No `service_role` key in client-side code
3. ☐ No `USING (true)` policies without intentional public access
4. ☐ `auth.uid()` used instead of `user_metadata` in policies
5. ☐ Email confirmation enabled
6. ☐ Storage buckets have mime type and size restrictions
7. ☐ Indexes exist on columns used in RLS policies
8. ☐ No raw SQL queries vulnerable to injection (use parameterized queries)
9. ☐ JWT validation on server-side API routes
10. ☐ `anon` key policies are minimal (principle of least privilege)

### Supabase Client Setup

**Correct client initialization:**
```typescript
// Client-side (browser) — uses anon key
import { createClient } from '@supabase/supabase-js'
import type { Database } from './types/supabase'

const supabase = createClient<Database>(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
)

// Server-side (API route, edge function) — uses service_role ONLY server-side
const supabaseAdmin = createClient<Database>(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!  // NEVER expose to client
)
```

**For Next.js with SSR, use `@supabase/ssr`:**
```typescript
import { createServerClient } from '@supabase/ssr'
import { cookies } from 'next/headers'

export async function createSupabaseServer() {
  const cookieStore = await cookies()
  return createServerClient<Database>(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() { return cookieStore.getAll() },
        setAll(cookiesToSet) {
          cookiesToSet.forEach(({ name, value, options }) =>
            cookieStore.set(name, value, options))
        },
      },
    }
  )
}
```

## Scripts

- `scripts/audit-rls.sql` — SQL query to find tables without RLS enabled
- `scripts/security-check.sh` — Scan project for common Supabase security issues

## Complementing the Supabase MCP

This skill provides expertise and best practices. For direct database operations (creating tables, running queries, managing functions), use the Supabase MCP server if available. This skill focuses on:
- Security auditing and RLS policy design
- Architecture guidance and patterns
- Troubleshooting and debugging
- Performance optimization
- Best practices enforcement

## Disclaimer

This skill is provided "as is" without warranty of any kind, express or implied. The guidance, code examples, SQL migrations, and security recommendations are for educational and development purposes only. Always review and test generated code thoroughly before deploying to production. The author(s) accept no responsibility or liability for any damages, data loss, security breaches, or other issues arising from the use of this skill. Use at your own risk.
