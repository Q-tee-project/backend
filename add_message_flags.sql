ALTER TABLE auth_service.messages ADD COLUMN is_starred BOOLEAN DEFAULT FALSE;
ALTER TABLE auth_service.messages ADD COLUMN is_deleted BOOLEAN DEFAULT FALSE;
