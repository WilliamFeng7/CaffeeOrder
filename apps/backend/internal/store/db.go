// Package store opens the SQLite database and owns the schema and the value
// conventions shared with the rows the Python backend already wrote:
// enums stored as upper-case names, naive Beijing-time timestamps with
// microseconds, booleans as 0/1, money as integer cents.
package store

import (
	"context"
	"database/sql"
	"fmt"
	"net/url"
	"os"
	"path/filepath"
	"strings"

	_ "modernc.org/sqlite"
)

// Open connects to the SQLite file at path, creating the directory if needed.
// Every transaction starts with BEGIN IMMEDIATE, so two writers queue on the
// busy timeout instead of failing halfway through a read-then-write.
func Open(path string) (*sql.DB, error) {
	if dir := filepath.Dir(path); dir != "" {
		if err := os.MkdirAll(dir, 0o755); err != nil {
			return nil, fmt.Errorf("create database directory: %w", err)
		}
	}
	q := url.Values{}
	q.Add("_pragma", "busy_timeout(5000)")
	q.Add("_pragma", "journal_mode(WAL)")
	q.Add("_pragma", "synchronous(NORMAL)")
	q.Add("_txlock", "immediate")
	db, err := sql.Open("sqlite", "file:"+path+"?"+q.Encode())
	if err != nil {
		return nil, err
	}
	db.SetMaxOpenConns(4)
	if err := db.Ping(); err != nil {
		db.Close()
		return nil, fmt.Errorf("open %s: %w", path, err)
	}
	return db, nil
}

// baselineRevision is the Alembic revision whose schema this file creates, so a
// database started by the Go server can still be handed to the Python tools.
const baselineRevision = "ed4f607a8f09"

