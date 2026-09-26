package auth

import (
	"errors"
	"strconv"
	"time"

	"github.com/golang-jwt/jwt/v5"
)

// Tokens are HS256 JWTs with the claims the Python backend issued ("sub" is
// the user id as a string, "exp" a Unix time) plus "pwv", the password version.
type Tokens struct {
	Secret []byte
	TTL    time.Duration
}

type claims struct {
	PasswordVersion string `json:"pwv"`
	jwt.RegisteredClaims
}

func (t Tokens) Issue(userID int64, passwordHash string) (string, error) {
	now := time.Now()
	c := claims{
		PasswordVersion: PasswordVersion(passwordHash),
		RegisteredClaims: jwt.RegisteredClaims{
			Subject:   strconv.FormatInt(userID, 10),
			ExpiresAt: jwt.NewNumericDate(now.Add(t.TTL)),
		},
	}
	return jwt.NewWithClaims(jwt.SigningMethodHS256, c).SignedString(t.Secret)
}

var ErrInvalidToken = errors.New("invalid token")

// Parse checks the signature and expiry and returns the user id and password
// version. A token without a password version predates revocation support
// and is rejected, which costs every user one sign-in after the upgrade.
func (t Tokens) Parse(token string) (int64, string, error) {
	var c claims
	parsed, err := jwt.ParseWithClaims(token, &c, func(*jwt.Token) (any, error) {
		return t.Secret, nil
	}, jwt.WithValidMethods([]string{"HS256"}), jwt.WithExpirationRequired())
	if err != nil || !parsed.Valid || c.PasswordVersion == "" {
		return 0, "", ErrInvalidToken
	}
	id, err := strconv.ParseInt(c.Subject, 10, 64)
	if err != nil {
		return 0, "", ErrInvalidToken
	}
	return id, c.PasswordVersion, nil
}
