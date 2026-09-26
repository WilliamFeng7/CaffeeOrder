package api

import (
	"context"
	"crypto/rand"
	"database/sql"
	"encoding/hex"
	"errors"
	"fmt"
	"net/http"
	"strconv"
	"strings"
	"time"

	"github.com/WilliamFeng7/CaffeeOrder/apps/backend/internal/auth"
	"github.com/WilliamFeng7/CaffeeOrder/apps/backend/internal/store"
)

// maxBalance bounds any balance an admin can set (¥100,000.00).
const maxBalance = 10_000_000

func newUUID() string {
	b := make([]byte, 16)
	if _, err := rand.Read(b); err != nil {
		panic(err)
	}
	b[6] = b[6]&0x0f | 0x40
	b[8] = b[8]&0x3f | 0x80
	h := hex.EncodeToString(b)
	return h[0:8] + "-" + h[8:12] + "-" + h[12:16] + "-" + h[16:20] + "-" + h[20:]
}

func randomTag(n int) string {
	b := make([]byte, (n+1)/2)
	if _, err := rand.Read(b); err != nil {
		panic(err)
	}
	return strings.ToUpper(hex.EncodeToString(b))[:n]
}

// ledgerID is the external_transaction_id of a manual balance movement.
func ledgerID(prefix string, userID int64, now time.Time) string {
	return fmt.Sprintf("%s%s%d-%s", prefix, now.Format("20060102150405"), userID, randomTag(6))
}

// writeLedger records a balance movement inside tx.
func writeLedger(ctx context.Context, tx *sql.Tx, userID, amount, balanceAfter int64, kind, method, description, prefix string, now time.Time) error {
	_, err := tx.ExecContext(ctx,
		`INSERT INTO "transaction" (user_id, order_id, external_transaction_id, amount, balance_after, type, payment_method, description, created_at)
		 VALUES (?, NULL, ?, ?, ?, ?, ?, ?, ?)`,
		userID, ledgerID(prefix, userID, now), amount, balanceAfter, kind, method, description, store.DBTime(now))
	return err
}

// deposit is the admin top-up: an atomic increment plus a ledger row.
func (s *Server) deposit(w http.ResponseWriter, r *http.Request) error {
	if _, err := s.requireRole(r, "admin"); err != nil {
		return err
	}
	id, err := pathID(r, "id")
	if err != nil {
		return err
	}
	amount, err := strconv.ParseInt(r.URL.Query().Get("amount"), 10, 64)
	if err != nil {
		return validation([]any{"query", "amount"}, "Input should be a valid integer", "int_parsing")
	}
	if amount <= 0 {
		return validation([]any{"query", "amount"}, "Input should be greater than 0", "greater_than")
	}
	if amount > 1_000_000 {
		return validation([]any{"query", "amount"}, "Input should be less than or equal to 1000000", "less_than_equal")
	}
	ctx := r.Context()
	tx, err := s.db.BeginTx(ctx, nil)
	if err != nil {
		return err
	}
	defer tx.Rollback()
	res, err := tx.ExecContext(ctx, `UPDATE user SET balance = balance + ? WHERE id = ?`, amount, id)
	if err != nil {
		return err
	}
	if n, _ := res.RowsAffected(); n == 0 {
		return fail(http.StatusNotFound, "User not found")
	}
	var balance int64
	if err := tx.QueryRowContext(ctx, `SELECT balance FROM user WHERE id = ?`, id).Scan(&balance); err != nil {
		return err
	}
	now := store.Now()
	if err := writeLedger(ctx, tx, id, amount, balance, "deposit", "admin_topup", "Admin Manual Top-up", "DEP", now); err != nil {
		return err
	}
	if err := tx.Commit(); err != nil {
		return err
	}
	u, err := s.userByID(ctx, id)
	if err != nil {
		return err
	}
	return ok(w, fullUser(u))
}

func (s *Server) listUsers(w http.ResponseWriter, r *http.Request) error {
	if _, err := s.requireRole(r, "admin"); err != nil {
		return err
	}
	// The old console never paged, so a 20-row default hid everyone after the 20th user.
	p, err := pagination(r, 200)
	if err != nil {
		return err
	}
	rows, err := s.db.QueryContext(r.Context(),
		`SELECT `+userColumns+` FROM user ORDER BY id LIMIT ? OFFSET ?`, p.limit, p.skip)
	if err != nil {
		return err
	}
	defer rows.Close()
	out := []userOut{}
	for rows.Next() {
		u, err := scanUser(rows)
		if err != nil {
			return err
		}
		out = append(out, fullUser(u))
	}
	if err := rows.Err(); err != nil {
		return err
	}
	return ok(w, out)
}

