// Package config reads the server settings from the environment.
//
// The variable names are the ones the Python backend used (SECRET_KEY,
// DATABASE_URL, ACCESS_TOKEN_EXPIRE_MINUTES, BACKEND_CORS_ORIGINS,
// FORWARDED_ALLOW_IPS), so existing .env files and compose files keep working.
package config

import (
	"bufio"
	"crypto/rand"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"log/slog"
	"net"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"time"
)

type Config struct {
	Addr           string
	DatabasePath   string
	StaticDir      string
	StudentWebDir  string
	DemoMode       bool
	SecretKey      string
	TokenTTL       time.Duration
	CORSOrigins    []string
	TrustedProxies []*net.IPNet
}

var defaultOrigins = []string{
	"http://localhost:3000",
	"http://localhost:5173",
	"http://localhost",
	"https://fengweiqin.com",
	"https://fengweiqin.com:8080",
	"https://fengweiqin.com:8081",
	"http://127.0.0.1",
}

// Load builds the configuration. baseDir is where coffee.db, static/ and .env
// live by default (the backend directory).
func Load(baseDir, addr string) (Config, error) {
	loadDotEnv(filepath.Join(baseDir, ".env"))

	cfg := Config{
		Addr:          addr,
		StaticDir:     filepath.Join(baseDir, "static"),
		SecretKey:     os.Getenv("SECRET_KEY"),
		TokenTTL:      7 * 24 * time.Hour,
		CORSOrigins:   defaultOrigins,
		StudentWebDir: os.Getenv("STUDENT_WEB_DIR"),
	}
	if v := os.Getenv("DEMO_MODE"); v != "" {
		var err error
		cfg.DemoMode, err = strconv.ParseBool(v)
		if err != nil {
			return cfg, fmt.Errorf("DEMO_MODE must be a boolean: %w", err)
		}
	}
	if cfg.StudentWebDir != "" {
		if _, err := os.Stat(filepath.Join(cfg.StudentWebDir, "index.html")); err != nil {
			return cfg, fmt.Errorf("STUDENT_WEB_DIR: %w", err)
		}
	}

	path, err := sqlitePath(os.Getenv("DATABASE_URL"))
	if err != nil {
		return cfg, err
	}
	if path == "" {
		path = filepath.Join(baseDir, "coffee.db")
	}
	cfg.DatabasePath = path

	if v := os.Getenv("ACCESS_TOKEN_EXPIRE_MINUTES"); v != "" {
		minutes, err := strconv.Atoi(v)
		if err != nil || minutes <= 0 {
			return cfg, fmt.Errorf("ACCESS_TOKEN_EXPIRE_MINUTES must be a positive integer, got %q", v)
		}
		cfg.TokenTTL = time.Duration(minutes) * time.Minute
	}

	if v := strings.TrimSpace(os.Getenv("BACKEND_CORS_ORIGINS")); v != "" {
		cfg.CORSOrigins = parseList(v)
	}

	proxies := os.Getenv("FORWARDED_ALLOW_IPS")
	if proxies == "" {
		proxies = "127.0.0.1"
	}
	if cfg.TrustedProxies, err = parseCIDRs(proxies); err != nil {
		return cfg, err
	}

	if cfg.SecretKey == "" {
		cfg.SecretKey = randomKey()
		slog.Warn("SECRET_KEY is not set: using a temporary key, sessions will not survive a restart")
	}
	return cfg, nil
}

// sqlitePath accepts the SQLAlchemy URL the Python backend used
// ("sqlite+aiosqlite:////data/coffee.db") as well as a plain file path.
func sqlitePath(url string) (string, error) {
	url = strings.TrimSpace(url)
	if url == "" {
		return "", nil
	}
	for _, prefix := range []string{"sqlite+aiosqlite://", "sqlite://"} {
		if strings.HasPrefix(url, prefix) {
			rest := strings.TrimPrefix(url, prefix)
			// sqlite:///relative/path and sqlite:////absolute/path
			if strings.HasPrefix(rest, "//") {
				return rest[1:], nil
			}
			return strings.TrimPrefix(rest, "/"), nil
		}
	}
	if strings.Contains(url, "://") {
		return "", fmt.Errorf("DATABASE_URL %q: only SQLite is supported", url)
	}
	return url, nil
}

// parseList reads either a JSON array (what pydantic-settings expected) or a
// comma-separated list.
func parseList(v string) []string {
	var list []string
	if strings.HasPrefix(v, "[") && json.Unmarshal([]byte(v), &list) == nil {
		return list
	}
	for _, item := range strings.Split(v, ",") {
		if item = strings.TrimSpace(item); item != "" {
			list = append(list, item)
		}
	}
	return list
}

func parseCIDRs(v string) ([]*net.IPNet, error) {
	var nets []*net.IPNet
	for _, item := range parseList(v) {
		if item == "*" {
			_, all4, _ := net.ParseCIDR("0.0.0.0/0")
			_, all6, _ := net.ParseCIDR("::/0")
			nets = append(nets, all4, all6)
			continue
		}
		if !strings.Contains(item, "/") {
			if ip := net.ParseIP(item); ip != nil && ip.To4() != nil {
				item += "/32"
			} else {
				item += "/128"
			}
		}
		_, n, err := net.ParseCIDR(item)
		if err != nil {
			return nil, fmt.Errorf("FORWARDED_ALLOW_IPS: %w", err)
		}
		nets = append(nets, n)
	}
	return nets, nil
}

// loadDotEnv sets KEY=VALUE pairs from path without overriding variables that
// are already present in the real environment.
func loadDotEnv(path string) {
	f, err := os.Open(path)
	if err != nil {
		return
	}
	defer f.Close()
	scanner := bufio.NewScanner(f)
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		key, value, ok := strings.Cut(line, "=")
		if !ok {
			continue
		}
		key = strings.TrimSpace(strings.TrimPrefix(key, "export "))
		value = strings.Trim(strings.TrimSpace(value), `"'`)
		if _, exists := os.LookupEnv(key); !exists {
			os.Setenv(key, value)
		}
	}
}

func randomKey() string {
	buf := make([]byte, 32)
	if _, err := rand.Read(buf); err != nil {
		panic(err)
	}
	return base64.RawURLEncoding.EncodeToString(buf)
}
