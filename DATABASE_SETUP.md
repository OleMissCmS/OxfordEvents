# Database Setup Guide

## Current Storage Status

**Images:**
- Stored in `static/images/cache/` (filesystem)
- Metadata in `data/team_logos.json` and `data/venue_images.json`

**Runtime Cache:**
- Flask-Caching with `SimpleCache` (in-memory, not persistent)

## Problem with Current Setup

On Render.com, the filesystem is **ephemeral** - data gets wiped on redeploy:
- ✅ Code persists (from Git)
- ❌ Images get deleted on redeploy
- ❌ JSON database files get deleted
- ❌ Cache is lost on restart

## Solutions

### Option 1: PostgreSQL Database (Recommended)

**Pros:**
- Persistent storage (survives redeploys)
- Fast queries
- Can store image metadata and binary data
- Works well with Flask

**Cons:**
- Requires setup on Render
- Need to migrate existing JSON data

### Option 2: Render Disk (Simple)

**Pros:**
- Persistent filesystem storage
- Minimal code changes needed
- Good for image files

**Cons:**
- Limited storage (1GB free)
- Slower than database
- Still need database for metadata queries

### Option 3: Cloud Storage (S3/Cloudinary)

**Pros:**
- Scales well
- Fast CDN
- Handles images well

**Cons:**
- Requires external service
- Costs money at scale

## Recommended: PostgreSQL Setup

If you want me to set up PostgreSQL, I can:

1. Add PostgreSQL support to the code
2. Create database schema for:
   - Team logos metadata
   - Venue images metadata
   - Generated image cache
3. Migrate existing JSON data
4. Update Render configuration

This will make your storage persistent and much faster!

