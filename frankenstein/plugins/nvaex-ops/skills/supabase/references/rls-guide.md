# Row Level Security (RLS) Complete Guide

## What is RLS?

Row Level Security is PostgreSQL's built-in mechanism to restrict which rows a user can access. In Supabase, RLS is the primary way to secure your data because the client connects directly to PostgreSQL via PostgREST.

## How RLS Works in Supabase

1. Client sends request with JWT (contains `auth.uid()`, role, app_metadata)
2. PostgREST passes the JWT to PostgreSQL
3. PostgreSQL evaluates RLS policies using JWT claims
4. Only matching rows are returned/modified

## Enabling RLS

```sql
-- Enable RLS on a table (MUST do this — without it, table is open to anyone with the anon key)
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- Force RLS for table owners too (recommended for safety)
ALTER TABLE public.profiles FORCE ROW LEVEL SECURITY;
```

**WARNING**: A table WITHOUT RLS enabled is **open to everyone** with the anon key. Enabling RLS without any policies means "deny all" — no one can access the table except via service_role.

## Policy Syntax

```sql
CREATE POLICY "policy_name"
ON schema.table
FOR [ALL | SELECT | INSERT | UPDATE | DELETE]
TO [role1, role2, ...]  -- anon, authenticated, service_role
USING (condition)        -- Filter existing rows (SELECT, UPDATE, DELETE)
WITH CHECK (condition);  -- Validate new/modified rows (INSERT, UPDATE)
```

### USING vs WITH CHECK

| Operation | USING | WITH CHECK |
|-----------|-------|------------|
| SELECT    | ✅ Filters visible rows | N/A |
| INSERT    | N/A | ✅ Validates new rows |
| UPDATE    | ✅ Filters which rows can be updated | ✅ Validates the new values |
| DELETE    | ✅ Filters which rows can be deleted | N/A |
| ALL       | ✅ Applied to all reads | ✅ Applied to all writes (defaults to USING if omitted) |

## Common Policy Patterns

### 1. Owner-Based Access

```sql
-- Users can CRUD their own data
CREATE POLICY "owner_access"
ON public.todos
FOR ALL
TO authenticated
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);
```

### 2. Public Read, Owner Write

```sql
-- Anyone can read
CREATE POLICY "public_read"
ON public.posts
FOR SELECT
TO anon, authenticated
USING (published = true);

-- Only owner can modify
CREATE POLICY "owner_write"
ON public.posts
FOR ALL
TO authenticated
USING (auth.uid() = author_id)
WITH CHECK (auth.uid() = author_id);
```

### 3. Role-Based Access (Admin/User)

```sql
-- Set role in app_metadata (server-side only):
-- supabaseAdmin.auth.admin.updateUserById(userId, { app_metadata: { role: 'admin' } })

-- Admin full access
CREATE POLICY "admin_all"
ON public.orders
FOR ALL
TO authenticated
USING (auth.jwt() -> 'app_metadata' ->> 'role' = 'admin');

-- Regular users see only their orders
CREATE POLICY "user_own_orders"
ON public.orders
FOR SELECT
TO authenticated
USING (auth.uid() = customer_id);
```

### 4. Organization/Team-Based Access

```sql
-- Members of the same org can access
CREATE POLICY "org_member_access"
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

-- Only org admins can modify
CREATE POLICY "org_admin_write"
ON public.projects
FOR ALL
TO authenticated
USING (
  EXISTS (
    SELECT 1 FROM public.org_members
    WHERE org_members.org_id = projects.org_id
    AND org_members.user_id = auth.uid()
    AND org_members.role = 'admin'
  )
)
WITH CHECK (
  EXISTS (
    SELECT 1 FROM public.org_members
    WHERE org_members.org_id = projects.org_id
    AND org_members.user_id = auth.uid()
    AND org_members.role = 'admin'
  )
);
```

### 5. Time-Based Access

```sql
-- Only access active subscriptions
CREATE POLICY "active_subscription"
ON public.premium_content
FOR SELECT
TO authenticated
USING (
  EXISTS (
    SELECT 1 FROM public.subscriptions
    WHERE subscriptions.user_id = auth.uid()
    AND subscriptions.expires_at > now()
    AND subscriptions.status = 'active'
  )
);
```

### 6. Row-Level Sharing (Shared Access Lists)

```sql
-- Access if owner OR explicitly shared
CREATE POLICY "shared_access"
ON public.documents
FOR SELECT
TO authenticated
USING (
  auth.uid() = owner_id
  OR EXISTS (
    SELECT 1 FROM public.document_shares
    WHERE document_shares.document_id = documents.id
    AND document_shares.shared_with = auth.uid()
  )
);
```

## Security Helper Functions

