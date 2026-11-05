-- ============================================
-- Supabase RLS Audit Script
-- Run this in the Supabase SQL Editor to find
-- tables without RLS and review existing policies
-- ============================================

-- 1. Find ALL public tables and their RLS status
SELECT
  c.relname AS table_name,
  CASE WHEN c.relrowsecurity THEN '✅ Enabled' ELSE '❌ DISABLED' END AS rls_status,
  CASE WHEN c.relforcerowsecurity THEN '✅ Forced' ELSE '⚠️ Not forced' END AS rls_forced,
  COUNT(p.policyname) AS policy_count
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
LEFT JOIN pg_policies p ON p.tablename = c.relname AND p.schemaname = n.nspname
WHERE n.nspname = 'public'
  AND c.relkind = 'r'  -- regular tables only
GROUP BY c.relname, c.relrowsecurity, c.relforcerowsecurity
ORDER BY c.relrowsecurity ASC, c.relname;

-- 2. Find tables WITHOUT RLS (critical security issue)
SELECT
  c.relname AS "⚠️ TABLE WITHOUT RLS"
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = 'public'
  AND c.relkind = 'r'
  AND NOT c.relrowsecurity
ORDER BY c.relname;

-- 3. Find tables WITH RLS but NO policies (effectively blocks all access)
SELECT
  c.relname AS "⚠️ TABLE WITH RLS BUT NO POLICIES (blocks all access)"
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
LEFT JOIN pg_policies p ON p.tablename = c.relname AND p.schemaname = 'public'
WHERE n.nspname = 'public'
  AND c.relkind = 'r'
  AND c.relrowsecurity
  AND p.policyname IS NULL
ORDER BY c.relname;

-- 4. List ALL RLS policies with details
SELECT
  tablename,
  policyname,
  permissive,
  roles,
  cmd,
  qual AS "USING condition",
  with_check AS "WITH CHECK condition"
FROM pg_policies
WHERE schemaname = 'public'
ORDER BY tablename, policyname;

-- 5. Find overly permissive policies (USING true or WITH CHECK true)
SELECT
  tablename,
  policyname,
  cmd,
  roles,
  '⚠️ OVERLY PERMISSIVE' AS warning
FROM pg_policies
WHERE schemaname = 'public'
  AND (
    qual = 'true'
    OR with_check = 'true'
  )
ORDER BY tablename;

-- 6. Find policies that reference user_metadata (security risk)
SELECT
  tablename,
  policyname,
  cmd,
  qual,
  with_check,
  '❌ USES user_metadata (users can modify this!)' AS warning
FROM pg_policies
WHERE schemaname = 'public'
  AND (
    qual LIKE '%user_metadata%'
    OR with_check LIKE '%user_metadata%'
  );

-- 7. Check storage bucket configurations
SELECT
  id,
  name,
  public,
  file_size_limit,
  allowed_mime_types,
  CASE
    WHEN file_size_limit IS NULL THEN '⚠️ No size limit'
    ELSE '✅ ' || (file_size_limit / 1048576)::text || 'MB limit'
  END AS size_check,
  CASE
    WHEN allowed_mime_types IS NULL THEN '⚠️ No mime type restriction'
    ELSE '✅ Restricted'
  END AS mime_check
FROM storage.buckets
ORDER BY name;

-- 8. Check storage policies
SELECT
  tablename,
  policyname,
  cmd,
  roles,
  qual,
  with_check
FROM pg_policies
WHERE schemaname = 'storage'
ORDER BY tablename, policyname;

-- 9. Find columns used in RLS policies that lack indexes
-- (Manual review needed — this lists all indexes on public tables)
SELECT
  t.relname AS table_name,
  i.relname AS index_name,
  a.attname AS column_name
FROM pg_class t
JOIN pg_namespace n ON n.oid = t.relnamespace
JOIN pg_index ix ON t.oid = ix.indrelid
JOIN pg_class i ON i.oid = ix.indexrelid
JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(ix.indkey)
WHERE n.nspname = 'public'
  AND t.relkind = 'r'
ORDER BY t.relname, i.relname;
