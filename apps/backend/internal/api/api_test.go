package api

import (
	"bytes"
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"mime/multipart"
	"net/http"
	"net/http/httptest"
	"net/url"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"testing"
	"time"

	"github.com/WilliamFeng7/CaffeeOrder/apps/backend/internal/auth"
	"github.com/WilliamFeng7/CaffeeOrder/apps/backend/internal/config"
	"github.com/WilliamFeng7/CaffeeOrder/apps/backend/internal/store"
)

const testPassword = "Test-pass-2026"

var (
	hashOnce sync.Once
	testHash string
)

type env struct {
	t      *testing.T
	srv    *httptest.Server
	db     *sql.DB
	static string
}

func newEnv(t *testing.T) *env {
	t.Helper()
	hashOnce.Do(func() { testHash, _ = auth.HashPassword(testPassword) })
	dir := t.TempDir()
	db, err := store.Open(filepath.Join(dir, "test.db"))
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { db.Close() })
	if err := store.EnsureSchema(context.Background(), db); err != nil {
		t.Fatal(err)
	}
	static := filepath.Join(dir, "static")
	cfg := config.Config{DatabasePath: filepath.Join(dir, "test.db"), StaticDir: static, SecretKey: "test-secret", TokenTTL: time.Hour}
	srv := httptest.NewServer(New(db, cfg).Handler())
	t.Cleanup(srv.Close)

	now := store.DBTime(store.Now())
	users := []struct {
		name, role string
		balance    int
	}{{"admin", "ADMIN", 0}, {"alice", "STUDENT", 10000}, {"bob", "STUDENT", 500}, {"barista", "BARISTA", 0}}
	for i, u := range users {
		mustExec(t, db, `INSERT INTO user (username, uuid, password, role, name, failed_login_attempts, balance, created_at, updated_at)
			VALUES (?, ?, ?, ?, ?, 0, ?, ?, ?)`, u.name, fmt.Sprintf("uuid-%d", i), testHash, u.role, u.name, u.balance, now, now)
	}
	mustExec(t, db, `INSERT INTO menuitem (id, name, name_cn, price, category, image_path, is_active, is_recommend, inventory_count) VALUES
		(1, 'Latte', '拿铁', 1500, 'coffee', '/static/art/latte.svg', 1, 1, 10),
		(2, 'Cake', '蛋糕', 2200, 'bakery', '/static/art/cheesecake.svg', 1, 0, 1),
		(3, 'Hidden', NULL, 999, 'coffee', '/static/default.png', 0, 0, 5)`)
	return &env{t: t, srv: srv, db: db, static: static}
}

func mustExec(t *testing.T, db *sql.DB, q string, args ...any) {
	t.Helper()
	if _, err := db.Exec(q, args...); err != nil {
		t.Fatal(err)
	}
}

func (e *env) scalar(q string, args ...any) int64 {
	e.t.Helper()
	var n sql.NullInt64
	if err := e.db.QueryRow(q, args...).Scan(&n); err != nil {
		e.t.Fatal(err)
	}
	return n.Int64
}

func (e *env) request(method, path, token string, body any) (int, any) {
	e.t.Helper()
	var reader *bytes.Reader
	contentType := "application/json"
	switch b := body.(type) {
	case nil:
		reader = bytes.NewReader(nil)
	case url.Values:
		reader, contentType = bytes.NewReader([]byte(b.Encode())), "application/x-www-form-urlencoded"
	default:
		raw, _ := json.Marshal(b)
		reader = bytes.NewReader(raw)
	}
	req, _ := http.NewRequest(method, e.srv.URL+"/api/v1"+path, reader)
	req.Header.Set("Content-Type", contentType)
	if token != "" {
		req.Header.Set("Authorization", "Bearer "+token)
	}
	res, err := http.DefaultClient.Do(req)
	if err != nil {
		e.t.Fatal(err)
	}
	defer res.Body.Close()
	var out any
	_ = json.NewDecoder(res.Body).Decode(&out)
	return res.StatusCode, out
}

func (e *env) login(user string) string {
	e.t.Helper()
	code, body := e.request("POST", "/login/access-token", "", url.Values{"username": {user}, "password": {testPassword}})
	if code != 200 {
		e.t.Fatalf("login %s: %d %v", user, code, body)
	}
	return body.(map[string]any)["access_token"].(string)
}

func field(v any, path ...string) any {
	for _, key := range path {
		m, ok := v.(map[string]any)
		if !ok {
			return nil
		}
		v = m[key]
	}
	return v
}

func (e *env) order(token string, items ...map[string]any) (int, any) {
	return e.request("POST", "/orders/", token, map[string]any{"items": items})
}