var schema = []string{
	`CREATE TABLE IF NOT EXISTS user (
	id INTEGER NOT NULL,
	username VARCHAR NOT NULL,
	uuid VARCHAR NOT NULL,
	password VARCHAR NOT NULL,
	role VARCHAR(7) NOT NULL,
	name VARCHAR,
	phone VARCHAR,
	email VARCHAR,
	failed_login_attempts INTEGER NOT NULL,
	last_failed_login DATETIME,
	lockout_until DATETIME,
	balance INTEGER NOT NULL,
	created_at DATETIME NOT NULL,
	updated_at DATETIME NOT NULL,
	PRIMARY KEY (id)
)`,
	`CREATE UNIQUE INDEX IF NOT EXISTS ix_user_uuid ON user (uuid)`,
	`CREATE UNIQUE INDEX IF NOT EXISTS ix_user_username ON user (username)`,
	`CREATE TABLE IF NOT EXISTS menuitem (
	id INTEGER NOT NULL,
	name VARCHAR NOT NULL,
	name_cn VARCHAR,
	description VARCHAR,
	price INTEGER NOT NULL,
	category VARCHAR NOT NULL,
	image_path VARCHAR NOT NULL,
	is_active BOOLEAN NOT NULL,
	is_recommend BOOLEAN NOT NULL,
	inventory_count INTEGER NOT NULL,
	PRIMARY KEY (id)
)`,
	`CREATE INDEX IF NOT EXISTS ix_menuitem_name ON menuitem (name)`,
	`CREATE INDEX IF NOT EXISTS ix_menuitem_category ON menuitem (category)`,
	`CREATE TABLE IF NOT EXISTS systemsetting (
	"key" VARCHAR NOT NULL,
	value VARCHAR NOT NULL,
	description VARCHAR,
	PRIMARY KEY ("key")
)`,
	`CREATE TABLE IF NOT EXISTS "transaction" (
	id INTEGER NOT NULL,
	user_id INTEGER,
	order_id INTEGER,
	external_transaction_id VARCHAR NOT NULL,
	amount INTEGER NOT NULL,
	balance_after INTEGER NOT NULL,
	type VARCHAR NOT NULL,
	payment_method VARCHAR NOT NULL,
	description VARCHAR,
	created_at DATETIME NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(user_id) REFERENCES user (id)
)`,
	`CREATE INDEX IF NOT EXISTS ix_transaction_type_created_at ON "transaction" (type, created_at)`,
	`CREATE UNIQUE INDEX IF NOT EXISTS ix_transaction_external_transaction_id ON "transaction" (external_transaction_id)`,
	`CREATE INDEX IF NOT EXISTS ix_transaction_order_id ON "transaction" (order_id)`,
	`CREATE INDEX IF NOT EXISTS ix_transaction_user_id ON "transaction" (user_id)`,
	`CREATE INDEX IF NOT EXISTS ix_transaction_type ON "transaction" (type)`,
	`CREATE TABLE IF NOT EXISTS loginlog (
	id INTEGER NOT NULL,
	user_id INTEGER,
	username_attempt VARCHAR NOT NULL,
	ip_address VARCHAR NOT NULL,
	user_agent VARCHAR,
	status VARCHAR NOT NULL,
	created_at DATETIME NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(user_id) REFERENCES user (id)
)`,
	`CREATE INDEX IF NOT EXISTS ix_loginlog_user_id ON loginlog (user_id)`,
	`CREATE INDEX IF NOT EXISTS ix_loginlog_username_attempt ON loginlog (username_attempt)`,
	`CREATE TABLE IF NOT EXISTS "order" (
	id INTEGER NOT NULL,
	user_id INTEGER,
	order_no VARCHAR NOT NULL,
	status VARCHAR(10) NOT NULL,
	created_at DATETIME NOT NULL,
	total_amount INTEGER NOT NULL,
	pickup_number INTEGER NOT NULL,
	is_completed BOOLEAN NOT NULL,
	updated_at DATETIME NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(user_id) REFERENCES user (id)
)`,
	`CREATE INDEX IF NOT EXISTS ix_order_updated_at ON "order" (updated_at)`,
	`CREATE INDEX IF NOT EXISTS ix_order_status ON "order" (status)`,
	`CREATE INDEX IF NOT EXISTS ix_order_created_at ON "order" (created_at)`,
	`CREATE UNIQUE INDEX IF NOT EXISTS ix_order_order_no ON "order" (order_no)`,
	`CREATE INDEX IF NOT EXISTS ix_order_user_created_at ON "order" (user_id, created_at)`,
	`CREATE INDEX IF NOT EXISTS ix_order_user_id ON "order" (user_id)`,
	`CREATE INDEX IF NOT EXISTS ix_order_status_created_at ON "order" (status, created_at)`,
	`CREATE TABLE IF NOT EXISTS orderitem (
	id INTEGER NOT NULL,
	order_id INTEGER NOT NULL,
	menu_item_id INTEGER NOT NULL,
	item_name VARCHAR NOT NULL,
	price_snap INTEGER NOT NULL,
	image_url VARCHAR NOT NULL,
	spec VARCHAR NOT NULL,
	quantity INTEGER NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(order_id) REFERENCES "order" (id)
)`,
	`CREATE INDEX IF NOT EXISTS ix_orderitem_order_id ON orderitem (order_id)`,
	`CREATE TABLE IF NOT EXISTS alembic_version (
	version_num VARCHAR(32) NOT NULL,
	CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
)`,
}

// pickupIndex backs the "pickup numbers are unique per day" rule. Old
// databases can hold duplicates from before the rule existed; the server then
// runs without the index rather than refusing to start.
const pickupIndex = `CREATE UNIQUE INDEX IF NOT EXISTS uix_order_day_pickup ON "order" (date(created_at), pickup_number)`

// EnsureSchema creates any missing tables and indexes. It never alters or drops
// existing ones, so it is safe to run on every start.
func EnsureSchema(ctx context.Context, db *sql.DB) error {
	tx, err := db.BeginTx(ctx, nil)
	if err != nil {
		return err
	}
	defer tx.Rollback()
	for _, stmt := range schema {
		if _, err := tx.ExecContext(ctx, stmt); err != nil {
			return fmt.Errorf("schema: %w\n%s", err, firstLine(stmt))
		}
	}
	var n int
	if err := tx.QueryRowContext(ctx, `SELECT count(*) FROM alembic_version`).Scan(&n); err != nil {
		return err
	}
	if n == 0 {
		if _, err := tx.ExecContext(ctx, `INSERT INTO alembic_version (version_num) VALUES (?)`, baselineRevision); err != nil {
			return err
		}
	}
	if err := tx.Commit(); err != nil {
		return err
	}
	if _, err := db.ExecContext(ctx, pickupIndex); err != nil && !strings.Contains(err.Error(), "UNIQUE") {
		return fmt.Errorf("pickup index: %w", err)
	}
	return nil
}

func firstLine(s string) string {
	line, _, _ := strings.Cut(s, "\n")
	return line
}
