package api

import (
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"testing"
	"time"

	"github.com/WilliamFeng7/CaffeeOrder/apps/backend/internal/config"
)

func TestDemoDisabledByDefault(t *testing.T) {
	e := newEnv(t)
	code, body := e.request("GET", "/app/config", "", nil)
	if code != 200 || field(body, "demo_mode") != false {
		t.Fatalf("config: %d %v", code, body)
	}
	code, _ = e.request("POST", "/demo/session", "", nil)
	if code != 404 {
		t.Fatalf("disabled demo: %d", code)
	}
	// A real account whose username happens to start with "demo-" still works.
	mustExec(t, e.db, `UPDATE user SET username = 'demo-alice' WHERE username = 'alice'`)
	code, _ = e.request("GET", "/users/me", e.login("demo-alice"), nil)
	if code != 200 {
		t.Fatalf("real account with demo prefix: %d", code)
	}
}

func TestDemoSessionOrderingAndIsolation(t *testing.T) {
	e := newEnv(t, func(c *config.Config) { c.DemoMode = true })
	session := func(token string) (string, string) {
		t.Helper()
		code, body := e.request("POST", "/demo/session", token, nil)
		if code != 200 || field(body, "role") != "student" {
			t.Fatalf("demo session: %d %v", code, body)
		}
		return field(body, "access_token").(string), field(body, "uuid").(string)
	}
	token, id := session("")
	_, reusedID := session(token)
	if id != reusedID {
		t.Fatal("refresh replaced the visitor account")
	}
	otherToken, otherID := session("")
	if id == otherID {
		t.Fatal("visitors share an account")
	}
	code, body := e.request("POST", "/orders/", token, map[string]any{
		"items": []map[string]any{{"menu_item_id": 1, "quantity": 1, "spec": map[string]string{"size": "Regular", "temp": "Hot", "sugar": "Regular"}}},
	})
	if code != 200 && code != 201 {
		t.Fatalf("demo order: %d %v", code, body)
	}
	code, body = e.request("GET", "/orders/me", otherToken, nil)
	if code != 200 || len(body.([]any)) != 0 {
		t.Fatalf("another visitor can see orders: %d %v", code, body)
	}
	code, _ = e.request("GET", "/admin/users", token, nil)
	if code != 403 {
		t.Fatalf("demo reached admin: %d", code)
	}
	_, staffDemoID := session(e.login("admin"))
	if staffDemoID == id || staffDemoID == otherID {
		t.Fatal("staff did not get an independent demo account")
	}
	// Switching the deployment back to normal login also revokes demo tokens.
	disabled := httptest.NewServer(New(e.db, config.Config{SecretKey: "test-secret", TokenTTL: time.Hour}).Handler())
	defer disabled.Close()
	req, _ := http.NewRequest("GET", disabled.URL+"/api/v1/users/me", nil)
	req.Header.Set("Authorization", "Bearer "+token)
	res, err := http.DefaultClient.Do(req)
	if err != nil {
		t.Fatal(err)
	}
	defer res.Body.Close()
	if res.StatusCode != 401 {
		t.Fatalf("disabled demo token: %d", res.StatusCode)
	}
}

func TestStudentFiles(t *testing.T) {
	dir := t.TempDir()
	if err := os.WriteFile(filepath.Join(dir, "index.html"), []byte("<html>menu</html>"), 0644); err != nil {
		t.Fatal(err)
	}
	if err := os.Mkdir(filepath.Join(dir, "assets"), 0755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(dir, "assets", "app.js"), []byte("app"), 0644); err != nil {
		t.Fatal(err)
	}
	e := newEnv(t, func(c *config.Config) { c.StudentWebDir = dir })
	for path, expected := range map[string]int{"/": 200, "/login": 200, "/assets/app.js": 200, "/assets/missing.js": 404, "/api/v1/missing": 404, "/assets/": 404} {
		res, err := http.Get(e.srv.URL + path)
		if err != nil {
			t.Fatal(err)
		}
		res.Body.Close()
		if res.StatusCode != expected {
			t.Errorf("%s: got %d, want %d", path, res.StatusCode, expected)
		}
	}
}
