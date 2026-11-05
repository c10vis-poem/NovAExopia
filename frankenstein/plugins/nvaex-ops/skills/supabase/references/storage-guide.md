# Supabase Storage Guide

## Architecture

Supabase Storage is built on top of PostgreSQL and S3-compatible object storage:
- Metadata stored in `storage.buckets` and `storage.objects` tables
- Files stored in S3-compatible storage
- Access controlled via RLS policies on `storage.objects`
- Supports resumable uploads (TUS protocol) for large files

## Bucket Types

### Public Buckets
- **Reads**: No authentication needed — files accessible via public URL
- **Writes**: Still require RLS policies — public doesn't mean writable by anyone
- Use for: profile pictures, public assets, blog images

### Private Buckets
- **All operations**: Require valid JWT and matching RLS policy
- Access files via signed URLs (temporary) or authenticated requests
- Use for: user documents, invoices, sensitive files

## Creating Buckets

### Via SQL Migration (Recommended)

```sql
-- Create a public bucket for avatars
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
  'avatars',
  'avatars',
  true,
  5242880,  -- 5MB limit
  ARRAY['image/jpeg', 'image/png', 'image/webp', 'image/gif']
);

-- Create a private bucket for documents
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
  'documents',
  'documents',
  false,
  52428800,  -- 50MB limit
  ARRAY['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
);
```

### Via Client SDK

```typescript
const { data, error } = await supabaseAdmin.storage.createBucket('avatars', {
  public: true,
  fileSizeLimit: 5242880,  // 5MB
  allowedMimeTypes: ['image/jpeg', 'image/png', 'image/webp'],
})
```

## Storage RLS Policies

### Key Functions

- `storage.foldername(name)` — Returns array of folder path segments
- `storage.filename(name)` — Returns the filename
- `storage.extension(name)` — Returns the file extension
- `bucket_id` — The bucket name
- `owner_id` — The UUID of the user who uploaded the file (auto-set by Supabase)

### Common Policy Patterns

#### 1. User-Specific Folders

```sql
-- Upload: users can only upload to their own folder
CREATE POLICY "user_upload"
ON storage.objects
FOR INSERT
TO authenticated
WITH CHECK (
  bucket_id = 'avatars'
  AND (storage.foldername(name))[1] = auth.uid()::text
);

-- Read: users can read their own files
CREATE POLICY "user_read"
ON storage.objects
FOR SELECT
TO authenticated
USING (
  bucket_id = 'avatars'
  AND (storage.foldername(name))[1] = auth.uid()::text
);

-- Delete: users can delete their own files
CREATE POLICY "user_delete"
ON storage.objects
FOR DELETE
TO authenticated
USING (
  bucket_id = 'avatars'
  AND (storage.foldername(name))[1] = auth.uid()::text
);

-- Update: users can update (overwrite) their own files
CREATE POLICY "user_update"
ON storage.objects
FOR UPDATE
TO authenticated
USING (
  bucket_id = 'avatars'
  AND (storage.foldername(name))[1] = auth.uid()::text
);
```

#### 2. Owner-Based Access (Using owner_id)

```sql
-- Read own files
CREATE POLICY "owner_read"
ON storage.objects
FOR SELECT
TO authenticated
USING (owner_id = auth.uid());

-- Delete own files
CREATE POLICY "owner_delete"
ON storage.objects
FOR DELETE
TO authenticated
USING (owner_id = auth.uid());
```

#### 3. Public Read, Authenticated Write

```sql
-- Anyone can read from public bucket
CREATE POLICY "public_read"
ON storage.objects
FOR SELECT
TO anon, authenticated
USING (bucket_id = 'public-assets');

-- Only authenticated users can upload
CREATE POLICY "auth_upload"
ON storage.objects
FOR INSERT
TO authenticated
WITH CHECK (bucket_id = 'public-assets');
```

#### 4. Organization-Based File Access

```sql
-- Org members can access org files
CREATE POLICY "org_file_access"
ON storage.objects
FOR SELECT
TO authenticated
USING (
  bucket_id = 'org-files'
  AND EXISTS (
    SELECT 1 FROM public.org_members
    WHERE org_members.org_id = (storage.foldername(name))[1]::uuid
    AND org_members.user_id = auth.uid()
  )
);
```

## File Operations

### Upload

```typescript
// Simple upload
const { data, error } = await supabase.storage
  .from('avatars')
  .upload(`${userId}/avatar.png`, file, {
    cacheControl: '3600',
    upsert: true,  // Overwrite if exists
    contentType: 'image/png',
  })

// Resumable upload (for large files > 6MB)
const { data, error } = await supabase.storage
  .from('documents')
  .upload(`${userId}/large-file.pdf`, file, {
    cacheControl: '3600',
    upsert: false,
    // Automatically uses TUS protocol for files > 6MB
  })
```

