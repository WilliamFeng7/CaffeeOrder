// Package auth holds password hashing, the password policy, access tokens and
// the login rate limiter.
package auth

import (
	"crypto/sha256"
	_ "embed"
	"encoding/hex"
	"errors"
	"regexp"
	"strings"
	"sync"
	"unicode/utf8"

	"golang.org/x/crypto/bcrypt"
)

// Cost 12 matches passlib's bcrypt default, so new and old hashes cost the same.
const bcryptCost = 12

// The shape of a bcrypt hash. Anything else stored in the password column
// (a legacy plain-text value, a truncated write) is rejected before bcrypt runs.
var bcryptHash = regexp.MustCompile(`^\$2[aby]\$\d{2}\$[./A-Za-z0-9]{53}$`)

// bcrypt only reads the first 72 bytes; cut explicitly so hashing and
// checking agree on what the password is.
func clip(password string) []byte {
	b := []byte(password)
	if len(b) > 72 {
		b = b[:72]
	}
	return b
}

func HashPassword(password string) (string, error) {
	hash, err := bcrypt.GenerateFromPassword(clip(password), bcryptCost)
	return string(hash), err
}

// VerifyPassword accepts the $2a$/$2b$ hashes written by Python's bcrypt.
func VerifyPassword(password, hash string) bool {
	if !bcryptHash.MatchString(hash) {
		return false
	}
	return bcrypt.CompareHashAndPassword([]byte(hash), clip(password)) == nil
}

var (
	dummyOnce sync.Once
	dummyHash string
)

// BurnPasswordCheck spends the same time as a real check, so a login for an
// unknown account is not measurably faster than one with a wrong password.
func BurnPasswordCheck(password string) {
	dummyOnce.Do(func() {
		dummyHash, _ = HashPassword("timing-equaliser-not-a-real-password")
	})
	VerifyPassword(password, dummyHash)
}

// PasswordVersion identifies the current password hash. It is embedded in
// access tokens; changing the password changes it and so revokes old tokens.
func PasswordVersion(hash string) string {
	sum := sha256.Sum256([]byte(hash))
	return hex.EncodeToString(sum[:8])
}

//go:embed common_passwords.txt
var commonPasswordList string

var commonPasswords = func() map[string]struct{} {
	set := map[string]struct{}{}
	for _, p := range []string{"123456", "password", "password123", "admin", "12345678", "qwerty", "system"} {
		set[p] = struct{}{}
	}
	for _, line := range strings.Split(commonPasswordList, "\n") {
		if line = strings.ToLower(strings.TrimSpace(line)); line != "" {
			set[line] = struct{}{}
		}
	}
	return set
}()

// ValidatePassword applies the policy the Python backend enforced, with the
// same bilingual messages the frontends already display.
func ValidatePassword(password string) error {
	if utf8.RuneCountInString(password) < 8 {
		return errors.New("密码长度必须至少为 8 位 (Password must be at least 8 characters)")
	}
	if len(password) > 72 {
		return errors.New("密码过长，最多 72 字节 (Password too long, max 72 bytes)")
	}
	if _, common := commonPasswords[strings.ToLower(password)]; common {
		return errors.New("密码太常见，请选择更安全的密码 (Password is too common, please choose a stronger one)")
	}
	return nil
}
