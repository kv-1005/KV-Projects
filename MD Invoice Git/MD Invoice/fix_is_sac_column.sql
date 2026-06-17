-- Quick fix: Add is_sac column to invoice table
-- Run this SQL directly in Railway PostgreSQL database console

-- For PostgreSQL (Railway)
ALTER TABLE invoice ADD COLUMN IF NOT EXISTS is_sac BOOLEAN DEFAULT FALSE;

-- Verify the column was added
SELECT column_name, data_type, column_default 
FROM information_schema.columns 
WHERE table_name = 'invoice' AND column_name = 'is_sac';

