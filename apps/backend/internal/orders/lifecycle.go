package orders

import (
	"context"
	"crypto/rand"
	"database/sql"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"log/slog"
	"strconv"
	"strings"
	"time"

	"github.com/WilliamFeng7/CaffeeOrder/apps/backend/internal/store"
)

// LineInput is one requested line: a product, its options and a quantity.
type LineInput struct {
	MenuItemID int64
	Spec       map[string]string
	Quantity   int64
}

// merge folds identical (product, options) lines into one line with the summed
// quantity, so three separate "latte, hot" rows become a single line of three.
func merge(lines []LineInput) []LineInput {
	var out []LineInput
	index := map[string]int{}
	for _, l := range lines {
		spec, _ := json.Marshal(l.Spec) // map keys marshal in sorted order
		key := strconv.FormatInt(l.MenuItemID, 10) + "|" + string(spec)
		qty := l.Quantity
		if qty <= 0 {
			qty = 1
		}
		if i, ok := index[key]; ok {
			out[i].Quantity += qty
			continue
		}
		index[key] = len(out)
		out = append(out, LineInput{MenuItemID: l.MenuItemID, Spec: l.Spec, Quantity: qty})
	}
	return out
}

func tag(n int) string {
	b := make([]byte, (n+1)/2)
	if _, err := rand.Read(b); err != nil {
		panic(err)
	}
	return strings.ToUpper(hex.EncodeToString(b))[:n]
}

func isUniqueViolation(err error) bool {
	return err != nil && strings.Contains(err.Error(), "UNIQUE constraint failed")
}

// Create places an order for userID. A clash on the order number or the daily
// pickup number (two orders in the same instant) is retried.
func (s *Service) Create(ctx context.Context, userID int64, lines []LineInput) (Response, error) {
	lines = merge(lines)
	if len(lines) == 0 {
		return Response{}, fail(400, "Order cannot be empty")
	}
	for attempt := 1; attempt <= 3; attempt++ {
		resp, err := s.createOnce(ctx, userID, lines)
		if err == nil {
			s.invalidateMenu()
			return resp, nil
		}
		if !isUniqueViolation(err) {
			return Response{}, err
		}
		slog.Warn("order number collision, retrying", "attempt", attempt, "err", err)
	}
	return Response{}, fail(409, "System busy, please retry")
}

type product struct {
	name, nameCN, image string
	price               int64
	active              bool
}

