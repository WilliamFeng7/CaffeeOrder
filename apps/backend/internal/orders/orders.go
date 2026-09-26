// Package orders owns every rule about orders and the money they move:
// pricing, stock reservation, balance debits, the status lifecycle and refunds.
//
// SQLite has no row locks, so each state change is a conditional UPDATE and the
// affected-row count decides who won: stock (inventory_count >= qty), balance
// (balance >= total) and status (status = the value the caller saw).
package orders

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"strings"
	"time"

	"github.com/WilliamFeng7/CaffeeOrder/apps/backend/internal/store"
)

const (
	Created    = "created"
	Processing = "processing"
	Ready      = "ready"
	Completed  = "completed"
	Refunded   = "refunded"
)

var Active = []string{Created, Processing, Ready}

// transitions is the lifecycle: created → processing → ready → completed, and
// any non-refunded order may be refunded (by an admin).
var transitions = map[string][]string{
	Created:    {Processing, Refunded},
	Processing: {Ready, Refunded},
	Ready:      {Completed, Refunded},
	Completed:  {Refunded},
	Refunded:   {},
}

// CompleteShortcuts lets staff hand an order over without walking every step.
var CompleteShortcuts = map[string][]string{
	Created:    {Completed},
	Processing: {Completed},
}

func ValidStatus(s string) bool {
	_, ok := transitions[s]
	return ok
}

// Error is an order failure with the HTTP status and message clients see.
type Error struct {
	Status int
	Detail string
}

func (e *Error) Error() string   { return e.Detail }
func (e *Error) StatusCode() int { return e.Status }
func (e *Error) Payload() any    { return e.Detail }

func fail(status int, format string, args ...any) *Error {
	return &Error{Status: status, Detail: fmt.Sprintf(format, args...)}
}

type Service struct {
	db             *sql.DB
	invalidateMenu func()
}

func NewService(db *sql.DB, invalidateMenu func()) *Service {
	if invalidateMenu == nil {
		invalidateMenu = func() {}
	}
	return &Service{db: db, invalidateMenu: invalidateMenu}
}

type Order struct {
	ID          int64
	UserID      sql.NullInt64
	OrderNo     string
	Status      string
	CreatedAt   store.Time
	UpdatedAt   store.Time
	Total       int64
	Pickup      int64
	IsCompleted bool
}

const orderColumns = `id, user_id, order_no, status, created_at, updated_at, total_amount, pickup_number, is_completed`

type queryer interface {
	QueryContext(ctx context.Context, query string, args ...any) (*sql.Rows, error)
	QueryRowContext(ctx context.Context, query string, args ...any) *sql.Row
}

func scanOrder(row interface{ Scan(...any) error }) (Order, error) {
	var o Order
	err := row.Scan(&o.ID, &o.UserID, &o.OrderNo, &o.Status, &o.CreatedAt, &o.UpdatedAt, &o.Total, &o.Pickup, &o.IsCompleted)
	o.Status = store.APIEnum(o.Status)
	return o, err
}

func getOrder(ctx context.Context, q queryer, id int64) (Order, error) {
	o, err := scanOrder(q.QueryRowContext(ctx, `SELECT `+orderColumns+` FROM "order" WHERE id = ?`, id))
	if err == sql.ErrNoRows {
		return o, fail(404, "Order not found")
	}
	return o, err
}