func TestLoginLockoutLadder(t *testing.T) {
	e := newEnv(t)
	code, body := e.request("POST", "/login/access-token", "", url.Values{"username": {"alice"}, "password": {testPassword}})
	if code != 200 || field(body, "role") != "student" || field(body, "username") != "alice" {
		t.Fatalf("login = %d %v", code, body)
	}
	for i := 1; i <= 4; i++ {
		code, body = e.request("POST", "/login/access-token", "", url.Values{"username": {"alice"}, "password": {"wrong-pass"}})
		if code != 401 || field(body, "detail", "code") != "failed" || field(body, "detail", "attempts_left") != float64(5-i) {
			t.Fatalf("failure %d = %d %v", i, code, body)
		}
	}
	e.request("POST", "/login/access-token", "", url.Values{"username": {"alice"}, "password": {"wrong-pass"}})
	code, body = e.request("POST", "/login/access-token", "", url.Values{"username": {"alice"}, "password": {testPassword}})
	if code != 403 || field(body, "detail", "code") != "locked" || field(body, "detail", "unlock_at") == nil {
		t.Fatalf("after 5 failures = %d %v, want 403 locked", code, body)
	}
}

func TestOrderLifecycleMovesMoneyAndStock(t *testing.T) {
	e := newEnv(t)
	alice, barista, admin := e.login("alice"), e.login("barista"), e.login("admin")

	code, body := e.order(alice,
		map[string]any{"menu_item_id": 1, "quantity": 2, "spec": map[string]string{"temp": "Hot"}},
		map[string]any{"menu_item_id": 1, "spec": map[string]string{"temp": "Hot"}})
	if code != 200 || field(body, "total_amount") != 4500.0 || field(body, "status") != "created" || field(body, "pickup_number") != 1.0 {
		t.Fatalf("order = %d %v", code, body)
	}
	items := field(body, "items").([]any)
	if len(items) != 1 || field(items[0], "quantity") != 3.0 {
		t.Fatalf("identical lines were not merged: %v", items)
	}
	id := int(field(body, "id").(float64))
	if got := e.scalar(`SELECT balance FROM user WHERE username = 'alice'`); got != 5500 {
		t.Fatalf("balance after order = %d, want 5500", got)
	}
	if got := e.scalar(`SELECT inventory_count FROM menuitem WHERE id = 1`); got != 7 {
		t.Fatalf("stock after order = %d, want 7", got)
	}

	for _, step := range []string{"processing", "ready"} {
		if code, body := e.request("PATCH", fmt.Sprintf("/orders/%d/status", id), barista, map[string]string{"status": step}); code != 200 || field(body, "status") != step {
			t.Fatalf("%s = %d %v", step, code, body)
		}
	}
	if code, _ := e.request("PATCH", fmt.Sprintf("/orders/%d/status", id), barista, map[string]string{"status": "refunded"}); code != 403 {
		t.Fatalf("barista refund = %d, want 403", code)
	}
	if code, body := e.request("POST", fmt.Sprintf("/orders/%d/complete", id), barista, nil); code != 200 || field(body, "is_completed") != true {
		t.Fatalf("complete = %d %v", code, body)
	}

	// Five admins refunding at once: exactly one pays out.
	var wg sync.WaitGroup
	var mu sync.Mutex
	wins := 0
	for i := 0; i < 5; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			if code, _ := e.request("PATCH", fmt.Sprintf("/orders/%d/status", id), admin, map[string]string{"status": "refunded"}); code == 200 {
				mu.Lock()
				wins++
				mu.Unlock()
			}
		}()
	}
	wg.Wait()
	if wins != 1 {
		t.Fatalf("%d refunds succeeded, want exactly 1", wins)
	}
	if got := e.scalar(`SELECT balance FROM user WHERE username = 'alice'`); got != 10000 {
		t.Fatalf("balance after refund = %d, want 10000", got)
	}
	if got := e.scalar(`SELECT inventory_count FROM menuitem WHERE id = 1`); got != 10 {
		t.Fatalf("stock after refund = %d, want 10", got)
	}
	if got := e.scalar(`SELECT count(*) FROM "transaction" WHERE type = 'refund'`); got != 1 {
		t.Fatalf("%d refund rows, want 1", got)
	}
}

