-- Migration 002: Add Unified Conviction Engine columns
-- Safe to re-run (IF NOT EXISTS guard)
-- DO NOT modify 001_create_hisseler.sql

ALTER TABLE "stocks" ADD COLUMN IF NOT EXISTS "unified_score" INTEGER DEFAULT 0;
ALTER TABLE "stocks" ADD COLUMN IF NOT EXISTS "conviction"    VARCHAR(20) DEFAULT 'BRONZE';
