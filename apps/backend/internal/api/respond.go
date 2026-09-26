package api

import (
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"log/slog"
	"math"
	"net/http"
	"reflect"
	"strconv"
	"strings"
)

var typeOfInt = reflect.TypeOf(int64(0))

// Error is an HTTP error in FastAPI's shape: {"detail": ...}. The frontends
// read detail as either a string or, for login, a {code, message, ...} object.
type Error struct {
	Status int
	Detail any
	Header http.Header
}

func (e *Error) Error() string { return fmt.Sprintf("%d: %v", e.Status, e.Detail) }

func fail(status int, detail any) *Error { return &Error{Status: status, Detail: detail} }

// validation builds FastAPI's 422 body for one failed field.
func validation(loc []any, msg, kind string) *Error {
	return fail(http.StatusUnprocessableEntity, []map[string]any{{"type": kind, "loc": loc, "msg": msg}})
}

func invalidField(where, field, msg string) *Error {
	return validation([]any{where, field}, "Value error, "+msg, "value_error")
}

func missingField(where, field string) *Error {
	return validation([]any{where, field}, "Field required", "missing")
}

type handlerFunc func(w http.ResponseWriter, r *http.Request) error

// handle turns a handler's error into the matching JSON response.
func handle(h handlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		err := h(w, r)
		if err == nil {
			return
		}
		var apiErr *Error
		var domain interface {
			StatusCode() int
			Payload() any
		}
		switch {
		case errors.As(err, &apiErr):
		case errors.As(err, &domain):
			apiErr = fail(domain.StatusCode(), domain.Payload())
		default:
			slog.Error("request failed", "method", r.Method, "path", r.URL.Path, "err", err)
			apiErr = fail(http.StatusInternalServerError, "Internal Server Error")
		}
		for k, v := range apiErr.Header {
			w.Header()[k] = v
		}
		body := map[string]any{"detail": apiErr.Detail}
		if apiErr.Status == http.StatusUnprocessableEntity {
			body["message"] = "Changes validation failed"
		}
		writeJSON(w, apiErr.Status, body)
	}
}

func writeJSON(w http.ResponseWriter, status int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	enc := json.NewEncoder(w)
	enc.SetEscapeHTML(false)
	if err := enc.Encode(v); err != nil {
		slog.Error("encode response", "err", err)
	}
}

func ok(w http.ResponseWriter, v any) error {
	writeJSON(w, http.StatusOK, v)
	return nil
}

const maxBody = 1 << 20

// decodeJSON reads the request body into dst. Unknown fields are ignored, as
// pydantic did.
func decodeJSON(r *http.Request, dst any) error {
	body, err := io.ReadAll(io.LimitReader(r.Body, maxBody+1))
	if err != nil {
		return fail(http.StatusBadRequest, "Could not read request body")
	}
	if len(body) > maxBody {
		return fail(http.StatusRequestEntityTooLarge, "Request body too large")
	}
	if len(strings.TrimSpace(string(body))) == 0 {
		return validation([]any{"body"}, "Field required", "missing")
	}
	if err := json.Unmarshal(body, dst); err != nil {
		var typeErr *json.UnmarshalTypeError
		if errors.As(err, &typeErr) {
			return validation([]any{"body", typeErr.Field}, "Input should be a valid "+typeErr.Type.String(), "type_error")
		}
		return validation([]any{"body"}, "JSON decode error", "json_invalid")
	}
	return nil
}

// Number accepts a JSON number or numeric string (pydantic's lax mode) and
// rounds it to an integer.
type Number struct {
	Value int64
	Set   bool
	Null  bool
}

func (n *Number) UnmarshalJSON(b []byte) error {
	n.Set = true
	s := strings.Trim(strings.TrimSpace(string(b)), `"`)
	if s == "null" {
		n.Null = true
		return nil
	}
	f, err := strconv.ParseFloat(s, 64)
	if err != nil || math.IsNaN(f) || math.IsInf(f, 0) {
		return &json.UnmarshalTypeError{Value: s, Type: typeOfInt}
	}
	n.Value = int64(math.Round(f))
	return nil
}

// Optional tracks whether a string field was present and whether it was null,
// which pydantic's exclude_unset partial updates depended on.
type Optional struct {
	Value string
	Set   bool
	Null  bool
}

func (o *Optional) UnmarshalJSON(b []byte) error {
	o.Set = true
	if string(b) == "null" {
		o.Null = true
		return nil
	}
	return json.Unmarshal(b, &o.Value)
}

// Ptr is the value to store: nil for null, the string otherwise.
func (o Optional) Ptr() *string {
	if o.Null {
		return nil
	}
	v := o.Value
	return &v
}

type page struct{ skip, limit int }

// pagination reads skip/limit with the bounds the Python backend enforced
// (limit 1..200), falling back to defaultLimit.
func pagination(r *http.Request, defaultLimit int) (page, error) {
	p := page{skip: 0, limit: defaultLimit}
	q := r.URL.Query()
	if v := q.Get("skip"); v != "" {
		n, err := strconv.Atoi(v)
		if err != nil || n < 0 {
			return p, validation([]any{"query", "skip"}, "Input should be greater than or equal to 0", "greater_than_equal")
		}
		p.skip = n
	}
	if v := q.Get("limit"); v != "" {
		n, err := strconv.Atoi(v)
		if err != nil || n < 1 {
			return p, validation([]any{"query", "limit"}, "Input should be greater than or equal to 1", "greater_than_equal")
		}
		if n > 200 {
			return p, validation([]any{"query", "limit"}, "Input should be less than or equal to 200", "less_than_equal")
		}
		p.limit = n
	}
	return p, nil
}

func pathID(r *http.Request, name string) (int64, error) {
	id, err := strconv.ParseInt(r.PathValue(name), 10, 64)
	if err != nil {
		return 0, validation([]any{"path", name}, "Input should be a valid integer", "int_parsing")
	}
	return id, nil
}
