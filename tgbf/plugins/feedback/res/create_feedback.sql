CREATE TABLE feedback (
    user_id INTEGER NOT NULL,
    first_name TEXT NOT NULL,
	username TEXT,
	feedback TEXT NOT NULL,
	date_time DATETIME DEFAULT CURRENT_TIMESTAMP
)