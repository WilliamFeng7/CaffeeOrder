-- V1 is immutable and seeded a publicly known password for imported users.
-- Force an explicit administrator configuration before the next import.
UPDATE infra_config
SET value = ''
WHERE config_key = 'system.user.init-password'
  AND value = 'admin123';
