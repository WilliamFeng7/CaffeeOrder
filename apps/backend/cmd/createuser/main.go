// Command createuser creates an account, or resets the password and role of an
// existing one. It is how a new deployment gets its first admin:
//
//	createuser -username admin -name 店长 -role admin
//
// The password is read from the COFFEE_PASSWORD environment variable, or
// prompted for, so it never ends up in shell history.
package main

import (
	"bufio"
	"context"
	"database/sql"
	"errors"
	"flag"
	"fmt"
	"os"
	"strings"

	"github.com/WilliamFeng7/CaffeeOrder/apps/backend/internal/auth"
	"github.com/WilliamFeng7/CaffeeOrder/apps/backend/internal/config"
	"github.com/WilliamFeng7/CaffeeOrder/apps/backend/internal/store"
)

func main() {
	username := flag.String("username", "", "login name (student or staff ID)")
	name := flag.String("name", "", "display name")
	role := flag.String("role", "student", "student, barista or admin")
	dir := flag.String("dir", ".", "backend directory (for .env and the default database)")
	flag.Parse()

	if err := run(*dir, strings.TrimSpace(*username), strings.TrimSpace(*name), strings.ToLower(*role)); err != nil {
		fmt.Fprintln(os.Stderr, "createuser:", err)
		os.Exit(1)
	}
}

func run(dir, username, name, role string) error {
	if username == "" {
		return errors.New("-username is required")
	}
	if role != "student" && role != "barista" && role != "admin" {
		return fmt.Errorf("-role must be student, barista or admin, got %q", role)
	}
	password := os.Getenv("COFFEE_PASSWORD")
	if password == "" {
		fmt.Print("Password: ")
		line, _ := bufio.NewReader(os.Stdin).ReadString('\n')
		password = strings.TrimRight(line, "\r\n")
	}
	if err := auth.ValidatePassword(password); err != nil {
		return err
	}
	hash, err := auth.HashPassword(password)
	if err != nil {
		return err
	}

	cfg, err := config.Load(dir, "")
	if err != nil {
		return err
	}
	db, err := store.Open(cfg.DatabasePath)
	if err != nil {
		return err
	}
	defer db.Close()
	ctx := context.Background()
	if err := store.EnsureSchema(ctx, db); err != nil {
		return err
	}

	now := store.DBTime(store.Now())
	var id int64
	err = db.QueryRowContext(ctx, `SELECT id FROM user WHERE username = ?`, username).Scan(&id)
	switch {
	case errors.Is(err, sql.ErrNoRows):
		if name == "" {
			name = username
		}
		_, err = db.ExecContext(ctx,
			`INSERT INTO user (username, uuid, password, role, name, failed_login_attempts, balance, created_at, updated_at)
			 VALUES (?, lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))), 2) || '-a' || substr(lower(hex(randomblob(2))), 2) || '-' || lower(hex(randomblob(6))),
			         ?, ?, ?, 0, 0, ?, ?)`,
			username, hash, store.DBEnum(role), name, now, now)
		if err == nil {
			fmt.Printf("created %s (%s)\n", username, role)
		}
	case err == nil:
		_, err = db.ExecContext(ctx,
			`UPDATE user SET password = ?, role = ?, failed_login_attempts = 0, lockout_until = NULL, updated_at = ? WHERE id = ?`,
			hash, store.DBEnum(role), now, id)
		if err == nil {
			fmt.Printf("updated %s: new password, role %s\n", username, role)
		}
	}
	return err
}
