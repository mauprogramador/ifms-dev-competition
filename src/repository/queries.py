CREATE_REPORT_TABLE = """
    CREATE TABLE IF NOT EXISTS Report (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dynamic TEXT NOT NULL,
        code TEXT NOT NULL,
        operation TEXT NOT NULL,
        file_type TEXT NOT NULL,
        timestamp REAL NOT NULL,
        similarity REAL NULL,
        score INTEGER NULL
    );
"""
DELETE_REPORTS = "DELETE FROM Report WHERE dynamic=?;"
INSERT_REPORT = """
    INSERT INTO Report
        (dynamic,code,operation,file_type,timestamp,similarity,score)
    VALUES (?, ?, ?, ?, ?, ?, ?);
"""
SELECT_DYNAMIC_REPORT = (
    "SELECT * FROM Report WHERE dynamic=? ORDER BY timestamp ASC;"
)
SELECT_FILE_REPORT = """
    SELECT MAX(timestamp) AS last_timestamp
    FROM Report WHERE dynamic=? AND code=? AND file_type=?;
"""
SELECT_OPERATIONS_REPORT = """
    SELECT
        code,
        operation,
        COUNT(*) AS total_exchanges,
        MIN(timestamp) AS first_timestamp,
        MAX(timestamp) AS last_timestamp,
        MAX(similarity) AS max_comparison,
        MAX(score) AS max_score
    FROM Report WHERE dynamic=? GROUP BY code;
"""
SELECT_OPERATION_REPORT = """
    SELECT
        code,
        operation,
        COUNT(*) AS total_exchanges,
        MIN(timestamp) AS first_timestamp,
        MAX(timestamp) AS last_timestamp,
        MAX(similarity) AS max_comparison,
        MAX(score) AS max_score
    FROM Report WHERE dynamic=? AND operation=? GROUP BY code;
"""


CREATE_DYNAMIC_TABLE = """
    CREATE TABLE IF NOT EXISTS Dynamic (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dynamic TEXT NOT NULL UNIQUE,
        lock_requests INTEGER NOT NULL,
        weight INTEGER NOT NULL,
        size TEXT NULL
    );
"""
INSERT_DYNAMIC = """
    INSERT INTO Dynamic (dynamic,lock_requests,weight) VALUES (?, ?, ?);
"""
SELECT_DYNAMICS = "SELECT dynamic FROM Dynamic ORDER BY id ASC;"
DELETE_DYNAMIC = "DELETE FROM Dynamic WHERE dynamic=?;"
SELECT_LOCK_STATUS = "SELECT lock_requests FROM Dynamic WHERE dynamic=?;"
UPDATE_LOCK_STATUS = "UPDATE Dynamic SET lock_requests=? WHERE dynamic=?;"
SELECT_WEIGHT = "SELECT weight FROM Dynamic WHERE dynamic=?;"
UPDATE_WEIGHT = "UPDATE Dynamic SET weight=? WHERE dynamic=?;"
SELECT_SIZE = "SELECT size FROM Dynamic WHERE dynamic=?;"
UPDATE_SIZE = "UPDATE Dynamic SET size=? WHERE dynamic=?;"
