package api

import (
	"database/sql"
	"errors"
	"fmt"
	"net/http"
	"time"

	"github.com/WilliamFeng7/CaffeeOrder/apps/backend/internal/auth"
	"github.com/WilliamFeng7/CaffeeOrder/apps/backend/internal/store"
)

// lockoutFor is the progressive lock applied after consecutive failures.
func lockoutFor(failures int64) time.Duration {
	switch {
	case failures >= 20:
		return 24 * time.Hour
	case failures >= 15:
		return 30 * time.Minute
	case failures >= 10:
		return 5 * time.Minute
	case failures >= 5:
		return time.Minute
	}
	return 0
}

func (s *Server) logLogin(r *http.Request, userID *int64, attempt, status string) {
	_, _ = s.db.ExecContext(r.Context(),
		`INSERT INTO loginlog (user_id, username_attempt, ip_address, user_agent, status, created_at) VALUES (?, ?, ?, ?, ?, ?)`,
		userID, attempt, auth.ClientIP(r, s.cfg.TrustedProxies), r.UserAgent(), status, store.DBTime(store.Now()))
}

// login is the OAuth2 password form: username may be a username, phone or email.
func (s *Server) login(w http.ResponseWriter, r *http.Request) error {
	if err := r.ParseForm(); err != nil {
		return fail(http.StatusBadRequest, "Could not read the login form")
	}
	username, password := r.PostForm.Get("username"), r.PostForm.Get("password")
	if _, has := r.PostForm["username"]; !has {
		return missingField("body", "username")
	}
	if _, has := r.PostForm["password"]; !has {
		return missingField("body", "password")
	}

	client := auth.ClientIP(r, s.cfg.TrustedProxies)
	if wait := s.limiter.Check(client); wait > 0 {
		return fail(http.StatusTooManyRequests,
			fmt.Sprintf("登录尝试过于频繁，请等待 %d 秒后重试 (Too many attempts)", int(wait.Seconds())))
	}

	ctx := r.Context()
	u, err := scanUser(s.db.QueryRowContext(ctx,
		`SELECT `+userColumns+` FROM user WHERE username = ? OR phone = ? OR email = ? ORDER BY id LIMIT 1`,
		username, username, username))
	if err != nil && !errors.Is(err, sql.ErrNoRows) {
		return err
	}
	if errors.Is(err, sql.ErrNoRows) {
		u = nil
	}

	now := store.Now()
	if u != nil && u.LockoutUntil.Valid {
		if u.LockoutUntil.Time.After(now) {
			s.logLogin(r, &u.ID, username, "locked_attempt")
			wait := int(u.LockoutUntil.Time.Sub(now).Minutes()) + 1
			if wait < 1 {
				wait = 1
			}
			return fail(http.StatusForbidden, map[string]any{
				"code":         "locked",
				"message":      fmt.Sprintf("Account locked. Try again in %d minutes.", wait),
				"unlock_at":    u.LockoutUntil.Time.Format("2006-01-02T15:04:05.000000-07:00"),
				"wait_minutes": wait,
			})
		}
		if _, err := s.db.ExecContext(ctx, `UPDATE user SET lockout_until = NULL WHERE id = ?`, u.ID); err != nil {
			return err
		}
	}

	valid := false
	if u != nil {
		valid = auth.VerifyPassword(password, u.Password)
	} else {
		auth.BurnPasswordCheck(password)
	}

	if !valid {
		s.limiter.RecordFailure(client)
		attemptsLeft := int64(5)
		if u == nil {
			s.logLogin(r, nil, username, "failed_unknown")
		} else {
			failures := u.FailedAttempts + 1
			var lockUntil any
			if d := lockoutFor(failures); d > 0 {
				lockUntil = store.DBTime(now.Add(d))
				status := fmt.Sprintf("locked_%dm", int(d.Minutes()))
				if d == time.Minute {
					status = "soft_locked_1m"
				}
				s.logLogin(r, &u.ID, username, status)
			}
			if _, err := s.db.ExecContext(ctx,
				`UPDATE user SET failed_login_attempts = ?, last_failed_login = ?, lockout_until = COALESCE(?, lockout_until) WHERE id = ?`,
				failures, store.DBTime(now), lockUntil, u.ID); err != nil {
				return err
			}
			s.logLogin(r, &u.ID, username, "failed")
			attemptsLeft = max(0, 5-failures)
		}
		return fail(http.StatusUnauthorized, map[string]any{
			"code":          "failed",
			"message":       "Invalid username or password",
			"attempts_left": attemptsLeft,
		})
	}

	if u.FailedAttempts > 0 || u.LockoutUntil.Valid {
		if _, err := s.db.ExecContext(ctx,
			`UPDATE user SET failed_login_attempts = 0, lockout_until = NULL, last_failed_login = NULL WHERE id = ?`, u.ID); err != nil {
			return err
		}
	}
	s.logLogin(r, &u.ID, username, "success")

	token, err := s.tokens.Issue(u.ID, u.Password)
	if err != nil {
		return err
	}
	return ok(w, map[string]any{
		"access_token": token,
		"token_type":   "bearer",
		"role":         u.Role,
		"username":     u.Username,
		"uuid":         u.UUID,
		"name":         nullable(u.Name),
	})
}

type passwordChange struct {
	OldPassword *string `json:"old_password"`
	NewPassword *string `json:"new_password"`
}

// changePassword re-hashes the password. Every token issued before this moment
// stops working; the response carries a fresh one for the current device.
func (s *Server) changePassword(w http.ResponseWriter, r *http.Request) error {
	u, err := s.currentUser(r)
	if err != nil {
		return err
	}
	var in passwordChange
	if err := decodeJSON(r, &in); err != nil {
		return err
	}
	if in.OldPassword == nil {
		return missingField("body", "old_password")
	}
	if in.NewPassword == nil {
		return missingField("body", "new_password")
	}
	if err := auth.ValidatePassword(*in.NewPassword); err != nil {
		return invalidField("body", "new_password", err.Error())
	}
	if !auth.VerifyPassword(*in.OldPassword, u.Password) {
		return fail(http.StatusBadRequest, "旧密码错误 (Incorrect old password)")
	}
	hash, err := auth.HashPassword(*in.NewPassword)
	if err != nil {
		return err
	}
	if _, err := s.db.ExecContext(r.Context(), `UPDATE user SET password = ?, updated_at = ? WHERE id = ?`,
		hash, store.DBTime(store.Now()), u.ID); err != nil {
		return err
	}
	token, err := s.tokens.Issue(u.ID, hash)
	if err != nil {
		return err
	}
	return ok(w, map[string]any{
		"message":      "密码修改成功 (Password updated successfully)",
		"access_token": token,
		"token_type":   "bearer",
	})
}
