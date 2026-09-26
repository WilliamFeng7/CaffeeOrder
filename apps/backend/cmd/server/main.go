// Command server runs the OTIA Café API: /api/v1 for the three frontends and
// /static for product images.
//
//	server -addr 127.0.0.1:8000 -dir .
//
// Settings come from the environment (or .env in -dir): SECRET_KEY,
// DATABASE_URL, ACCESS_TOKEN_EXPIRE_MINUTES, BACKEND_CORS_ORIGINS,
// FORWARDED_ALLOW_IPS.
package main

import (
	"context"
	"errors"
	"flag"
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/WilliamFeng7/CaffeeOrder/apps/backend/internal/api"
	"github.com/WilliamFeng7/CaffeeOrder/apps/backend/internal/config"
	"github.com/WilliamFeng7/CaffeeOrder/apps/backend/internal/store"
)

func main() {
	addr := flag.String("addr", envOr("ADDR", "127.0.0.1:8000"), "listen address")
	dir := flag.String("dir", ".", "backend directory holding coffee.db, static/ and .env")
	flag.Parse()

	slog.SetDefault(slog.New(slog.NewTextHandler(os.Stdout, nil)))
	if err := run(*addr, *dir); err != nil {
		slog.Error("server stopped", "err", err)
		os.Exit(1)
	}
}

func run(addr, dir string) error {
	cfg, err := config.Load(dir, addr)
	if err != nil {
		return err
	}
	db, err := store.Open(cfg.DatabasePath)
	if err != nil {
		return err
	}
	defer db.Close()

	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()
	if err := store.EnsureSchema(ctx, db); err != nil {
		return err
	}

	srv := &http.Server{
		Addr:              cfg.Addr,
		Handler:           api.New(db, cfg).Handler(),
		ReadHeaderTimeout: 10 * time.Second,
		ReadTimeout:       30 * time.Second,
		WriteTimeout:      60 * time.Second,
		IdleTimeout:       120 * time.Second,
	}
	errs := make(chan error, 1)
	go func() {
		slog.Info("listening", "addr", cfg.Addr, "database", cfg.DatabasePath, "static", cfg.StaticDir)
		errs <- srv.ListenAndServe()
	}()

	select {
	case err := <-errs:
		if !errors.Is(err, http.ErrServerClosed) {
			return err
		}
	case <-ctx.Done():
		slog.Info("shutting down")
		shutdown, cancel := context.WithTimeout(context.Background(), 10*time.Second)
		defer cancel()
		if err := srv.Shutdown(shutdown); err != nil {
			return err
		}
	}
	return nil
}

func envOr(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}
