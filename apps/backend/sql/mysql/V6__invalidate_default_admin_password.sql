-- V1 is immutable and contains the old public bootstrap password hash.
-- Clear it before the application runner writes the operator-supplied value.
UPDATE `system_users`
SET `password` = ''
WHERE `id` = 1
  AND `password` LIKE '$2a$04$%';
