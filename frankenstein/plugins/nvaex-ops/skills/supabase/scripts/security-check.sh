#!/bin/bash
# ============================================
# Supabase Security Check Script
# Scans a project for common Supabase security issues
# Usage: bash security-check.sh [project-dir]
# ============================================

set -euo pipefail

PROJECT_DIR="${1:-.}"
ISSUES_FOUND=0
WARNINGS_FOUND=0

RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color
BOLD='\033[1m'

echo ""
echo "${BOLD}🔒 Supabase Security Check${NC}"
echo "================================"
echo "Scanning: $PROJECT_DIR"
echo ""

# --- Helper functions ---
report_issue() {
  echo -e "${RED}❌ ISSUE:${NC} $1"
  if [ -n "${2:-}" ]; then
    echo "   File: $2"
  fi
  ISSUES_FOUND=$((ISSUES_FOUND + 1))
}

report_warning() {
  echo -e "${YELLOW}⚠️  WARNING:${NC} $1"
  if [ -n "${2:-}" ]; then
    echo "   File: $2"
  fi
  WARNINGS_FOUND=$((WARNINGS_FOUND + 1))
}

report_ok() {
  echo -e "${GREEN}✅${NC} $1"
}

# --- Check 1: Service role key in client-side code ---
echo "${BOLD}1. Checking for exposed service_role key...${NC}"

# Check for service_role in client-accessible files
CLIENT_FILES=$(find "$PROJECT_DIR" \
  -type f \( -name "*.tsx" -o -name "*.ts" -o -name "*.jsx" -o -name "*.js" -o -name "*.vue" -o -name "*.svelte" \) \
  ! -path "*/node_modules/*" \
  ! -path "*/.next/*" \
  ! -path "*/dist/*" \
  ! -path "*/build/*" \
  ! -path "*/supabase/functions/*" \
  ! -path "*/server/*" \
  ! -path "*/api/*" \
  2>/dev/null || true)

SERVICE_ROLE_EXPOSED=false
if [ -n "$CLIENT_FILES" ]; then
  while IFS= read -r file; do
    if grep -l "service_role\|SUPABASE_SERVICE_ROLE\|serviceRole" "$file" 2>/dev/null | grep -v "\.d\.ts$" > /dev/null 2>&1; then
      # Check if it's a server file (Next.js patterns)
      if ! echo "$file" | grep -qE "(server|api|middleware|route)\.(ts|js|tsx|jsx)$"; then
        report_issue "service_role key potentially exposed in client code" "$file"
        SERVICE_ROLE_EXPOSED=true
      fi
    fi
  done <<< "$CLIENT_FILES"
fi
if [ "$SERVICE_ROLE_EXPOSED" = false ]; then
  report_ok "No service_role key found in client-side code"
fi

# --- Check 2: NEXT_PUBLIC_ with service role ---
echo ""
echo "${BOLD}2. Checking environment variables...${NC}"

ENV_FILES=$(find "$PROJECT_DIR" -maxdepth 3 -name ".env*" ! -name ".env.example" ! -path "*/node_modules/*" 2>/dev/null || true)
ENV_ISSUE=false

if [ -n "$ENV_FILES" ]; then
  while IFS= read -r file; do
    if grep -qi "NEXT_PUBLIC.*SERVICE_ROLE\|VITE.*SERVICE_ROLE\|REACT_APP.*SERVICE_ROLE\|NUXT_PUBLIC.*SERVICE_ROLE" "$file" 2>/dev/null; then
      report_issue "service_role key in a public environment variable (exposed to browser!)" "$file"
      ENV_ISSUE=true
    fi
  done <<< "$ENV_FILES"
fi

# Check .env files are gitignored
if [ -f "$PROJECT_DIR/.gitignore" ]; then
  if ! grep -q "\.env" "$PROJECT_DIR/.gitignore" 2>/dev/null; then
    report_warning ".env files may not be gitignored"
    ENV_ISSUE=true
  fi
fi

if [ "$ENV_ISSUE" = false ]; then
  report_ok "Environment variables look properly configured"
fi

# --- Check 3: Supabase client initialization ---
echo ""
echo "${BOLD}3. Checking Supabase client setup...${NC}"

# Look for createClient calls
if [ -n "$CLIENT_FILES" ]; then
  ANON_KEY_FOUND=false
  while IFS= read -r file; do
    if grep -q "createClient\|createBrowserClient\|createServerClient" "$file" 2>/dev/null; then
      ANON_KEY_FOUND=true
      # Check if using @supabase/ssr for server components
      if echo "$file" | grep -qE "(server|middleware)" && ! grep -q "@supabase/ssr" "$file" 2>/dev/null; then
        report_warning "Server file uses createClient instead of @supabase/ssr" "$file"
      fi
    fi
  done <<< "$CLIENT_FILES"
  if [ "$ANON_KEY_FOUND" = true ]; then
    report_ok "Supabase client initialization found"
  fi
