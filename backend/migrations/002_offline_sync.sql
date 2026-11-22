CREATE TABLE IF NOT EXISTS sync_batches (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    note VARCHAR(200) NOT NULL DEFAULT '',
    created_by VARCHAR(32) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(username)
);
CREATE TABLE IF NOT EXISTS sync_items (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    batch_id BIGINT NOT NULL,
    line_no INT NOT NULL,
    reference VARCHAR(32) NOT NULL,
    kind ENUM('loan','reversal') NOT NULL,
    original_reference VARCHAR(32),
    source VARCHAR(12),
    destination VARCHAR(12),
    instrument VARCHAR(12),
    quantity INT,
    effective_on DATE NOT NULL,
    signer VARCHAR(32) NOT NULL,
    note VARCHAR(200) NOT NULL,
    content_hash CHAR(64) NOT NULL,
    status ENUM('posted','pending_original','conflict') NOT NULL,
    detail VARCHAR(200) NOT NULL DEFAULT '',
    receipt_id BIGINT,
    FOREIGN KEY (batch_id) REFERENCES sync_batches(id),
    FOREIGN KEY (receipt_id) REFERENCES receipts(id),
    INDEX sync_item_reference (reference),
    INDEX sync_item_waiting (original_reference, status),
    INDEX sync_item_status (status, id)
);
