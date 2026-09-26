// Package api is the HTTP layer: routes, authentication and the JSON shapes
// the Student, Barista and Admin frontends expect.
package api

import (
	"database/sql"
	"errors"
	"log/slog"
	"net/http"
	"os"
	"path/filepath"
	"slices"
	"strings"
	"sync"
	"time"

	"github.com/WilliamFeng7/CaffeeOrder/apps/backend/internal/auth"
	"github.com/WilliamFeng7/CaffeeOrder/apps/backend/internal/config"
	"github.com/WilliamFeng7/CaffeeOrder/apps/backend/internal/orders"
)

type Server struct {
	db      *sql.DB
	cfg     config.Config
	tokens  auth.Tokens
	limiter *auth.LoginLimiter
	orders  *orders.Service
	menu    menuCache
}

func New(db *sql.DB, cfg config.Config) *Server {
	s := &Server{
		db:      db,
		cfg:     cfg,
		tokens:  auth.Tokens{Secret: []byte(cfg.SecretKey), TTL: cfg.TokenTTL},
		limiter: auth.NewLoginLimiter(),
	}
	s.orders = orders.NewService(db, s.menu.invalidate)
	return s
}

// Handler returns the full HTTP handler: API routes, /static and middleware.
func (s *Server) Handler() http.Handler {
	mux := http.NewServeMux()
	route := func(pattern string, h handlerFunc) {
		mux.Handle(pattern, handle(h))
		// FastAPI answered "/menu" and "/menu/" alike; keep both spellings working.
		method, path, _ := strings.Cut(pattern, " ")
		if strings.HasSuffix(path, "/{$}") {
			mux.Handle(method+" "+strings.TrimSuffix(path, "/{$}"), handle(h))
		}
	}
	const v1 = "/api/v1"

	route("POST "+v1+"/login/access-token", s.login)

	route("GET "+v1+"/users/me", s.getMe)
	route("PUT "+v1+"/users/me", s.updateMe)
	route("PUT "+v1+"/users/me/password", s.changePassword)
	route("POST "+v1+"/users/{id}/deposit", s.deposit)

	route("GET "+v1+"/menu/{$}", s.listMenu)
	route("GET "+v1+"/shop/status", s.shopStatus)

	route("GET "+v1+"/orders/me", s.myOrders)
	route("POST "+v1+"/orders/{$}", s.createOrder)
	route("POST "+v1+"/orders/{id}/cancel", s.cancelOrder)
	route("POST "+v1+"/orders/{id}/complete", s.completeOrder)
	route("GET "+v1+"/orders/sync", s.syncOrders)
	route("PATCH "+v1+"/orders/{id}/status", s.patchOrderStatus)

	route("GET "+v1+"/admin/stats", s.dashboardStats)
	route("GET "+v1+"/admin/users", s.listUsers)
	route("POST "+v1+"/admin/users", s.createUser)
	route("PUT "+v1+"/admin/users/{id}", s.updateUser)
	route("DELETE "+v1+"/admin/users/{id}", s.deleteUser)
	route("GET "+v1+"/admin/products", s.listProducts)
	route("POST "+v1+"/admin/products", s.createProduct)
	route("PUT "+v1+"/admin/products/{id}", s.updateProduct)
	route("DELETE "+v1+"/admin/products/{id}", s.deleteProduct)
	route("GET "+v1+"/admin/orders", s.adminOrders)
	route("PUT "+v1+"/admin/orders/{id}/status", s.adminOrderStatus)

	route("GET "+v1+"/finance/stats", s.financeStats)
	route("GET "+v1+"/finance/chart", s.financeChart)
	route("GET "+v1+"/finance/transactions", s.financeTransactions)

	route("GET "+v1+"/settings/{$}", s.listSettings)
	route("PUT "+v1+"/settings/{key}", s.putSetting)

	route("POST "+v1+"/upload", s.upload)

	mux.Handle("GET /static/", http.StripPrefix("/static/", staticFiles(s.cfg.StaticDir)))
	mux.Handle("GET /{$}", handle(func(w http.ResponseWriter, _ *http.Request) error {
		return ok(w, map[string]string{"message": "Welcome to School Coffee System API"})
	}))
	mux.Handle("/", handle(func(http.ResponseWriter, *http.Request) error {
		return fail(http.StatusNotFound, "Not Found")
	}))

	return s.recoverer(s.logRequests(s.cors(mux)))
}

// --- authentication -------------------------------------------------------------

var bearer = http.Header{"Www-Authenticate": {"Bearer"}}

