package api

import (
	"net/http"
	"os"
	"path/filepath"
	"strings"
)

// Serve the Vue build on the API port, with history routes and no listings.
func studentFiles(dir string) http.Handler {
	files := http.FileServer(http.Dir(dir))
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		path := filepath.Clean("/" + r.URL.Path)
		if path == "/api" || path == "/static" || strings.HasPrefix(path, "/api/") || strings.HasPrefix(path, "/static/") {
			http.NotFound(w, r)
			return
		}
		if info, err := os.Stat(filepath.Join(dir, path)); err == nil && !info.IsDir() {
			files.ServeHTTP(w, r)
			return
		}
		if filepath.Ext(path) != "" || path == "/assets" || strings.HasPrefix(path, "/assets/") {
			http.NotFound(w, r)
			return
		}
		w.Header().Set("Cache-Control", "no-cache")
		http.ServeFile(w, r, filepath.Join(dir, "index.html"))
	})
}
