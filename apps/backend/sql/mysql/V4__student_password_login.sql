-- 学生端新增账号密码登录；密码只保存 BCrypt 哈希，原文不落库。
ALTER TABLE cafe_student
  ADD COLUMN password_hash varchar(100) NULL AFTER dingtalk_user_id;
