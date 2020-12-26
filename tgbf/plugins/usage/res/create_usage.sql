CREATE TABLE usage (
    user_id INTEGER NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT,
	username TEXT,
	localization TEXT,
	group_id TEXT,
	group_name TEXT,
	message TEXT NOT NULL,
    date_time DATETIME DEFAULT CURRENT_TIMESTAMP
)