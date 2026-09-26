package api

import (
	"bytes"
	"errors"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"strings"
)

const maxUpload = 5 << 20 // 5 MB

// signatures are the leading bytes each accepted image format starts with.
var signatures = map[string]func([]byte) bool{
	".jpg":  func(b []byte) bool { return bytes.HasPrefix(b, []byte{0xFF, 0xD8, 0xFF}) },
	".jpeg": func(b []byte) bool { return bytes.HasPrefix(b, []byte{0xFF, 0xD8, 0xFF}) },
	".png":  func(b []byte) bool { return bytes.HasPrefix(b, []byte("\x89PNG\r\n\x1a\n")) },
	".webp": func(b []byte) bool { return len(b) >= 12 && string(b[:4]) == "RIFF" && string(b[8:12]) == "WEBP" },
}

// upload stores an admin's product photo under static/uploads. The extension
// must be an image type and the bytes must actually be that type.
func (s *Server) upload(w http.ResponseWriter, r *http.Request) error {
	if _, err := s.requireRole(r, "admin"); err != nil {
		return err
	}
	r.Body = http.MaxBytesReader(w, r.Body, maxUpload+64<<10)
	file, header, err := r.FormFile("file")
	if err != nil {
		var tooBig *http.MaxBytesError
		if errors.As(err, &tooBig) {
			return fail(http.StatusRequestEntityTooLarge, "File too large (max 5MB)")
		}
		return missingField("body", "file")
	}
	defer file.Close()

	ext := strings.ToLower(filepath.Ext(header.Filename))
	matches, allowed := signatures[ext]
	if !allowed {
		return fail(http.StatusBadRequest, "Invalid image format")
	}
	data, err := io.ReadAll(io.LimitReader(file, maxUpload+1))
	if err != nil {
		return fail(http.StatusBadRequest, "Upload failed")
	}
	if len(data) > maxUpload {
		return fail(http.StatusRequestEntityTooLarge, "File too large (max 5MB)")
	}
	if !matches(data) {
		return fail(http.StatusBadRequest, "File content does not match its image type")
	}

	dir := filepath.Join(s.cfg.StaticDir, "uploads")
	if err := os.MkdirAll(dir, 0o755); err != nil {
		return err
	}
	name := newUUID() + ext
	if err := os.WriteFile(filepath.Join(dir, name), data, 0o644); err != nil {
		return err
	}
	return ok(w, map[string]string{"url": "/static/uploads/" + name})
}