func TestLastItemCannotBeSoldTwice(t *testing.T) {
	e := newEnv(t)
	alice := e.login("alice")
	var wg sync.WaitGroup
	var mu sync.Mutex
	sold := 0
	for i := 0; i < 5; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			if code, _ := e.order(alice, map[string]any{"menu_item_id": 2}); code == 200 {
				mu.Lock()
				sold++
				mu.Unlock()
			}
		}()
	}
	wg.Wait()
	if sold != 1 || e.scalar(`SELECT inventory_count FROM menuitem WHERE id = 2`) != 0 {
		t.Fatalf("sold %d cakes from a stock of 1", sold)
	}
	if got := e.scalar(`SELECT count(DISTINCT pickup_number) FROM "order"`); got != 1 {
		t.Fatalf("pickup numbers = %d", got)
	}
}

func TestOrderRejections(t *testing.T) {
	e := newEnv(t)
	alice, bob, admin := e.login("alice"), e.login("bob"), e.login("admin")
	cases := []struct {
		name  string
		token string
		items []map[string]any
		code  int
	}{
		{"hidden product", alice, []map[string]any{{"menu_item_id": 3}}, 400},
		{"unknown product", alice, []map[string]any{{"menu_item_id": 99}}, 400},
		{"quantity 0", alice, []map[string]any{{"menu_item_id": 1, "quantity": 0}}, 422},
		{"empty", alice, []map[string]any{}, 422},
		{"not enough balance", bob, []map[string]any{{"menu_item_id": 1}}, 402},
	}
	for _, c := range cases {
		if code, body := e.order(c.token, c.items...); code != c.code {
			t.Errorf("%s = %d %v, want %d", c.name, code, body, c.code)
		}
	}
	if got := e.scalar(`SELECT inventory_count FROM menuitem WHERE id = 1`); got != 10 {
		t.Fatalf("a rejected order changed stock: %d", got)
	}

	e.request("PUT", "/settings/store_status", admin, map[string]string{"value": "closed"})
	code, body := e.order(alice, map[string]any{"menu_item_id": 1})
	if code != 409 || !strings.Contains(fmt.Sprint(field(body, "detail")), "closed") {
		t.Fatalf("order while closed = %d %v", code, body)
	}
	if _, body := e.request("GET", "/shop/status", "", nil); field(body, "is_open") != false {
		t.Fatalf("shop status = %v", body)
	}
}

func TestCancelOnlyOwnNewOrders(t *testing.T) {
	e := newEnv(t)
	alice, bob, barista := e.login("alice"), e.login("bob"), e.login("barista")
	_, body := e.order(alice, map[string]any{"menu_item_id": 1})
	id := int(field(body, "id").(float64))
	if code, _ := e.request("POST", fmt.Sprintf("/orders/%d/cancel", id), bob, nil); code != 403 {
		t.Fatalf("cancel by another student = %d", code)
	}
	if code, body := e.request("POST", fmt.Sprintf("/orders/%d/cancel", id), alice, nil); code != 200 || field(body, "status") != "refunded" {
		t.Fatalf("cancel = %d %v", code, body)
	}
	_, body = e.order(alice, map[string]any{"menu_item_id": 1})
	id = int(field(body, "id").(float64))
	e.request("PATCH", fmt.Sprintf("/orders/%d/status", id), barista, map[string]string{"status": "processing"})
	if code, _ := e.request("POST", fmt.Sprintf("/orders/%d/cancel", id), alice, nil); code != 400 {
		t.Fatalf("cancel while processing = %d, want 400", code)
	}
}

func TestAdminBalancesAreCentsAndLedgered(t *testing.T) {
	e := newEnv(t)
	admin := e.login("admin")
	code, body := e.request("POST", "/admin/users", admin, map[string]any{
		"username": "carol", "password": "Carol-pass-2026", "name": "Carol", "role": "student", "balance": 12345})
	if code != 200 || field(body, "balance") != 12345.0 || field(body, "role") != "student" {
		t.Fatalf("create = %d %v", code, body)
	}
	id := int(field(body, "id").(float64))
	if got := e.scalar(`SELECT amount FROM "transaction" WHERE user_id = ? AND type = 'deposit'`, id); got != 12345 {
		t.Fatalf("opening balance ledger = %d", got)
	}
	if code, body := e.request("PUT", fmt.Sprintf("/admin/users/%d", id), admin, map[string]any{"balance": 20000}); code != 200 || field(body, "balance") != 20000.0 {
		t.Fatalf("update = %d %v", code, body)
	}
	if got := e.scalar(`SELECT amount FROM "transaction" WHERE user_id = ? AND type = 'adjustment'`, id); got != 7655 {
		t.Fatalf("adjustment ledger = %d, want 7655", got)
	}
	if code, body := e.request("POST", fmt.Sprintf("/users/%d/deposit?amount=500", id), admin, nil); code != 200 || field(body, "balance") != 20500.0 {
		t.Fatalf("deposit = %d %v", code, body)
	}
	if code, _ := e.request("POST", "/admin/users", admin, map[string]any{"username": "dave", "password": "Dave-pass-2026", "name": "D", "role": "boss"}); code != 422 {
		t.Fatalf("invalid role = %d, want 422", code)
	}
}

