INSERT INTO supported_languages (code, name) VALUES
	('en', 'English'), ('sn', 'Shona'), ('nd', 'Ndebele')
ON DUPLICATE KEY UPDATE name = VALUES(name), is_active = TRUE;

INSERT INTO communication_channels (code, name) VALUES
	('browser', 'Browser chat'), ('sms', 'SMS'), ('whatsapp', 'WhatsApp'), ('test', 'Test provider')
ON DUPLICATE KEY UPDATE name = VALUES(name), is_active = TRUE;

INSERT INTO users (phone_number, name, preferred_language)
VALUES ('0770000000', 'Development User', 'en')
ON DUPLICATE KEY UPDATE name = VALUES(name), preferred_language = VALUES(preferred_language);

INSERT INTO user_channels (user_id, channel_code, address, is_primary)
SELECT id, 'sms', phone_number, TRUE FROM users WHERE phone_number = '0770000000'
ON DUPLICATE KEY UPDATE is_primary = TRUE;
