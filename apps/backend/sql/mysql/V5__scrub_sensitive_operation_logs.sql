-- Older builds placed BCrypt password hashes in password-reset operation logs.
-- Keep the audit event while removing the credential material from existing rows.
UPDATE `system_operate_log`
SET `action` = '重置用户密码（历史敏感字段已清理）'
WHERE `action` LIKE CONCAT('%', CHAR(36), '2', '_', CHAR(36), '%');