func (s *Service) createOnce(ctx context.Context, userID int64, lines []LineInput) (Response, error) {
	tx, err := s.db.BeginTx(ctx, nil)
	if err != nil {
		return Response{}, err
	}
	defer tx.Rollback()

	products, err := loadProducts(ctx, tx, lines)
	if err != nil {
		return Response{}, err
	}
	var total int64
	for _, l := range lines {
		p, ok := products[l.MenuItemID]
		if !ok || !p.active {
			return Response{}, fail(400, "Item %d not available", l.MenuItemID)
		}
		res, err := tx.ExecContext(ctx,
			`UPDATE menuitem SET inventory_count = inventory_count - ? WHERE id = ? AND inventory_count >= ?`,
			l.Quantity, l.MenuItemID, l.Quantity)
		if err != nil {
			return Response{}, err
		}
		if n, _ := res.RowsAffected(); n == 0 {
			name := p.nameCN
			if name == "" {
				name = p.name
			}
			return Response{}, fail(400, "Item %s is sold out", name)
		}
		total += p.price * l.Quantity
	}
	if total <= 0 {
		return Response{}, fail(400, "Order cannot be empty")
	}

	res, err := tx.ExecContext(ctx, `UPDATE user SET balance = balance - ? WHERE id = ? AND balance >= ?`, total, userID, total)
	if err != nil {
		return Response{}, err
	}
	if n, _ := res.RowsAffected(); n == 0 {
		return Response{}, fail(402, "Insufficient funds")
	}
	var balance int64
	if err := tx.QueryRowContext(ctx, `SELECT balance FROM user WHERE id = ?`, userID).Scan(&balance); err == sql.ErrNoRows {
		return Response{}, fail(409, "Account no longer exists")
	} else if err != nil {
		return Response{}, err
	}

	now := store.Now()
	orderNo, pickup, err := nextIdentifiers(ctx, tx, now)
	if err != nil {
		return Response{}, err
	}
	stamp := store.DBTime(now)
	res, err = tx.ExecContext(ctx,
		`INSERT INTO "order" (user_id, order_no, status, created_at, total_amount, pickup_number, is_completed, updated_at)
		 VALUES (?, ?, ?, ?, ?, ?, 0, ?)`,
		userID, orderNo, store.DBEnum(Created), stamp, total, pickup, stamp)
	if err != nil {
		return Response{}, err
	}
	orderID, _ := res.LastInsertId()

	for _, l := range lines {
		p := products[l.MenuItemID]
		spec := l.Spec
		if spec == nil {
			spec = map[string]string{}
		}
		specJSON, _ := json.Marshal(spec)
		if _, err := tx.ExecContext(ctx,
			`INSERT INTO orderitem (order_id, menu_item_id, item_name, price_snap, image_url, spec, quantity) VALUES (?, ?, ?, ?, ?, ?, ?)`,
			orderID, l.MenuItemID, p.name, p.price, p.image, string(specJSON), l.Quantity); err != nil {
			return Response{}, err
		}
	}
	if _, err := tx.ExecContext(ctx,
		`INSERT INTO "transaction" (user_id, order_id, external_transaction_id, amount, balance_after, type, payment_method, description, created_at)
		 VALUES (?, ?, ?, ?, ?, 'order', 'balance', ?, ?)`,
		userID, orderID, "LOC-"+tag(8), -total, balance, fmt.Sprintf("Order #%d", pickup), stamp); err != nil {
		return Response{}, err
	}

	o, err := getOrder(ctx, tx, orderID)
	if err != nil {
		return Response{}, err
	}
	list, err := responses(ctx, tx, []Order{o}, false)
	if err != nil {
		return Response{}, err
	}
	if err := tx.Commit(); err != nil {
		return Response{}, err
	}
	return list[0], nil
}

func loadProducts(ctx context.Context, tx *sql.Tx, lines []LineInput) (map[int64]product, error) {
	ids := make([]any, len(lines))
	marks := make([]string, len(lines))
	for i, l := range lines {
		ids[i], marks[i] = l.MenuItemID, "?"
	}
	rows, err := tx.QueryContext(ctx,
		`SELECT id, name, COALESCE(name_cn, ''), image_path, price, is_active FROM menuitem WHERE id IN (`+strings.Join(marks, ", ")+`)`, ids...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	out := map[int64]product{}
	for rows.Next() {
		var id int64
		var p product
		if err := rows.Scan(&id, &p.name, &p.nameCN, &p.image, &p.price, &p.active); err != nil {
			return nil, err
		}
		out[id] = p
	}
	return out, rows.Err()
}

// nextIdentifiers reserves the order number (timestamp + 4-digit sequence) and
// the pickup number (per-day sequence starting at 1).
func nextIdentifiers(ctx context.Context, tx *sql.Tx, now time.Time) (string, int64, error) {
	prefix := now.Format("20060102150405")
	var maxNo sql.NullString
	if err := tx.QueryRowContext(ctx, `SELECT max(order_no) FROM "order" WHERE order_no LIKE ?`, prefix+"%").Scan(&maxNo); err != nil {
		return "", 0, err
	}
	seq := 1
	if maxNo.Valid && len(maxNo.String) >= 4 {
		if n, err := strconv.Atoi(maxNo.String[len(maxNo.String)-4:]); err == nil {
			seq = n + 1
		}
	}
	var maxPickup sql.NullInt64
	if err := tx.QueryRowContext(ctx, `SELECT max(pickup_number) FROM "order" WHERE created_at >= ?`,
		store.DBTime(store.StartOfDay(now))).Scan(&maxPickup); err != nil {
		return "", 0, err
	}
	return fmt.Sprintf("%s%04d", prefix, seq), maxPickup.Int64 + 1, nil
}
