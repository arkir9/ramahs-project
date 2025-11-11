#!/bin/bash
# Vercel Deployment Fix Script
# Run this after authenticating with: vercel login

# Don't exit on errors - we want to continue diagnostics
set +e

echo "=== Vercel Deployment Diagnostic Script ==="
echo ""

# Check authentication
echo "1. Checking authentication..."
vercel whoami || {
    echo "❌ Not authenticated. Please run: vercel login"
    exit 1
}
echo "✅ Authenticated"
echo ""

# List teams
echo "2. Listing available teams..."
vercel teams ls
echo ""

# Check current project link
echo "3. Checking project link..."
if [ -d ".vercel" ]; then
    echo "✅ Project is linked"
    cat .vercel/project.json 2>/dev/null || echo "⚠️  Project config exists but may be incomplete"
else
    echo "⚠️  Project not linked. Run: vercel link"
fi
echo ""

# List projects
echo "4. Listing projects..."
vercel projects ls
echo ""

# List recent deployments
echo "5. Listing recent deployments..."
if [ -d ".vercel" ] && [ -f ".vercel/project.json" ]; then
    # If project is linked, list deployments for this project
    vercel deployments ls 2>&1 | head -20 || echo "⚠️  Could not list deployments"
else
    echo "⚠️  Project not linked. Link project first to see deployments."
    echo "   Run: vercel link"
fi
echo ""

# Check for environment variables
echo "6. Checking for Vercel environment variables..."
if [ -n "$VERCEL_TOKEN" ]; then
    echo "✅ VERCEL_TOKEN is set"
else
    echo "⚠️  VERCEL_TOKEN not set (optional if using CLI auth)"
fi

if [ -n "$VERCEL_ORG_ID" ]; then
    echo "✅ VERCEL_ORG_ID is set: $VERCEL_ORG_ID"
else
    echo "⚠️  VERCEL_ORG_ID not set"
fi

if [ -n "$VERCEL_PROJECT_ID" ]; then
    echo "✅ VERCEL_PROJECT_ID is set: $VERCEL_PROJECT_ID"
else
    echo "⚠️  VERCEL_PROJECT_ID not set"
fi
echo ""

echo "=== Diagnostic Complete ==="
echo ""
echo "Next steps:"
echo "1. If project not linked: vercel link"
echo "2. To deploy: vercel deploy"
echo "3. To list deployments: vercel deployments ls"
echo "4. To get specific deployment: vercel deployments get <deployment-id>"