func TestPasswordChangeRevokesOldTokens(t *testing.T) {
	e := newEnv(t)
	old := e.login("alice")
	code, body := e.request("PUT", "/users/me/password", old, map[string]string{"old_password": testPassword, "new_password": "Newer-pass-2026"})
	if code != 200 {
		t.Fatalf("change = %d %v", code, body)
	}
	if code, _ := e.request("GET", "/users/me", old, nil); code != 401 {
		t.Fatalf("old token after change = %d, want 401", code)
	}
	fresh := field(body, "access_token").(string)
	if code, _ := e.request("GET", "/users/me", fresh, nil); code != 200 {
		t.Fatalf("new token = %d", code)
	}
}

func TestStaffFeedsAreNotCappedAtTwenty(t *testing.T) {
	e := newEnv(t)
	alice, barista := e.login("alice"), e.login("barista")
	mustExec(t, e.db, `UPDATE menuitem SET inventory_count = 100, price = 100 WHERE id = 1`)
	for i := 0; i < 25; i++ {
		if code, body := e.order(alice, map[string]any{"menu_item_id": 1}); code != 200 {
			t.Fatalf("order %d = %d %v", i, code, body)
		}
	}
	if _, body := e.request("GET", "/admin/orders", barista, nil); len(body.([]any)) != 25 {
		t.Fatalf("/admin/orders returned %d orders, want 25", len(body.([]any)))
	}
	if _, body := e.request("GET", "/orders/sync?since=0", barista, nil); len(body.([]any)) != 25 {
		t.Fatalf("/orders/sync returned %d orders, want 25", len(body.([]any)))
	}
	if code, _ := e.request("GET", "/orders/sync?since=0", alice, nil); code != 403 {
		t.Fatalf("student on sync = %d, want 403", code)
	}
}

func TestUploadChecksFileContent(t *testing.T) {
	e := newEnv(t)
	admin := e.login("admin")
	upload := func(name string, content []byte) (int, any) {
		var buf bytes.Buffer
		mw := multipart.NewWriter(&buf)
		part, _ := mw.CreateFormFile("file", name)
		part.Write(content)
		mw.Close()
		req, _ := http.NewRequest("POST", e.srv.URL+"/api/v1/upload", &buf)
		req.Header.Set("Content-Type", mw.FormDataContentType())
		req.Header.Set("Authorization", "Bearer "+admin)
		res, err := http.DefaultClient.Do(req)
		if err != nil {
			t.Fatal(err)
		}
		defer res.Body.Close()
		var out any
		json.NewDecoder(res.Body).Decode(&out)
		return res.StatusCode, out
	}
	if code, _ := upload("fake.jpg", []byte("<html>not an image</html>")); code != 400 {
		t.Fatalf("fake jpg = %d, want 400", code)
	}
	if code, _ := upload("script.svg", []byte("<svg/>")); code != 400 {
		t.Fatalf("svg = %d, want 400", code)
	}
	code, body := upload("photo.png", append([]byte("\x89PNG\r\n\x1a\n"), make([]byte, 64)...))
	if code != 200 {
		t.Fatalf("png = %d %v", code, body)
	}
	name := strings.TrimPrefix(field(body, "url").(string), "/static/uploads/")
	if _, err := os.Stat(filepath.Join(e.static, "uploads", name)); err != nil {
		t.Fatalf("uploaded file missing: %v", err)
	}
}

func TestErrorShapesMatchFastAPI(t *testing.T) {
	e := newEnv(t)
	code, body := e.request("GET", "/users/me", "", nil)
	if code != 401 || field(body, "detail") != "Not authenticated" {
		t.Fatalf("no token = %d %v", code, body)
	}
	code, body = e.request("GET", "/users/me", "not-a-token", nil)
	if code != 401 || !strings.Contains(fmt.Sprint(field(body, "detail")), "Could not validate credentials") {
		t.Fatalf("bad token = %d %v", code, body)
	}
	code, body = e.request("POST", "/orders/", e.login("alice"), map[string]any{"items": []map[string]any{{"menu_item_id": 1, "quantity": 100}}})
	detail, _ := field(body, "detail").([]any)
	if code != 422 || len(detail) != 1 || field(body, "message") != "Changes validation failed" {
		t.Fatalf("validation = %d %v", code, body)
	}
	if code, _ := e.request("GET", "/nope", "", nil); code != 404 {
		t.Fatalf("unknown route = %d", code)
	}
}