Use `security definer` functions to encapsulate complex authorization logic:

```sql
-- Create a helper function (runs with elevated privileges)
CREATE OR REPLACE FUNCTION public.is_org_member(org_id uuid)
RETURNS boolean
LANGUAGE sql
SECURITY DEFINER
SET search_path = public
STABLE
AS $$
  SELECT EXISTS (
    SELECT 1 FROM org_members
    WHERE org_members.org_id = $1
    AND org_members.user_id = auth.uid()
  );
$$;

-- Use in policies (cleaner and reusable)
CREATE POLICY "org_access"
ON public.projects
FOR SELECT
TO authenticated
USING (public.is_org_member(org_id));
```

**Important for security definer functions:**
- ALWAYS set `search_path = public` to prevent search path injection
- ALWAYS mark as `STABLE` or `IMMUTABLE` when possible for performance
- Keep them minimal — they bypass RLS

## Performance Optimization

### 1. Index Policy Columns

```sql
-- If your policy uses user_id, index it
CREATE INDEX idx_todos_user_id ON public.todos(user_id);

-- For org-based policies
CREATE INDEX idx_org_members_user_org ON public.org_members(user_id, org_id);
CREATE INDEX idx_projects_org_id ON public.projects(org_id);
```

### 2. Use EXISTS Instead of IN

```sql
-- ❌ Slow — scans full subquery
USING (org_id IN (SELECT org_id FROM org_members WHERE user_id = auth.uid()))

-- ✅ Fast — stops at first match
USING (EXISTS (
  SELECT 1 FROM org_members
  WHERE org_members.org_id = projects.org_id
  AND org_members.user_id = auth.uid()
))
```

### 3. Avoid Function Calls in Hot Paths

```sql
-- ❌ Calls function for every row
USING (public.get_user_role() = 'admin')

-- ✅ Cache in a subquery or use JWT claims directly
USING (auth.jwt() -> 'app_metadata' ->> 'role' = 'admin')
```

### 4. Monitor Policy Performance

```sql
-- Check which policies exist
SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual, with_check
FROM pg_policies
WHERE schemaname = 'public';

-- Analyze query performance with RLS
EXPLAIN ANALYZE SELECT * FROM public.todos;
```

## Common Mistakes

### 1. Forgetting to Enable RLS
Tables without RLS are fully accessible to anyone with the anon key.

### 2. Using `user_metadata` for Authorization
```sql
-- ❌ DANGEROUS — users can modify their own user_metadata
USING (auth.jwt() -> 'user_metadata' ->> 'role' = 'admin')

-- ✅ SAFE — only server-side code can modify app_metadata
USING (auth.jwt() -> 'app_metadata' ->> 'role' = 'admin')
```

### 3. Overly Permissive Policies
```sql
-- ❌ Anyone authenticated can do anything
CREATE POLICY "too_broad" ON public.users FOR ALL TO authenticated USING (true);

-- ✅ Restrict to owner
CREATE POLICY "owner_only" ON public.users FOR ALL TO authenticated
USING (auth.uid() = id) WITH CHECK (auth.uid() = id);
```

### 4. Missing WITH CHECK on INSERT/UPDATE
```sql
-- ❌ Users can read their data but insert data pretending to be someone else
CREATE POLICY "read_own" ON public.profiles FOR ALL TO authenticated
USING (auth.uid() = user_id);
-- WITH CHECK defaults to USING, which is fine here, but be explicit for clarity

-- ✅ Explicit WITH CHECK
CREATE POLICY "own_data" ON public.profiles FOR ALL TO authenticated
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);
```

### 5. Not Restricting the `anon` Role
```sql
-- ❌ Anonymous users can read everything
CREATE POLICY "public" ON public.posts FOR SELECT USING (true);

-- ✅ Specify the role and add conditions
CREATE POLICY "public_published" ON public.posts FOR SELECT
TO anon, authenticated
USING (published = true AND deleted_at IS NULL);
```

## Debugging RLS Issues

### "Row not found" or empty results
1. Check RLS is enabled: `SELECT relrowsecurity FROM pg_class WHERE relname = 'tablename';`
2. Check policies exist: `SELECT * FROM pg_policies WHERE tablename = 'tablename';`
3. Verify JWT claims: `SELECT auth.uid(), auth.jwt();` (in SQL editor as authenticated user)

### "Permission denied"
1. Check the `TO` clause matches the user's role
2. Verify the policy operation (SELECT/INSERT/UPDATE/DELETE) matches
3. Test the policy condition manually with known values

### Policy not triggering
1. Ensure the policy is `PERMISSIVE` (default) not `RESTRICTIVE`
2. Multiple PERMISSIVE policies are OR'd together
3. RESTRICTIVE policies are AND'd with all permissive policies