fi

# --- Check 4: Auth usage patterns ---
echo ""
echo "${BOLD}4. Checking authentication patterns...${NC}"

AUTH_ISSUES=false
if [ -n "$CLIENT_FILES" ]; then
  while IFS= read -r file; do
    # Check for getSession used for authorization (common mistake)
    if grep -q "getSession" "$file" 2>/dev/null; then
      # Check if it's used for auth decisions (not just display)
      if grep -A3 "getSession" "$file" 2>/dev/null | grep -qi "redirect\|authorized\|permission\|allow\|deny\|role\|admin" 2>/dev/null; then
        report_warning "getSession() may be used for authorization — use getUser() instead" "$file"
        AUTH_ISSUES=true
      fi
    fi

    # Check for user_metadata used for roles
    if grep -q "user_metadata.*role\|userMetadata.*role" "$file" 2>/dev/null; then
      report_issue "user_metadata used for role checks — use app_metadata instead (users can modify user_metadata)" "$file"
      AUTH_ISSUES=true
    fi
  done <<< "$CLIENT_FILES"
fi
if [ "$AUTH_ISSUES" = false ]; then
  report_ok "Authentication patterns look correct"
fi

# --- Check 5: SQL injection risks ---
echo ""
echo "${BOLD}5. Checking for SQL injection risks...${NC}"

SQL_ISSUES=false
if [ -n "$CLIENT_FILES" ]; then
  while IFS= read -r file; do
    # Check for string interpolation in .rpc() or raw SQL (template literals or concatenation)
    if grep -E '\.rpc\(.*`|\.sql\(.*`|\.rpc\(.*\$\{|\.rpc\(.*\+' "$file" 2>/dev/null; then
      report_issue "Potential SQL injection — string interpolation in database query" "$file"
      SQL_ISSUES=true
    fi
  done <<< "$CLIENT_FILES"
fi
if [ "$SQL_ISSUES" = false ]; then
  report_ok "No obvious SQL injection risks found"
fi

# --- Check 6: Supabase config ---
echo ""
echo "${BOLD}6. Checking Supabase project configuration...${NC}"

if [ -f "$PROJECT_DIR/supabase/config.toml" ]; then
  report_ok "supabase/config.toml found"

  # Check if email confirmation is enabled
  if grep -q "enable_confirmations = false" "$PROJECT_DIR/supabase/config.toml" 2>/dev/null; then
    report_warning "Email confirmations are disabled — enable for production"
  fi

  # Check JWT expiry
  if grep -q "jwt_expiry" "$PROJECT_DIR/supabase/config.toml" 2>/dev/null; then
    JWT_EXPIRY=$(grep "jwt_expiry" "$PROJECT_DIR/supabase/config.toml" | head -1 | grep -o '[0-9]*')
    if [ -n "$JWT_EXPIRY" ] && [ "$JWT_EXPIRY" -gt 86400 ]; then
      report_warning "JWT expiry is over 24 hours ($JWT_EXPIRY seconds) — consider shorter tokens"
    fi
  fi
else
  report_warning "No supabase/config.toml found — run 'supabase init'"
fi

# Check for migrations
if [ -d "$PROJECT_DIR/supabase/migrations" ]; then
  MIGRATION_COUNT=$(find "$PROJECT_DIR/supabase/migrations" -name "*.sql" 2>/dev/null | wc -l | tr -d ' ')
  report_ok "$MIGRATION_COUNT migration(s) found in supabase/migrations/"
else
  report_warning "No migrations directory found"
fi

# --- Check 7: TypeScript types ---
echo ""
echo "${BOLD}7. Checking type safety...${NC}"

TYPE_FILES=$(find "$PROJECT_DIR" -type f -name "*.ts" -path "*supabase*" \( -name "types.ts" -o -name "database.types.ts" -o -name "supabase.ts" \) ! -path "*/node_modules/*" 2>/dev/null || true)

if [ -n "$TYPE_FILES" ]; then
  report_ok "Generated Supabase types found"
else
  report_warning "No generated Supabase types found — run 'supabase gen types typescript'"
fi

# --- Summary ---
echo ""
echo "================================"
echo "${BOLD}Summary${NC}"
echo "================================"
if [ "$ISSUES_FOUND" -gt 0 ]; then
  echo -e "${RED}❌ $ISSUES_FOUND critical issue(s) found${NC}"
fi
if [ "$WARNINGS_FOUND" -gt 0 ]; then
  echo -e "${YELLOW}⚠️  $WARNINGS_FOUND warning(s) found${NC}"
fi
if [ "$ISSUES_FOUND" -eq 0 ] && [ "$WARNINGS_FOUND" -eq 0 ]; then
  echo -e "${GREEN}✅ No issues found — looking good!${NC}"
fi
echo ""

exit $ISSUES_FOUND
