CREATE TABLE IF NOT EXISTS supported_languages (
	code CHAR(2) PRIMARY KEY,
	name VARCHAR(40) NOT NULL,
	is_active BOOLEAN NOT NULL DEFAULT TRUE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS communication_channels (
	code VARCHAR(30) PRIMARY KEY,
	name VARCHAR(60) NOT NULL,
	is_active BOOLEAN NOT NULL DEFAULT TRUE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS users (
	id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
	phone_number VARCHAR(20) NOT NULL UNIQUE,
	name VARCHAR(120),
	preferred_language CHAR(2) NOT NULL DEFAULT 'en',
	due_date DATE,
	created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
	updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT fk_users_language FOREIGN KEY (preferred_language) REFERENCES supported_languages(code)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS user_channels (
	id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
	user_id BIGINT UNSIGNED NOT NULL,
	channel_code VARCHAR(30) NOT NULL,
	address VARCHAR(120) NOT NULL,
	is_primary BOOLEAN NOT NULL DEFAULT FALSE,
	created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
	UNIQUE KEY uq_user_channel_address (channel_code, address),
	CONSTRAINT fk_user_channels_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
	CONSTRAINT fk_user_channels_channel FOREIGN KEY (channel_code) REFERENCES communication_channels(code)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS pregnancy_profiles (
	id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
	user_id BIGINT UNSIGNED NOT NULL,
	last_menstrual_period DATE,
	due_date DATE,
	gravida TINYINT UNSIGNED,
	parity TINYINT UNSIGNED,
	notes TEXT,
	created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
	updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT fk_profiles_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS conversations (
	id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
	user_id BIGINT UNSIGNED,
	channel_code VARCHAR(30) NOT NULL,
	status ENUM('open', 'closed') NOT NULL DEFAULT 'open',
	started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
	last_message_at TIMESTAMP NULL,
	CONSTRAINT fk_conversations_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
	CONSTRAINT fk_conversations_channel FOREIGN KEY (channel_code) REFERENCES communication_channels(code)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS messages (
	id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
	conversation_id BIGINT UNSIGNED NOT NULL,
	user_id BIGINT UNSIGNED,
	direction ENUM('inbound', 'outbound') NOT NULL,
	language_code CHAR(2) NOT NULL DEFAULT 'en',
	message_text TEXT NOT NULL,
	created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
	CONSTRAINT fk_messages_conversation FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
	CONSTRAINT fk_messages_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
	CONSTRAINT fk_messages_language FOREIGN KEY (language_code) REFERENCES supported_languages(code)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS appointments (
	id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
	user_id BIGINT UNSIGNED NOT NULL,
	pregnancy_profile_id BIGINT UNSIGNED,
	appointment_type VARCHAR(40) NOT NULL DEFAULT 'anc',
	appointment_date DATE NOT NULL,
	status ENUM('scheduled', 'completed', 'cancelled') NOT NULL DEFAULT 'scheduled',
	reminder_sent BOOLEAN NOT NULL DEFAULT FALSE,
	created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
	updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT fk_appointments_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
	CONSTRAINT fk_appointments_profile FOREIGN KEY (pregnancy_profile_id) REFERENCES pregnancy_profiles(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS reminders (
	id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
	user_id BIGINT UNSIGNED NOT NULL,
	appointment_id BIGINT UNSIGNED,
	reminder_type VARCHAR(40) NOT NULL DEFAULT 'appointment',
	scheduled_for DATETIME NOT NULL,
	status ENUM('pending', 'sent', 'failed', 'cancelled') NOT NULL DEFAULT 'pending',
	sent_at DATETIME NULL,
	created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
	CONSTRAINT fk_reminders_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
	CONSTRAINT fk_reminders_appointment FOREIGN KEY (appointment_id) REFERENCES appointments(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS health_workers (
	id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
	name VARCHAR(120) NOT NULL,
	phone_number VARCHAR(20),
	email VARCHAR(160),
	active BOOLEAN NOT NULL DEFAULT TRUE,
	created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
	updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS escalations (
	id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
	user_id BIGINT UNSIGNED NOT NULL,
	conversation_id BIGINT UNSIGNED,
	assigned_health_worker_id BIGINT UNSIGNED,
	reason TEXT NOT NULL,
	severity ENUM('urgent', 'high', 'normal') NOT NULL DEFAULT 'urgent',
	status ENUM('open', 'in_progress', 'resolved') NOT NULL DEFAULT 'open',
	created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
	resolved_at TIMESTAMP NULL,
	CONSTRAINT fk_escalations_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
	CONSTRAINT fk_escalations_conversation FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE SET NULL,
	CONSTRAINT fk_escalations_worker FOREIGN KEY (assigned_health_worker_id) REFERENCES health_workers(id) ON DELETE SET NULL
) ENGINE=InnoDB;
