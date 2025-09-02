-- Database schema for Kamehameha vulnerability scanner
-- Version 2.1: Fixed to match actual code implementation

CREATE DATABASE IF NOT EXISTS kamehameha_scanner;
USE kamehameha_scanner;

-- Drop tables if they exist to ensure a clean slate on re-creation
DROP TABLE IF EXISTS scan_results;
DROP TABLE IF EXISTS scans;
DROP TABLE IF EXISTS companies;

-- Companies table
CREATE TABLE IF NOT EXISTS companies (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Scans table - matches the code expectations
CREATE TABLE IF NOT EXISTS scans (
    id INT AUTO_INCREMENT PRIMARY KEY,
    company_id INT NOT NULL,
    target_domain VARCHAR(255) NOT NULL,
    scan_datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('initializing', 'running', 'completed', 'failed') NOT NULL DEFAULT 'initializing',
    domain_file VARCHAR(512),
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

-- Scan results table - matches the code expectations
CREATE TABLE IF NOT EXISTS scan_results (
    id INT AUTO_INCREMENT PRIMARY KEY,
    scan_id INT NOT NULL,
    template_name VARCHAR(255) NOT NULL,
    severity VARCHAR(50) NOT NULL,
    protocol VARCHAR(50) DEFAULT 'http',
    target VARCHAR(2048) NOT NULL,
    details TEXT,
    cvss_score FLOAT DEFAULT 0.0,
    recommendation TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (scan_id) REFERENCES scans(id) ON DELETE CASCADE
);

-- Create indexes for better performance
CREATE INDEX idx_scan_results_severity ON scan_results(severity);
CREATE INDEX idx_scan_results_scan_id ON scan_results(scan_id);
CREATE INDEX idx_scans_company_id ON scans(company_id);
CREATE INDEX idx_scans_datetime ON scans(scan_datetime);
CREATE INDEX idx_companies_name ON companies(name);

-- Insert default companies if they don't exist
INSERT IGNORE INTO companies (name) VALUES ('TestCompany');
INSERT IGNORE INTO companies (name) VALUES ('DemoCorp');
INSERT IGNORE INTO companies (name) VALUES ('ExampleOrg');