// userInput is the create/update body. balance is in cents: the admin console
// already multiplies yuan by 100, and the Python schema multiplied again, which
// is how balances ended up 100 times too large.
type userInput struct {
	Username Optional `json:"username"`
	Password Optional `json:"password"`
	Role     Optional `json:"role"`
	Balance  Number   `json:"balance"`
	Name     Optional `json:"name"`
	Phone    Optional `json:"phone"`
	Email    Optional `json:"email"`
}

func normaliseRole(v Optional) (string, error) {
	role := strings.ToLower(trimmedValue(v))
	switch role {
	case "student", "barista", "admin":
		return role, nil
	}
	return "", invalidField("body", "role", "角色必须是 student / barista / admin (Role must be student, barista or admin)")
}

func trimmedValue(v Optional) string { return strings.TrimSpace(v.Value) }

func checkBalance(n Number) error {
	if n.Set && !n.Null && (n.Value < 0 || n.Value > maxBalance) {
		return invalidField("body", "balance", "余额需在 0 到 10000000 分之间 (Balance must be between 0 and 10000000 cents)")
	}
	return nil
}

func (s *Server) createUser(w http.ResponseWriter, r *http.Request) error {
	if _, err := s.requireRole(r, "admin"); err != nil {
		return err
	}
	var in userInput
	if err := decodeJSON(r, &in); err != nil {
		return err
	}
	username, name := trimmedValue(in.Username), trimmedValue(in.Name)
	switch {
	case !in.Username.Set || in.Username.Null || username == "":
		return missingField("body", "username")
	case !in.Password.Set || in.Password.Null:
		return missingField("body", "password")
	case !in.Name.Set || in.Name.Null || name == "":
		return missingField("body", "name")
	}
	if err := auth.ValidatePassword(in.Password.Value); err != nil {
		return invalidField("body", "password", err.Error())
	}
	role := "student"
	if in.Role.Set && !in.Role.Null {
		var err error
		if role, err = normaliseRole(in.Role); err != nil {
			return err
		}
	}
	if err := checkBalance(in.Balance); err != nil {
		return err
	}
	if err := checkContact(in.Phone, in.Email); err != nil {
		return err
	}
	ctx := r.Context()
	var exists int
	if err := s.db.QueryRowContext(ctx, `SELECT count(*) FROM user WHERE username = ?`, username).Scan(&exists); err != nil {
		return err
	}
	if exists > 0 {
		return fail(http.StatusBadRequest, "The user with this username already exists in the system.")
	}
	if taken, err := s.contactTaken(ctx, 0, in.Phone, in.Email); err != nil {
		return err
	} else if taken {
		return fail(http.StatusBadRequest, "Email or phone already registered by another user")
	}
	hash, err := auth.HashPassword(in.Password.Value)
	if err != nil {
		return err
	}
	balance := int64(0)
	if in.Balance.Set && !in.Balance.Null {
		balance = in.Balance.Value
	}
	now := store.Now()
	tx, err := s.db.BeginTx(ctx, nil)
	if err != nil {
		return err
	}
	defer tx.Rollback()
	res, err := tx.ExecContext(ctx,
		`INSERT INTO user (username, uuid, password, role, name, phone, email, failed_login_attempts, balance, created_at, updated_at)
		 VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?)`,
		username, newUUID(), hash, store.DBEnum(role), name, blankToNil(in.Phone), blankToNil(in.Email),
		balance, store.DBTime(now), store.DBTime(now))
	if err != nil {
		return err
	}
	id, _ := res.LastInsertId()
	if balance > 0 {
		if err := writeLedger(ctx, tx, id, balance, balance, "deposit", "account_opening", "Opening balance", "DEP", now); err != nil {
			return err
		}
	}
	if err := tx.Commit(); err != nil {
		return err
	}
	u, err := s.userByID(ctx, id)
	if err != nil {
		return err
	}
	return ok(w, fullUser(u))
}

// blankToNil stores an absent or empty contact field as NULL.
func blankToNil(v Optional) any {
	if !v.Set || v.Null || strings.TrimSpace(v.Value) == "" {
		return nil
	}
	return strings.TrimSpace(v.Value)
}

