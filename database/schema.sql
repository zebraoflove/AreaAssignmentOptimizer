-- ==========================================================
-- AreaAssignmentOptimizer
-- Database schema v1.0
-- ==========================================================

PRAGMA foreign_keys = ON;

-- ==========================================================
-- Schema version
-- ==========================================================

CREATE TABLE IF NOT EXISTS schema_version (

    version INTEGER PRIMARY KEY,

    applied_at TEXT NOT NULL

);

-- ==========================================================
-- Subjects of the Russian Federation
-- ==========================================================

CREATE TABLE IF NOT EXISTS subjects_raw (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    name TEXT NOT NULL UNIQUE,

    type TEXT NOT NULL,

    federal_district TEXT NOT NULL,

    area_km2 REAL NOT NULL
        CHECK(area_km2 > 0)

);

-- ==========================================================
-- Countries
-- ==========================================================

CREATE TABLE IF NOT EXISTS countries_raw (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    name TEXT NOT NULL UNIQUE,

    iso_alpha2 TEXT,

    iso_alpha3 TEXT,

    continent TEXT NOT NULL,

    area_km2 REAL NOT NULL
        CHECK(area_km2 > 0)

);

-- ==========================================================
-- Territory adjustments
-- ==========================================================

CREATE TABLE IF NOT EXISTS territory_adjustments (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    territory TEXT NOT NULL,

    area_km2 REAL NOT NULL
        CHECK(area_km2 > 0),

    subtract_from TEXT NOT NULL,

    add_to TEXT NOT NULL,

    comment TEXT

);

-- ==========================================================
-- Candidate sets
-- ==========================================================

CREATE TABLE IF NOT EXISTS candidate_sets (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    subject_id INTEGER NOT NULL,

    FOREIGN KEY(subject_id)
        REFERENCES subjects(id)
        ON DELETE CASCADE

);

-- ==========================================================
-- Countries inside candidate sets
-- ==========================================================

CREATE TABLE IF NOT EXISTS candidate_set_items (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    candidate_set_id INTEGER NOT NULL,

    country_id INTEGER NOT NULL,

    FOREIGN KEY(candidate_set_id)
        REFERENCES candidate_sets(id)
        ON DELETE CASCADE,

    FOREIGN KEY(country_id)
        REFERENCES countries(id)
        ON DELETE RESTRICT,

    UNIQUE(candidate_set_id, country_id)

);

-- ==========================================================
-- Final assignments
-- ==========================================================

CREATE TABLE IF NOT EXISTS assignments (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    subject_id INTEGER NOT NULL,

    FOREIGN KEY(subject_id)
        REFERENCES subjects(id)
        ON DELETE CASCADE

);

-- ==========================================================
-- Countries inside final assignments
-- ==========================================================

CREATE TABLE IF NOT EXISTS assignment_items (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    assignment_id INTEGER NOT NULL,

    country_id INTEGER NOT NULL,

    FOREIGN KEY(assignment_id)
        REFERENCES assignments(id)
        ON DELETE CASCADE,

    FOREIGN KEY(country_id)
        REFERENCES countries(id)
        ON DELETE RESTRICT,

    UNIQUE(assignment_id, country_id)

);

-- ==========================================================
-- Countries inside final assignments
-- ==========================================================

CREATE TABLE IF NOT EXISTS countries_final (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    name TEXT NOT NULL UNIQUE,

    iso_alpha2 TEXT,

    iso_alpha3 TEXT,

    continent TEXT NOT NULL,

    area_km2 REAL NOT NULL
        CHECK(area_km2 > 0)

);

-- ==========================================================
-- Russian subjects inside final assignments
-- ==========================================================

CREATE TABLE IF NOT EXISTS subjects_final (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    name TEXT NOT NULL UNIQUE,

    type TEXT NOT NULL,

    federal_district TEXT NOT NULL,

    area_km2 REAL NOT NULL
        CHECK(area_km2 > 0)

);