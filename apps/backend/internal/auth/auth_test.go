package auth

import (
	"net"
	"net/http/httptest"
	"testing"
	"time"
)

// Hashes written by the Python backend (bcrypt and passlib, both $2b$) must keep working.
func TestVerifyPythonHashes(t *testing.T) {
	for _, hash := range []string{
		"$2b$12$NA.2oL56c8xNRDp5FhIDDeQG7hUtaLaBDrKbuvb6UjukDZep0nttS",
		"$2b$12$nZ8GCg34MdA72lF9LoZfhecDnWVK10nnufETZP2mxBtnTiYsE0Oiy",
	} {
		if !VerifyPassword("Python-made-9", hash) {
			t.Errorf("python hash %s did not verify", hash)
		}
		if VerifyPassword("python-made-9", hash) {
			t.Errorf("wrong password verified against %s", hash)
		}
	}
}

func TestVerifyRejectsMalformedHashes(t *testing.T) {
	for _, stored := range []string{"", "plaintext-password", "$2b$12$short", "$2b$12$invalidinvalidinvalidinvalidinvalidinvalidinvalidinva"} {
		if VerifyPassword("plaintext-password", stored) {
			t.Errorf("accepted malformed hash %q", stored)
		}
	}
}

func TestPasswordPolicy(t *testing.T) {
	cases := map[string]bool{
		"short1":                 false,
		"password123":            false, // common
		"Correct-horse-9":        true,
		"咖啡咖啡咖啡咖啡":               true, // 8 characters, 24 bytes
		string(make([]byte, 73)): false,
	}
	for pw, want := range cases {
		if got := ValidatePassword(pw) == nil; got != want {
			t.Errorf("ValidatePassword(%q) ok=%v, want %v", pw, got, want)
		}
	}
}

func TestTokensCarryPasswordVersion(t *testing.T) {
	tokens := Tokens{Secret: []byte("test-secret"), TTL: time.Hour}
	token, err := tokens.Issue(42, "hash-one")
	if err != nil {
		t.Fatal(err)
	}
	id, pwv, err := tokens.Parse(token)
	if err != nil || id != 42 || pwv != PasswordVersion("hash-one") {
		t.Fatalf("Parse = %d, %q, %v", id, pwv, err)
	}
	if pwv == PasswordVersion("hash-two") {
		t.Fatal("password version does not change with the hash")
	}
	if _, _, err := (Tokens{Secret: []byte("other"), TTL: time.Hour}).Parse(token); err == nil {
		t.Fatal("token verified with the wrong secret")
	}
	expired, _ := Tokens{Secret: []byte("test-secret"), TTL: -time.Minute}.Issue(42, "hash-one")
	if _, _, err := tokens.Parse(expired); err == nil {
		t.Fatal("expired token accepted")
	}
}

func TestLoginLimiterWindow(t *testing.T) {
	l := NewLoginLimiter()
	for i := 0; i < 6; i++ {
		if wait := l.Check("1.2.3.4"); wait != 0 {
			t.Fatalf("blocked after %d failures", i)
		}
		l.RecordFailure("1.2.3.4")
	}
	if wait := l.Check("1.2.3.4"); wait <= 0 || wait > time.Minute {
		t.Fatalf("7th attempt wait = %v, want (0, 1m]", wait)
	}
	if wait := l.Check("5.6.7.8"); wait != 0 {
		t.Fatal("another client was blocked")
	}
}

func TestClientIPTrustsOnlyConfiguredProxies(t *testing.T) {
	_, proxyNet, _ := net.ParseCIDR("172.28.0.0/16")
	trusted := []*net.IPNet{proxyNet}

	r := httptest.NewRequest("GET", "/", nil)
	r.RemoteAddr = "203.0.113.9:5555"
	r.Header.Set("X-Forwarded-For", "10.0.0.1")
	if got := ClientIP(r, trusted); got != "203.0.113.9" {
		t.Errorf("untrusted peer: got %s, want the peer itself", got)
	}

	r.RemoteAddr = "172.28.0.5:5555"
	r.Header.Set("X-Forwarded-For", "198.51.100.7, 172.28.0.9")
	if got := ClientIP(r, trusted); got != "198.51.100.7" {
		t.Errorf("trusted proxy chain: got %s, want 198.51.100.7", got)
	}
}