func (s *Server) updateUser(w http.ResponseWriter, r *http.Request) error {
	if _, err := s.requireRole(r, "admin"); err != nil {
		return err
	}
	id, err := pathID(r, "id")
	if err != nil {
		return err
	}
	var in userInput
	if err := decodeJSON(r, &in); err != nil {
		return err
	}
	ctx := r.Context()
	current, err := s.userByID(ctx, id)
	if errors.Is(err, sql.ErrNoRows) {
		return fail(http.StatusNotFound, "User not found")
	}
	if err != nil {
		return err
	}
	if err := checkContact(in.Phone, in.Email); err != nil {
		return err
	}
	if err := checkBalance(in.Balance); err != nil {
		return err
	}
	if taken, err := s.contactTaken(ctx, id, in.Phone, in.Email); err != nil {
		return err
	} else if taken {
		return fail(http.StatusBadRequest, "Email or phone already registered by another user")
	}

	sets, args := []string{}, []any{}
	if in.Name.Set {
		sets, args = append(sets, "name = ?"), append(args, in.Name.Ptr())
	}
	if in.Phone.Set {
		sets, args = append(sets, "phone = ?"), append(args, blankToNil(in.Phone))
	}
	if in.Email.Set {
		sets, args = append(sets, "email = ?"), append(args, blankToNil(in.Email))
	}
	if in.Role.Set && !in.Role.Null {
		role, err := normaliseRole(in.Role)
		if err != nil {
			return err
		}
		sets, args = append(sets, "role = ?"), append(args, store.DBEnum(role))
	}
	if in.Password.Set && !in.Password.Null && in.Password.Value != "" {
		if err := auth.ValidatePassword(in.Password.Value); err != nil {
			return invalidField("body", "password", err.Error())
		}
		hash, err := auth.HashPassword(in.Password.Value)
		if err != nil {
			return err
		}
		sets, args = append(sets, "password = ?"), append(args, hash)
	}

	now := store.Now()
	tx, err := s.db.BeginTx(ctx, nil)
	if err != nil {
		return err
	}
	defer tx.Rollback()
	if len(sets) > 0 {
		sets, args = append(sets, "updated_at = ?"), append(args, store.DBTime(now), id)
		if _, err := tx.ExecContext(ctx, `UPDATE user SET `+strings.Join(sets, ", ")+` WHERE id = ?`, args...); err != nil {
			return err
		}
	}
	// A balance edit is a correction: applied only if nobody else moved the
	// balance meanwhile, and recorded in the ledger as an adjustment.
	if in.Balance.Set && !in.Balance.Null && in.Balance.Value != current.Balance {
		res, err := tx.ExecContext(ctx, `UPDATE user SET balance = ?, updated_at = ? WHERE id = ? AND balance = ?`,
			in.Balance.Value, store.DBTime(now), id, current.Balance)
		if err != nil {
			return err
		}
		if n, _ := res.RowsAffected(); n == 0 {
			return fail(http.StatusConflict, "余额已被其他操作修改，请刷新后重试 (Balance changed meanwhile, refresh and retry)")
		}
		if err := writeLedger(ctx, tx, id, in.Balance.Value-current.Balance, in.Balance.Value,
			"adjustment", "admin_adjustment", "Admin balance correction", "ADJ", now); err != nil {
			return err
		}
	}
	if err := tx.Commit(); err != nil {
		return err
	}
	u, err := s.userByID(ctx, id)
	if err != nil {
		return err
	}
	return ok(w, fullUser(u))
}

func (s *Server) deleteUser(w http.ResponseWriter, r *http.Request) error {
	admin, err := s.requireRole(r, "admin")
	if err != nil {
		return err
	}
	id, err := pathID(r, "id")
	if err != nil {
		return err
	}
	target, err := s.userByID(r.Context(), id)
	if errors.Is(err, sql.ErrNoRows) {
		return fail(http.StatusNotFound, "User not found")
	}
	if err != nil {
		return err
	}
	if target.Role == "admin" {
		return fail(http.StatusForbidden, "Cannot delete an admin user")
	}
	if target.ID == admin.ID {
		return fail(http.StatusBadRequest, "Cannot delete yourself")
	}
	if _, err := s.db.ExecContext(r.Context(), `DELETE FROM user WHERE id = ?`, id); err != nil {
		return err
	}
	return ok(w, map[string]bool{"ok": true})
}
