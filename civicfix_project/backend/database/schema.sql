-- =========================================================================
-- CivicFix - Reference MySQL Schema
-- =========================================================================
-- This documents the shape of the database in plain SQL for your defense
-- / diagrams. In practice you do NOT need to run this file by hand --
-- Django's migrations (`python manage.py migrate`) create these tables
-- automatically from accounts/models.py, departments/models.py, and
-- complaints/models.py. This file is kept in sync with those models for
-- reference and for anyone who wants to inspect/version the raw schema.
-- =========================================================================

CREATE DATABASE IF NOT EXISTS civicfix CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE civicfix;

-- ---------------------------------------------------------------------
-- Departments
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS departments_department (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    name            VARCHAR(150) NOT NULL,
    category        VARCHAR(30) NOT NULL UNIQUE,   -- road_damage, water_leakage, garbage, street_light, drainage, others
    description     TEXT,
    contact_email   VARCHAR(254),
    contact_phone   VARCHAR(20),
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      DATETIME(6) NOT NULL
);

-- ---------------------------------------------------------------------
-- Users (citizens, department staff, admins)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS accounts_user (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    password        VARCHAR(128) NOT NULL,
    last_login      DATETIME(6),
    is_superuser    BOOLEAN NOT NULL DEFAULT FALSE,
    username        VARCHAR(150),
    first_name      VARCHAR(150),
    last_name       VARCHAR(150),
    is_staff        BOOLEAN NOT NULL DEFAULT FALSE,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    date_joined     DATETIME(6) NOT NULL,
    email           VARCHAR(254) NOT NULL UNIQUE,
    role            VARCHAR(20) NOT NULL DEFAULT 'citizen',  -- citizen | department | admin
    phone           VARCHAR(20),
    department_id   BIGINT,
    created_at      DATETIME(6) NOT NULL,
    FOREIGN KEY (department_id) REFERENCES departments_department(id) ON DELETE SET NULL
);

-- ---------------------------------------------------------------------
-- Complaints (the core entity)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS complaints_complaint (
    id                      BIGINT AUTO_INCREMENT PRIMARY KEY,
    citizen_id              BIGINT NOT NULL,
    title                   VARCHAR(200) NOT NULL,
    description             TEXT NOT NULL,
    category                VARCHAR(30) NOT NULL,
    department_id           BIGINT,
    photo                   VARCHAR(255),
    latitude                DECIMAL(10,7),
    longitude               DECIMAL(10,7),
    address                 VARCHAR(500),
    status                  VARCHAR(20) NOT NULL DEFAULT 'pending', -- pending | in_progress | resolved
    is_emergency            BOOLEAN NOT NULL DEFAULT FALSE,
    emergency_confidence    FLOAT NOT NULL DEFAULT 0,
    emergency_reason        VARCHAR(255),
    auto_categorized        BOOLEAN NOT NULL DEFAULT FALSE,
    created_at              DATETIME(6) NOT NULL,
    updated_at              DATETIME(6) NOT NULL,
    resolved_at             DATETIME(6),
    FOREIGN KEY (citizen_id) REFERENCES accounts_user(id) ON DELETE CASCADE,
    FOREIGN KEY (department_id) REFERENCES departments_department(id) ON DELETE SET NULL
);

-- ---------------------------------------------------------------------
-- Complaint status history (audit trail / "track status")
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS complaints_complaintstatushistory (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    complaint_id    BIGINT NOT NULL,
    status          VARCHAR(20) NOT NULL,
    changed_by_id   BIGINT,
    note            VARCHAR(500),
    created_at      DATETIME(6) NOT NULL,
    FOREIGN KEY (complaint_id) REFERENCES complaints_complaint(id) ON DELETE CASCADE,
    FOREIGN KEY (changed_by_id) REFERENCES accounts_user(id) ON DELETE SET NULL
);

-- ---------------------------------------------------------------------
-- Complaint updates ("receives updates" page)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS complaints_complaintupdate (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    complaint_id    BIGINT NOT NULL,
    posted_by_id    BIGINT,
    message         TEXT NOT NULL,
    created_at      DATETIME(6) NOT NULL,
    FOREIGN KEY (complaint_id) REFERENCES complaints_complaint(id) ON DELETE CASCADE,
    FOREIGN KEY (posted_by_id) REFERENCES accounts_user(id) ON DELETE SET NULL
);

-- ---------------------------------------------------------------------
-- Notifications (sent by Admin: to citizens about status, or to
-- department staff as reminders)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS complaints_notification (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    recipient_id    BIGINT NOT NULL,
    complaint_id    BIGINT,
    kind            VARCHAR(30) NOT NULL, -- status_change | new_update | sla_warning | emergency
    message         VARCHAR(500) NOT NULL,
    is_read         BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      DATETIME(6) NOT NULL,
    FOREIGN KEY (recipient_id) REFERENCES accounts_user(id) ON DELETE CASCADE,
    FOREIGN KEY (complaint_id) REFERENCES complaints_complaint(id) ON DELETE CASCADE
);

-- ---------------------------------------------------------------------
-- Helpful indexes
-- ---------------------------------------------------------------------
CREATE INDEX idx_complaint_status ON complaints_complaint(status);
CREATE INDEX idx_complaint_category ON complaints_complaint(category);
CREATE INDEX idx_complaint_department ON complaints_complaint(department_id);
CREATE INDEX idx_complaint_citizen ON complaints_complaint(citizen_id);
CREATE INDEX idx_notification_recipient ON complaints_notification(recipient_id);
