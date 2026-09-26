package api

import (
	"context"
	"database/sql"
	"net/http"
	"regexp"
	"strings"

	"github.com/WilliamFeng7/CaffeeOrder/apps/backend/internal/store"
)

type User struct {
	ID             int64
	Username       string
	UUID           string
	Password       string
	Role           string // "student" | "barista" | "admin"
	Name           sql.NullString
	Phone          sql.NullString
	Email          sql.NullString
	FailedAttempts int64
	LastFailed     store.Time
	LockoutUntil   store.Time
	Balance        int64
	CreatedAt      store.Time
	UpdatedAt      store.Time
}

const userColumns = `id, username, uuid, password, role, name, phone, email,
	failed_login_attempts, last_failed_login, lockout_until, balance, created_at, updated_at`

type rowScanner interface{ Scan(dest ...any) error }

func scanUser(row rowScanner) (*User, error) {
	var u User
	err := row.Scan(&u.ID, &u.Username, &u.UUID, &u.Password, &u.Role, &u.Name, &u.Phone, &u.Email,
		&u.FailedAttempts, &u.LastFailed, &u.LockoutUntil, &u.Balance, &u.CreatedAt, &u.UpdatedAt)
	if err != nil {
		return nil, err
	}
	u.Role = store.APIEnum(u.Role)
	return &u, nil
}

func (s *Server) userByID(ctx context.Context, id int64) (*User, error) {
	return scanUser(s.db.QueryRowContext(ctx, `SELECT `+userColumns+` FROM user WHERE id = ?`, id))
}

func nullable(v sql.NullString) *string {
	if !v.Valid {
		return nil
	}
	return &v.String
}

// userOut is the UserOut schema, in the Python field order.
type userOut struct {
	ID                  int64   `json:"id"`
	Username            string  `json:"username"`
	UUID                string  `json:"uuid"`
	Name                *string `json:"name"`
	Phone               *string `json:"phone"`
	Email               *string `json:"email"`
	Role                string  `json:"role"`
	Balance             int64   `json:"balance"`
	FailedLoginAttempts int64   `json:"failed_login_attempts"`
	LockoutUntil        any     `json:"lockout_until"`
	CreatedAt           any     `json:"created_at"`
	UpdatedAt           any     `json:"updated_at"`
}

func fullUser(u *User) userOut {
	return userOut{
		ID: u.ID, Username: u.Username, UUID: u.UUID, Name: nullable(u.Name), Phone: nullable(u.Phone),
		Email: nullable(u.Email), Role: u.Role, Balance: u.Balance, FailedLoginAttempts: u.FailedAttempts,
		LockoutUntil: u.LockoutUntil.ISO(), CreatedAt: u.CreatedAt.ISO(), UpdatedAt: u.UpdatedAt.ISO(),
	}
}

// profile is what /users/me returned: identity, contact and balance only.
func profile(u *User) userOut {
	return userOut{
		ID: u.ID, Username: u.Username, UUID: u.UUID, Name: nullable(u.Name), Phone: nullable(u.Phone),
		Email: nullable(u.Email), Role: u.Role, Balance: u.Balance,
	}
}

func (s *Server) getMe(w http.ResponseWriter, r *http.Request) error {
	u, err := s.currentUser(r)
	if err != nil {
		return err
	}
	return ok(w, profile(u))
}

var (
	phonePattern = regexp.MustCompile(`^\d{11}$`)
	emailPattern = regexp.MustCompile(`^[^@\s]+@[^@\s]+\.[^@\s]+$`)
)

// checkContact validates phone/email formats (the messages the frontends show).
func checkContact(phone, email Optional) error {
	if phone.Set && !phone.Null && phone.Value != "" && !phonePattern.MatchString(phone.Value) {
		return invalidField("body", "phone", "手机号必须是 11 位数字 (Phone number must be exactly 11 digits)")
	}
	if email.Set && !email.Null && email.Value != "" && !emailPattern.MatchString(email.Value) {
		return invalidField("body", "email", "无效的邮箱格式 (Invalid email format)")
	}
	return nil
}

// contactTaken reports whether another account already uses the phone or email,
// since both double as login names.
func (s *Server) contactTaken(ctx context.Context, exceptID int64, phone, email Optional) (bool, error) {
	check := func(column string, v Optional) (bool, error) {
		if !v.Set || v.Null || v.Value == "" {
			return false, nil
		}
		var n int
		err := s.db.QueryRowContext(ctx,
			`SELECT count(*) FROM user WHERE (`+column+` = ? OR username = ?) AND id != ?`, v.Value, v.Value, exceptID).Scan(&n)
		return n > 0, err
	}
	if taken, err := check("phone", phone); taken || err != nil {
		return taken, err
	}
	return check("email", email)
}

type profileUpdate struct {
	Name  Optional `json:"name"`
	Phone Optional `json:"phone"`
	Email Optional `json:"email"`
}

func (s *Server) updateMe(w http.ResponseWriter, r *http.Request) error {
	u, err := s.currentUser(r)
	if err != nil {
		return err
	}
	var in profileUpdate
	if err := decodeJSON(r, &in); err != nil {
		return err
	}
	if err := checkContact(in.Phone, in.Email); err != nil {
		return err
	}
	if taken, err := s.contactTaken(r.Context(), u.ID, in.Phone, in.Email); err != nil {
		return err
	} else if taken {
		return fail(http.StatusBadRequest, "Email or phone already registered by another user")
	}
	sets, args := []string{}, []any{}
	for _, f := range []struct {
		col string
		v   Optional
	}{{"name", in.Name}, {"phone", in.Phone}, {"email", in.Email}} {
		if f.v.Set {
			sets, args = append(sets, f.col+" = ?"), append(args, f.v.Ptr())
		}
	}
	if len(sets) > 0 {
		sets, args = append(sets, "updated_at = ?"), append(args, store.DBTime(store.Now()), u.ID)
		if _, err := s.db.ExecContext(r.Context(), `UPDATE user SET `+strings.Join(sets, ", ")+` WHERE id = ?`, args...); err != nil {
			return err
		}
	}
	fresh, err := s.userByID(r.Context(), u.ID)
	if err != nil {
		return err
	}
	return ok(w, profile(fresh))
}
