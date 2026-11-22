CREATE TABLE IF NOT EXISTS users (
    username VARCHAR(32) PRIMARY KEY,
    display_name VARCHAR(40) NOT NULL,
    role ENUM('reviewer','analyst','observer') NOT NULL,
    password_hash VARCHAR(220) NOT NULL
);
CREATE TABLE IF NOT EXISTS halls (
    code VARCHAR(12) PRIMARY KEY,
    name VARCHAR(40) NOT NULL,
    manager VARCHAR(40) NOT NULL,
    purpose VARCHAR(100) NOT NULL
);
CREATE TABLE IF NOT EXISTS instruments (
    code VARCHAR(12) PRIMARY KEY,
    name VARCHAR(40) NOT NULL,
    unit VARCHAR(12) NOT NULL
);
CREATE TABLE IF NOT EXISTS receipts (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    reference VARCHAR(32) NOT NULL UNIQUE,
    kind ENUM('loan','reversal') NOT NULL,
    original_id BIGINT UNIQUE,
    source VARCHAR(12) NOT NULL,
    destination VARCHAR(12) NOT NULL,
    instrument VARCHAR(12) NOT NULL,
    quantity INT NOT NULL CHECK (quantity > 0),
    effective_on DATE NOT NULL,
    signer VARCHAR(32) NOT NULL,
    note VARCHAR(200) NOT NULL,
    signature CHAR(64) NOT NULL,
    CHECK (source <> destination),
    CHECK ((kind='loan' AND original_id IS NULL) OR (kind='reversal' AND original_id IS NOT NULL)),
    FOREIGN KEY (original_id) REFERENCES receipts(id),
    FOREIGN KEY (source) REFERENCES halls(code),
    FOREIGN KEY (destination) REFERENCES halls(code),
    FOREIGN KEY (instrument) REFERENCES instruments(code),
    FOREIGN KEY (signer) REFERENCES users(username),
    INDEX receipt_period (effective_on, id)
);
CREATE TABLE IF NOT EXISTS plans (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    series VARCHAR(64) NOT NULL,
    version INT NOT NULL,
    start_on DATE NOT NULL,
    end_on DATE NOT NULL,
    instrument VARCHAR(12),
    created_by VARCHAR(32) NOT NULL,
    UNIQUE (series, version),
    FOREIGN KEY (instrument) REFERENCES instruments(code),
    FOREIGN KEY (created_by) REFERENCES users(username)
);
CREATE TABLE IF NOT EXISTS runs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    seed_key VARCHAR(32) UNIQUE,
    plan_id BIGINT NOT NULL,
    status ENUM('queued','done','failed') NOT NULL DEFAULT 'queued',
    snapshot JSON NOT NULL,
    result JSON,
    error VARCHAR(240),
    created_by VARCHAR(32) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    published_at DATETIME,
    published_by VARCHAR(32),
    FOREIGN KEY (plan_id) REFERENCES plans(id),
    FOREIGN KEY (created_by) REFERENCES users(username),
    FOREIGN KEY (published_by) REFERENCES users(username),
    INDEX run_queue (status, id)
);
CREATE TABLE IF NOT EXISTS audit_log (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    actor VARCHAR(32) NOT NULL,
    action VARCHAR(32) NOT NULL,
    target VARCHAR(96) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (actor) REFERENCES users(username)
);