### Download

```typescript
// Download file
const { data, error } = await supabase.storage
  .from('documents')
  .download(`${userId}/report.pdf`)

// data is a Blob
```

### Get URLs

```typescript
// Public URL (only works for public buckets)
const { data } = supabase.storage
  .from('avatars')
  .getPublicUrl(`${userId}/avatar.png`)
// data.publicUrl

// Signed URL (works for private buckets, expires)
const { data, error } = await supabase.storage
  .from('documents')
  .createSignedUrl(`${userId}/report.pdf`, 3600) // 1 hour
// data.signedUrl

// Multiple signed URLs
const { data, error } = await supabase.storage
  .from('documents')
  .createSignedUrls([
    `${userId}/file1.pdf`,
    `${userId}/file2.pdf`,
  ], 3600)
```

### List Files

```typescript
const { data, error } = await supabase.storage
  .from('documents')
  .list(userId, {
    limit: 100,
    offset: 0,
    sortBy: { column: 'created_at', order: 'desc' },
  })
```

### Delete Files

```typescript
// Delete single file
const { data, error } = await supabase.storage
  .from('avatars')
  .remove([`${userId}/old-avatar.png`])

// Delete multiple files
const { data, error } = await supabase.storage
  .from('documents')
  .remove([
    `${userId}/file1.pdf`,
    `${userId}/file2.pdf`,
  ])
```

### Move/Copy Files

```typescript
// Move
const { data, error } = await supabase.storage
  .from('documents')
  .move('old/path/file.pdf', 'new/path/file.pdf')

// Copy
const { data, error } = await supabase.storage
  .from('documents')
  .copy('source/file.pdf', 'destination/file.pdf')
```

## Image Transformations

Supabase Storage supports on-the-fly image transformations for public buckets:

```typescript
const { data } = supabase.storage
  .from('avatars')
  .getPublicUrl(`${userId}/avatar.png`, {
    transform: {
      width: 200,
      height: 200,
      resize: 'cover',  // 'cover' | 'contain' | 'fill'
      quality: 80,
      format: 'origin',  // 'origin' | 'avif' | 'webp'
    }
  })
```

## Common Storage Mistakes

### 1. No File Size Limits
```sql
-- ❌ No limits — users can upload massive files
INSERT INTO storage.buckets (id, name, public) VALUES ('uploads', 'uploads', false);

-- ✅ Set limits
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES ('uploads', 'uploads', false, 10485760, ARRAY['image/jpeg', 'image/png', 'application/pdf']);
```

### 2. Missing Write Policies on Public Buckets
Public bucket = public reads, NOT public writes. You still need INSERT/UPDATE/DELETE policies.

### 3. Not Using User Folders
```typescript
// ❌ Flat structure — hard to manage access
await supabase.storage.from('avatars').upload('avatar.png', file)

// ✅ User-scoped folders — easy RLS
await supabase.storage.from('avatars').upload(`${user.id}/avatar.png`, file)
```

### 4. Not Validating File Types Client-Side
Always validate BOTH client-side (UX) and server-side (via `allowed_mime_types`):
```typescript
const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp']
if (!ALLOWED_TYPES.includes(file.type)) {
  throw new Error('Invalid file type')
}
```

### 5. Long-Lived Signed URLs
```typescript
// ❌ 30-day signed URL — too long
const { data } = await supabase.storage.from('docs').createSignedUrl('file.pdf', 2592000)

// ✅ Short-lived signed URL — generate on demand
const { data } = await supabase.storage.from('docs').createSignedUrl('file.pdf', 300) // 5 min
```

## Storage with Edge Functions

```typescript
// supabase/functions/process-upload/index.ts
import { createClient } from 'npm:@supabase/supabase-js'

Deno.serve(async (req) => {
  const supabase = createClient(
    Deno.env.get('SUPABASE_URL')!,
    Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
  )

  // Download file from storage
  const { data, error } = await supabase.storage
    .from('uploads')
    .download('path/to/file.pdf')

  if (error) throw error

  // Process the file...
  const processedData = await processFile(data)

  // Upload processed result
  await supabase.storage
    .from('processed')
    .upload('path/to/result.pdf', processedData)

  return new Response(JSON.stringify({ success: true }))
})
```

## Database Triggers for Storage Events

```sql
-- Auto-create a profile entry when user uploads an avatar
CREATE OR REPLACE FUNCTION handle_avatar_upload()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  UPDATE public.profiles
  SET avatar_url = NEW.name
  WHERE id = NEW.owner_id;
  RETURN NEW;
END;
$$;

CREATE TRIGGER on_avatar_upload
  AFTER INSERT ON storage.objects
  FOR EACH ROW
  WHEN (NEW.bucket_id = 'avatars')
  EXECUTE FUNCTION handle_avatar_upload();
```
