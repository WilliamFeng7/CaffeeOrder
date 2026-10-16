package api

import (
	"net/http"
	"strings"

	"github.com/WilliamFeng7/CaffeeOrder/apps/backend/internal/store"
	"github.com/google/uuid"
)

func (s *Server) appConfig(w http.ResponseWriter, _ *http.Request) error {
	w.Header().Set("Cache-Control", "no-store")
	return ok(w, map[string]bool{"demo_mode": s.cfg.DemoMode})
}

// Each browser gets its own student account and demonstration balance.
func (s *Server) demoSession(w http.ResponseWriter, r *http.Request) error {
	if !s.cfg.DemoMode {
		return fail(http.StatusNotFound, "Not Found")
	}
	w.Header().Set("Cache-Control", "no-store")
	u, err := s.currentUser(r)
	if err != nil || u.Role != "student" || !strings.HasPrefix(u.Password, "!demo:") {
		id := uuid.NewString()
		now := store.DBTime(store.Now())
		// An invalid password hash prevents password login for visitor accounts.
		result, err := s.db.ExecContext(r.Context(), `INSERT INTO user
			(username, uuid, password, role, name, failed_login_attempts, balance, created_at, updated_at)
			VALUES (?, ?, ?, 'STUDENT', ?, 0, ?, ?, ?)`,
			"demo-"+id, id, "!demo:"+uuid.NewString(), "演示访客", 1000000, now, now)
		if err != nil {
			return err
		}
		userID, err := result.LastInsertId()
		if err != nil {
			return err
		}
		u, err = s.userByID(r.Context(), userID)
		if err != nil {
			return err
		}
	}
	token, err := s.tokens.Issue(u.ID, u.Password)
	if err != nil {
		return err
	}
	return ok(w, map[string]any{"access_token": token, "token_type": "bearer", "role": u.Role, "uuid": u.UUID})
}
