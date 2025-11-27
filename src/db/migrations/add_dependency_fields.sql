-- Migration: Add dependency tracking fields
-- Date: 2024-11-26
-- Description: Adds dependencies field to File table and dependency_graph field to Folder table

-- Add dependencies column to File table (JSON array of imported modules)
ALTER TABLE File ADD COLUMN IF NOT EXISTS dependencies JSONB DEFAULT '[]'::jsonb;

-- Add dependency_graph column to Folder table (Mermaid diagram string)
ALTER TABLE Folder ADD COLUMN IF NOT EXISTS dependency_graph TEXT;

-- Create an index on dependencies for faster queries (optional, for future use)
CREATE INDEX IF NOT EXISTS idx_file_dependencies ON File USING GIN (dependencies);
