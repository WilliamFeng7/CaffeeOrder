package api

import (
	"context"
	"database/sql"
	"net/http"
	"regexp"
	"unicode/utf8"
)

const (
	storeStatusKey = "store_status"
	bannerKey      = "banner_message"
)

type setting struct {
	Key         string  `json:"key"`
	Value       string  `json:"value"`
	Description *string `json:"description"`
}

func (s *Server) listSettings(w http.ResponseWriter, r *http.Request) error {
	if _, err := s.requireRole(r, "admin"); err != nil {
		return err
	}
	rows, err := s.db.QueryContext(r.Context(), `SELECT "key", value, description FROM systemsetting ORDER BY "key"`)
	if err != nil {
		return err
	}
	defer rows.Close()
	list := []setting{}
	for rows.Next() {
		var st setting
		var desc sql.NullString
		if err := rows.Scan(&st.Key, &st.Value, &desc); err != nil {
			return err
		}
		st.Description = nullable(desc)
		list = append(list, st)
	}
	if err := rows.Err(); err != nil {
		return err
	}
	return ok(w, list)
}

var settingKey = regexp.MustCompile(`^[a-z0-9_]{1,64}$`)

func (s *Server) putSetting(w http.ResponseWriter, r *http.Request) error {
	if _, err := s.requireRole(r, "admin"); err != nil {
		return err
	}
	key := r.PathValue("key")
	if !settingKey.MatchString(key) {
		return fail(http.StatusBadRequest, "Invalid setting key")
	}
	var body struct {
		Value *string `json:"value"`
	}
	if err := decodeJSON(r, &body); err != nil {
		return err
	}
	if body.Value == nil {
		return missingField("body", "value")
	}
	value := *body.Value
	switch {
	case utf8.RuneCountInString(value) > 500:
		return invalidField("body", "value", "String should have at most 500 characters")
	case key == storeStatusKey && value != "open" && value != "closed":
		return fail(http.StatusBadRequest, "store_status must be 'open' or 'closed'")
	case key == bannerKey && utf8.RuneCountInString(value) > 120:
		return fail(http.StatusBadRequest, "banner_message is limited to 120 characters")
	}
	if _, err := s.db.ExecContext(r.Context(),
		`INSERT INTO systemsetting ("key", value) VALUES (?, ?) ON CONFLICT("key") DO UPDATE SET value = excluded.value`,
		key, value); err != nil {
		return err
	}
	var st setting
	var desc sql.NullString
	if err := s.db.QueryRowContext(r.Context(), `SELECT "key", value, description FROM systemsetting WHERE "key" = ?`, key).
		Scan(&st.Key, &st.Value, &desc); err != nil {
		return err
	}
	st.Description = nullable(desc)
	return ok(w, st)
}

// shopState reads the admin's open/closed switch and banner. Missing means open.
func (s *Server) shopState(ctx context.Context) (bool, *string, error) {
	rows, err := s.db.QueryContext(ctx, `SELECT "key", value FROM systemsetting WHERE "key" IN (?, ?)`, storeStatusKey, bannerKey)
	if err != nil {
		return true, nil, err
	}
	defer rows.Close()
	open := true
	var banner *string
	for rows.Next() {
		var k, v string
		if err := rows.Scan(&k, &v); err != nil {
			return true, nil, err
		}
		switch k {
		case storeStatusKey:
			open = v != "closed"
		case bannerKey:
			if v != "" {
				banner = &v
			}
		}
	}
	return open, banner, rows.Err()
}

func (s *Server) shopStatus(w http.ResponseWriter, r *http.Request) error {
	open, banner, err := s.shopState(r.Context())
	if err != nil {
		return err
	}
	message := "Shop is open"
	if !open {
		message = "Shop is closed"
	}
	w.Header().Set("Cache-Control", "no-store")
	return ok(w, map[string]any{"is_open": open, "message": message, "banner": banner})
}
