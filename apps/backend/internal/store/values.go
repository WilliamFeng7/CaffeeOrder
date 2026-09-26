package store

import (
	"database/sql/driver"
	"fmt"
	"strings"
	"time"
)

// CST is Beijing time. A fixed zone, so the binary needs no tzdata.
var CST = time.FixedZone("CST", 8*3600)

// Now is the current Beijing time, truncated to microseconds like Python's datetime.
func Now() time.Time {
	return time.Now().In(CST).Truncate(time.Microsecond)
}

// StartOfDay is midnight (Beijing) of t's day.
func StartOfDay(t time.Time) time.Time {
	t = t.In(CST)
	return time.Date(t.Year(), t.Month(), t.Day(), 0, 0, 0, 0, CST)
}

// DBTime formats t as the naive wall-clock string SQLAlchemy stored:
// "2006-01-02 15:04:05.000000".
func DBTime(t time.Time) string {
	return t.In(CST).Format("2006-01-02 15:04:05.000000")
}

// Time scans a DATETIME column whether the driver hands back text or a
// time.Time. The stored value is naive Beijing wall-clock time.
type Time struct {
	Time  time.Time
	Valid bool
}

var layouts = []string{
	"2006-01-02 15:04:05.999999999",
	"2006-01-02T15:04:05.999999999",
	"2006-01-02 15:04:05",
	"2006-01-02T15:04:05",
	"2006-01-02 15:04",
	"2006-01-02",
}

func (t *Time) Scan(src any) error {
	switch v := src.(type) {
	case nil:
		*t = Time{}
		return nil
	case time.Time:
		// The driver parsed a naive value as UTC: keep the wall clock, re-zone it.
		t.Time = time.Date(v.Year(), v.Month(), v.Day(), v.Hour(), v.Minute(), v.Second(), v.Nanosecond(), CST)
		t.Valid = true
		return nil
	case string:
		return t.parse(v)
	case []byte:
		return t.parse(string(v))
	}
	return fmt.Errorf("store.Time: cannot scan %T", src)
}

func (t *Time) parse(s string) error {
	s = strings.TrimSpace(s)
	if s == "" {
		*t = Time{}
		return nil
	}
	// Drop an explicit offset if a writer stored one; values are Beijing time.
	if i := strings.LastIndexAny(s, "+Z"); i > 10 {
		s = s[:i]
	}
	for _, layout := range layouts {
		if parsed, err := time.ParseInLocation(layout, s, CST); err == nil {
			t.Time, t.Valid = parsed, true
			return nil
		}
	}
	return fmt.Errorf("store.Time: unrecognised timestamp %q", s)
}

func (t Time) Value() (driver.Value, error) {
	if !t.Valid {
		return nil, nil
	}
	return DBTime(t.Time), nil
}

// ISO renders t the way Python's datetime.isoformat() does for a naive value:
// microseconds only when non-zero. nil for a NULL column.
func (t Time) ISO() any {
	if !t.Valid {
		return nil
	}
	return ISO(t.Time)
}

func ISO(t time.Time) string {
	t = t.In(CST)
	base := t.Format("2006-01-02T15:04:05")
	if us := t.Nanosecond() / 1000; us != 0 {
		return fmt.Sprintf("%s.%06d", base, us)
	}
	return base
}

// ISOSeconds is the order-response format: whole seconds, no fraction.
func ISOSeconds(t Time) string {
	if !t.Valid {
		return ""
	}
	return t.Time.In(CST).Format("2006-01-02T15:04:05")
}

// Enum values are stored by name (upper case) and exposed by value (lower case).

func DBEnum(value string) string { return strings.ToUpper(value) }

func APIEnum(stored string) string { return strings.ToLower(stored) }