func (s *Service) query(ctx context.Context, where string, args ...any) ([]Order, error) {
	rows, err := s.db.QueryContext(ctx, `SELECT `+orderColumns+` FROM "order" `+where, args...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var list []Order
	for rows.Next() {
		o, err := scanOrder(rows)
		if err != nil {
			return nil, err
		}
		list = append(list, o)
	}
	return list, rows.Err()
}

// ForUser is a student's order history, newest first.
func (s *Service) ForUser(ctx context.Context, userID int64, skip, limit int) ([]Response, error) {
	list, err := s.query(ctx, `WHERE user_id = ? ORDER BY created_at DESC, id DESC LIMIT ? OFFSET ?`, userID, limit, skip)
	if err != nil {
		return nil, err
	}
	return s.Responses(ctx, list, false)
}

// All lists every order, newest first, optionally filtered by status.
func (s *Service) All(ctx context.Context, status string, skip, limit int) ([]Response, error) {
	where, args := `ORDER BY created_at DESC, id DESC LIMIT ? OFFSET ?`, []any{limit, skip}
	if status != "" {
		where, args = `WHERE status = ? `+where, append([]any{store.DBEnum(status)}, args...)
	}
	list, err := s.query(ctx, where, args...)
	if err != nil {
		return nil, err
	}
	return s.Responses(ctx, list, false)
}

const (
	syncLookback = 24 * time.Hour
	syncMaxRows  = 500
)

// Sync is the staff feed. since == 0 returns every active order; otherwise the
// orders changed after the Unix time since, looking back at most 24 hours.
func (s *Service) Sync(ctx context.Context, since float64) ([]Response, error) {
	var list []Order
	var err error
	if since > 0 {
		from := time.Unix(0, int64(since*float64(time.Second))).In(store.CST)
		if floor := store.Now().Add(-syncLookback); from.Before(floor) {
			from = floor
		}
		list, err = s.query(ctx, `WHERE updated_at > ? ORDER BY created_at, id LIMIT ?`, store.DBTime(from), syncMaxRows)
	} else {
		list, err = s.query(ctx, `WHERE status IN (?, ?, ?) ORDER BY created_at, id LIMIT ?`,
			store.DBEnum(Created), store.DBEnum(Processing), store.DBEnum(Ready), syncMaxRows)
	}
	if err != nil {
		return nil, err
	}
	return s.Responses(ctx, list, false)
}

// Response is the OrderResponse schema.
type Response struct {
	ID                    int64          `json:"id"`
	OrderNo               string         `json:"order_no"`
	Status                string         `json:"status"`
	TotalAmount           int64          `json:"total_amount"`
	PickupNumber          int64          `json:"pickup_number"`
	IsCompleted           bool           `json:"is_completed"`
	CreatedAt             string         `json:"created_at"`
	UpdatedAt             string         `json:"updated_at"`
	ExternalTransactionID string         `json:"external_transaction_id"`
	Items                 []ItemResponse `json:"items"`
	UserID                *int64         `json:"user_id"`
}

type ItemResponse struct {
	MenuItemID int64          `json:"menu_item_id"`
	ItemName   string         `json:"item_name"`
	PriceSnap  int64          `json:"price_snap"`
	ImageURL   string         `json:"image_url"`
	Spec       map[string]any `json:"spec"`
	Quantity   int64          `json:"quantity"`
}

// Responses hydrates orders with their payment reference and lines in two
// queries. refundRow shows the refund's reference instead of the payment's.
func (s *Service) Responses(ctx context.Context, list []Order, refundRow bool) ([]Response, error) {
	return responses(ctx, s.db, list, refundRow)
}

func responses(ctx context.Context, q queryer, list []Order, refundRow bool) ([]Response, error) {
	out := make([]Response, 0, len(list))
	if len(list) == 0 {
		return out, nil
	}
	ids := make([]any, len(list))
	marks := make([]string, len(list))
	for i, o := range list {
		ids[i], marks[i] = o.ID, "?"
	}
	in := strings.Join(marks, ", ")

	kind := "order"
	if refundRow {
		kind = "refund"
	}
	refs := map[int64]string{}
	rows, err := q.QueryContext(ctx,
		`SELECT order_id, external_transaction_id FROM "transaction" WHERE type = ? AND order_id IN (`+in+`) ORDER BY id`,
		append([]any{kind}, ids...)...)
	if err != nil {
		return nil, err
	}
	for rows.Next() {
		var id int64
		var ref string
		if err := rows.Scan(&id, &ref); err != nil {
			rows.Close()
			return nil, err
		}
		if _, seen := refs[id]; !seen {
			refs[id] = ref
		}
	}
	rows.Close()

	items := map[int64][]ItemResponse{}
	rows, err = q.QueryContext(ctx,
		`SELECT order_id, menu_item_id, item_name, price_snap, image_url, spec, quantity FROM orderitem WHERE order_id IN (`+in+`) ORDER BY id`,
		ids...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	for rows.Next() {
		var orderID int64
		var it ItemResponse
		var spec sql.NullString
		if err := rows.Scan(&orderID, &it.MenuItemID, &it.ItemName, &it.PriceSnap, &it.ImageURL, &spec, &it.Quantity); err != nil {
			return nil, err
		}
		it.Spec = map[string]any{}
		if spec.Valid {
			_ = json.Unmarshal([]byte(spec.String), &it.Spec)
		}
		if it.Quantity <= 0 {
			it.Quantity = 1
		}
		items[orderID] = append(items[orderID], it)
	}
	if err := rows.Err(); err != nil {
		return nil, err
	}

	for _, o := range list {
		r := Response{
			ID: o.ID, OrderNo: o.OrderNo, Status: o.Status, TotalAmount: o.Total, PickupNumber: o.Pickup,
			IsCompleted: o.IsCompleted, CreatedAt: store.ISOSeconds(o.CreatedAt), UpdatedAt: store.ISOSeconds(o.UpdatedAt),
			ExternalTransactionID: refs[o.ID], Items: items[o.ID],
		}
		if r.Items == nil {
			r.Items = []ItemResponse{}
		}
		if o.UserID.Valid {
			id := o.UserID.Int64
			r.UserID = &id
		}
		out = append(out, r)
	}
	return out, nil
}

// Raw is the plain Order row the admin status endpoint returned.
type Raw struct {
	ID           int64  `json:"id"`
	UserID       *int64 `json:"user_id"`
	OrderNo      string `json:"order_no"`
	Status       string `json:"status"`
	CreatedAt    any    `json:"created_at"`
	TotalAmount  int64  `json:"total_amount"`
	PickupNumber int64  `json:"pickup_number"`
	IsCompleted  bool   `json:"is_completed"`
	UpdatedAt    any    `json:"updated_at"`
}

func (o Order) Raw() Raw {
	r := Raw{ID: o.ID, OrderNo: o.OrderNo, Status: o.Status, CreatedAt: o.CreatedAt.ISO(), TotalAmount: o.Total,
		PickupNumber: o.Pickup, IsCompleted: o.IsCompleted, UpdatedAt: o.UpdatedAt.ISO()}
	if o.UserID.Valid {
		id := o.UserID.Int64
		r.UserID = &id
	}
	return r
}
