package auth

import (
	"net"
	"net/http"
	"strings"
	"sync"
	"time"
)

// LoginLimiter is the per-IP sliding window on failed logins: at most
// maxAttempts failures within window, then 429 until the oldest expires.
// Per-account lockout is separate and lives on the user row.
type LoginLimiter struct {
	mu       sync.Mutex
	failures map[string][]time.Time
	window   time.Duration
	max      int
}

const maxTrackedClients = 10_000

func NewLoginLimiter() *LoginLimiter {
	return &LoginLimiter{failures: map[string][]time.Time{}, window: time.Minute, max: 6}
}

// Check reports how long the client must wait before trying again (0 = go ahead).
func (l *LoginLimiter) Check(client string) time.Duration {
	l.mu.Lock()
	defer l.mu.Unlock()
	now := time.Now()
	recent := l.recent(client, now)
	if len(recent) < l.max {
		return 0
	}
	return l.window - now.Sub(recent[0])
}

func (l *LoginLimiter) RecordFailure(client string) {
	l.mu.Lock()
	defer l.mu.Unlock()
	now := time.Now()
	l.failures[client] = append(l.recent(client, now), now)
	if len(l.failures) > maxTrackedClients {
		for key := range l.failures {
			if len(l.recent(key, now)) == 0 {
				delete(l.failures, key)
			}
		}
	}
}

// recent drops expired entries for client and returns what is left, oldest first.
func (l *LoginLimiter) recent(client string, now time.Time) []time.Time {
	list := l.failures[client]
	i := 0
	for i < len(list) && now.Sub(list[i]) >= l.window {
		i++
	}
	list = list[i:]
	if len(list) == 0 {
		delete(l.failures, client)
		return nil
	}
	l.failures[client] = list
	return list
}

// ClientIP is the address used for rate limiting and the login log. The
// X-Forwarded-For header is believed only when the direct peer is a trusted
// proxy; otherwise any client could mint a fresh bucket per attempt.
func ClientIP(r *http.Request, trusted []*net.IPNet) string {
	peer, _, err := net.SplitHostPort(r.RemoteAddr)
	if err != nil {
		peer = r.RemoteAddr
	}
	if !isTrusted(peer, trusted) {
		return peer
	}
	hops := strings.Split(r.Header.Get("X-Forwarded-For"), ",")
	// Walk from the nearest hop outwards; the first address that is not one of
	// our own proxies is the client.
	for i := len(hops) - 1; i >= 0; i-- {
		hop := strings.TrimSpace(hops[i])
		if hop == "" {
			continue
		}
		if !isTrusted(hop, trusted) {
			return hop
		}
		if i == 0 {
			return hop
		}
	}
	return peer
}

func isTrusted(addr string, trusted []*net.IPNet) bool {
	ip := net.ParseIP(addr)
	if ip == nil {
		return false
	}
	for _, n := range trusted {
		if n.Contains(ip) {
			return true
		}
	}
	return false
}
