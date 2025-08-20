-- Database schema for Kamehameha vulnerability scanner
-- Version 2.0: Optimized for enterprise features

CREATE DATABASE IF NOT EXISTS kamehameha_scanner;
USE kamehameha_scanner;

-- Drop tables if they exist to ensure a clean slate on re-creation
DROP TABLE IF EXISTS findings;
DROP TABLE IF EXISTS scans;
DROP TABLE IF EXISTS companies;

CREATE TABLE IF NOT EXISTS companies (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS scans (
    id INT AUTO_INCREMENT PRIMARY KEY,
    company_id INT NOT NULL,
    target_domain VARCHAR(255) NOT NULL,
    scan_datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('initializing', 'running', 'completed', 'failed') NOT NULL DEFAULT 'initializing',
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS findings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    scan_id INT NOT NULL,
    template_id VARCHAR(255) NOT NULL,
    name VARCHAR(512) NOT NULL,
    severity VARCHAR(50),
    host VARCHAR(512),
    matched_at VARCHAR(2048),
    ip VARCHAR(100),
    description TEXT,
    cvss_score FLOAT,
    recommendation TEXT,
    curl_command TEXT,
    -- Enterprise Features
    status VARCHAR(50) DEFAULT 'new', -- new, confirmed, false_positive, resolved
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (scan_id) REFERENCES scans(id) ON DELETE CASCADE
);