var errCredentials = &Error{
	Status: http.StatusUnauthorized,
	Detail: "无法验证凭证 (Could not validate credentials)",
	Header: bearer,
}

// currentUser resolves the bearer token to a user. A token issued before the
// user's latest password change no longer matches the password version.
func (s *Server) currentUser(r *http.Request) (*User, error) {
	scheme, token, found := strings.Cut(r.Header.Get("Authorization"), " ")
	if !found || !strings.EqualFold(scheme, "Bearer") || strings.TrimSpace(token) == "" {
		return nil, &Error{Status: http.StatusUnauthorized, Detail: "Not authenticated", Header: bearer}
	}
	id, pwv, err := s.tokens.Parse(strings.TrimSpace(token))
	if err != nil {
		return nil, errCredentials
	}
	u, err := s.userByID(r.Context(), id)
	if errors.Is(err, sql.ErrNoRows) {
		return nil, errCredentials
	}
	if err != nil {
		return nil, err
	}
	if auth.PasswordVersion(u.Password) != pwv {
		return nil, errCredentials
	}
	return u, nil
}

// requireRole admits only the listed roles ("admin", "barista", "student").
func (s *Server) requireRole(r *http.Request, roles ...string) (*User, error) {
	u, err := s.currentUser(r)
	if err != nil {
		return nil, err
	}
	if !slices.Contains(roles, u.Role) {
		return nil, fail(http.StatusForbidden, "The user doesn't have enough privileges")
	}
	return u, nil
}

// --- middleware -------------------------------------------------------------------

func (s *Server) cors(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		origin := r.Header.Get("Origin")
		if origin != "" && slices.Contains(s.cfg.CORSOrigins, origin) {
			h := w.Header()
			h.Set("Access-Control-Allow-Origin", origin)
			h.Set("Access-Control-Allow-Credentials", "true")
			h.Add("Vary", "Origin")
			if r.Method == http.MethodOptions && r.Header.Get("Access-Control-Request-Method") != "" {
				h.Set("Access-Control-Allow-Methods", "DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT")
				if req := r.Header.Get("Access-Control-Request-Headers"); req != "" {
					h.Set("Access-Control-Allow-Headers", req)
				}
				h.Set("Access-Control-Max-Age", "600")
				w.WriteHeader(http.StatusOK)
				return
			}
		}
		next.ServeHTTP(w, r)
	})
}

type statusRecorder struct {
	http.ResponseWriter
	status int
}

func (r *statusRecorder) WriteHeader(code int) {
	r.status = code
	r.ResponseWriter.WriteHeader(code)
}

func (s *Server) logRequests(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		rec := &statusRecorder{ResponseWriter: w, status: http.StatusOK}
		w.Header().Set("X-Content-Type-Options", "nosniff")
		next.ServeHTTP(rec, r)
		if strings.HasPrefix(r.URL.Path, "/static/") && rec.status < 400 {
			return
		}
		slog.Info("request", "method", r.Method, "path", r.URL.Path, "status", rec.status,
			"ms", time.Since(start).Milliseconds(), "ip", auth.ClientIP(r, s.cfg.TrustedProxies))
	})
}

func (s *Server) recoverer(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		defer func() {
			if v := recover(); v != nil {
				if v == http.ErrAbortHandler {
					panic(v)
				}
				slog.Error("panic", "method", r.Method, "path", r.URL.Path, "panic", v)
				writeJSON(w, http.StatusInternalServerError, map[string]string{"detail": "Internal Server Error"})
			}
		}()
		next.ServeHTTP(w, r)
	})
}

// staticFiles serves files under dir but never directory listings.
func staticFiles(dir string) http.Handler {
	fs := http.FileServer(http.Dir(dir))
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		info, err := os.Stat(filepath.Join(dir, filepath.FromSlash(filepath.Clean("/"+r.URL.Path))))
		if err != nil || info.IsDir() {
			writeJSON(w, http.StatusNotFound, map[string]string{"detail": "Not Found"})
			return
		}
		fs.ServeHTTP(w, r)
	})
}

// --- menu cache ---------------------------------------------------------------------

// menuCache holds the public menu for up to five minutes. Anything that changes
// stock or a product (orders, refunds, admin edits) invalidates it.
type menuCache struct {
	mu       sync.Mutex
	items    []MenuItem
	loadedAt time.Time
}

func (c *menuCache) invalidate() {
	c.mu.Lock()
	c.items = nil
	c.mu.Unlock()
}
