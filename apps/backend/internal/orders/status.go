package orders

import (
	"context"
	"database/sql"
	"fmt"
	"slices"
	"strings"

	"github.com/WilliamFeng7/CaffeeOrder/apps/backend/internal/store"
)

var errChanged = &Error{Status: 409, Detail: "订单状态已被他人更新，请刷新 (Order status changed, refresh and retry)"}

// refund marks the order refunded exactly once, credits the customer, writes the
// refund ledger row and puts the stock back. The conditional UPDATE is the
// lock: whoever flips the row pays out, everyone else gets 409.
func refund(ctx context.Context, tx *sql.Tx, o Order, allowedFrom []string) error {
	now := store.DBTime(store.Now())
	q := `UPDATE "order" SET status = ?, updated_at = ? WHERE id = ? AND status != ?`
	args := []any{store.DBEnum(Refunded), now, o.ID, store.DBEnum(Refunded)}
	if len(allowedFrom) > 0 {
		marks := make([]string, len(allowedFrom))
		for i, st := range allowedFrom {
			marks[i] = "?"
			args = append(args, store.DBEnum(st))
		}
		q += ` AND status IN (` + strings.Join(marks, ", ") + `)`
	}
	res, err := tx.ExecContext(ctx, q, args...)
	if err != nil {
		return err
	}
	if n, _ := res.RowsAffected(); n == 0 {
		return fail(409, "Order already refunded or its status changed, retry the action")
	}

	if o.UserID.Valid {
		res, err := tx.ExecContext(ctx, `UPDATE user SET balance = balance + ? WHERE id = ?`, o.Total, o.UserID.Int64)
		if err != nil {
			return err
		}
		if n, _ := res.RowsAffected(); n > 0 {
			var balance int64
			if err := tx.QueryRowContext(ctx, `SELECT balance FROM user WHERE id = ?`, o.UserID.Int64).Scan(&balance); err != nil {
				return err
			}
			if _, err := tx.ExecContext(ctx,
				`INSERT INTO "transaction" (user_id, order_id, external_transaction_id, amount, balance_after, type, payment_method, description, created_at)
				 VALUES (?, ?, ?, ?, ?, 'refund', 'balance', ?, ?)`,
				o.UserID.Int64, o.ID, "REF-"+tag(8), o.Total, balance, fmt.Sprintf("Refund for Order #%d", o.Pickup), now); err != nil {
				return err
			}
		}
	}

	rows, err := tx.QueryContext(ctx, `SELECT menu_item_id, sum(quantity) FROM orderitem WHERE order_id = ? GROUP BY menu_item_id`, o.ID)
	if err != nil {
		return err
	}
	restock := map[int64]int64{}
	for rows.Next() {
		var id, qty int64
		if err := rows.Scan(&id, &qty); err != nil {
			rows.Close()
			return err
		}
		restock[id] = qty
	}
	rows.Close()
	for id, qty := range restock {
		if _, err := tx.ExecContext(ctx, `UPDATE menuitem SET inventory_count = inventory_count + ? WHERE id = ?`, qty, id); err != nil {
			return err
		}
	}
	return nil
}

// Cancel is the customer's cancel: own order (or an admin), still "created".
func (s *Service) Cancel(ctx context.Context, orderID, actorID int64, actorRole string) (Response, error) {
	tx, err := s.db.BeginTx(ctx, nil)
	if err != nil {
		return Response{}, err
	}
	defer tx.Rollback()
	o, err := getOrder(ctx, tx, orderID)
	if err != nil {
		return Response{}, err
	}
	if (!o.UserID.Valid || o.UserID.Int64 != actorID) && actorRole != "admin" {
		return Response{}, fail(403, "Not authorized to cancel this order")
	}
	if o.Status != Created {
		return Response{}, fail(400, "Cannot cancel order that is already processing or completed")
	}
	if err := refund(ctx, tx, o, []string{Created}); err != nil {
		return Response{}, err
	}
	if err := tx.Commit(); err != nil {
		return Response{}, err
	}
	s.invalidateMenu()
	return s.one(ctx, orderID, true)
}

// Complete hands an order over from any active status.
func (s *Service) Complete(ctx context.Context, orderID int64) (Response, error) {
	tx, err := s.db.BeginTx(ctx, nil)
	if err != nil {
		return Response{}, err
	}
	defer tx.Rollback()
	o, err := getOrder(ctx, tx, orderID)
	if err != nil {
		return Response{}, err
	}
	if o.Status == Completed || o.Status == Refunded {
		return Response{}, fail(400, "Cannot complete an order that is already %s", o.Status)
	}
	res, err := tx.ExecContext(ctx,
		`UPDATE "order" SET status = ?, is_completed = 1, updated_at = ? WHERE id = ? AND status = ?`,
		store.DBEnum(Completed), store.DBTime(store.Now()), o.ID, store.DBEnum(o.Status))
	if err != nil {
		return Response{}, err
	}
	if n, _ := res.RowsAffected(); n == 0 {
		return Response{}, errChanged
	}
	if err := tx.Commit(); err != nil {
		return Response{}, err
	}
	return s.one(ctx, orderID, false)
}

// ChangeStatus moves an order along the lifecycle (plus any extra transitions
// the caller allows). Refunds are admin-only. Returns the updated order.
func (s *Service) ChangeStatus(ctx context.Context, orderID int64, to, actorRole string, extra map[string][]string) (Order, error) {
	tx, err := s.db.BeginTx(ctx, nil)
	if err != nil {
		return Order{}, err
	}
	defer tx.Rollback()
	o, err := getOrder(ctx, tx, orderID)
	if err != nil {
		return Order{}, err
	}
	allowed := slices.Concat(transitions[o.Status], extra[o.Status])
	if !slices.Contains(allowed, to) {
		return Order{}, fail(400, "Invalid status transition from %s to %s", o.Status, to)
	}
	if to == Refunded {
		if actorRole != "admin" {
			return Order{}, fail(403, "Only an admin can refund an order")
		}
		if err := refund(ctx, tx, o, nil); err != nil {
			return Order{}, err
		}
	} else {
		completed := 0
		if to == Completed || o.IsCompleted {
			completed = 1
		}
		res, err := tx.ExecContext(ctx,
			`UPDATE "order" SET status = ?, is_completed = ?, updated_at = ? WHERE id = ? AND status = ?`,
			store.DBEnum(to), completed, store.DBTime(store.Now()), o.ID, store.DBEnum(o.Status))
		if err != nil {
			return Order{}, err
		}
		if n, _ := res.RowsAffected(); n == 0 {
			return Order{}, errChanged
		}
	}
	updated, err := getOrder(ctx, tx, orderID)
	if err != nil {
		return Order{}, err
	}
	if err := tx.Commit(); err != nil {
		return Order{}, err
	}
	if to == Refunded {
		s.invalidateMenu()
	}
	return updated, nil
}

// Response returns one order in the response shape.
func (s *Service) Response(ctx context.Context, o Order, refundRow bool) (Response, error) {
	list, err := s.Responses(ctx, []Order{o}, refundRow)
	if err != nil {
		return Response{}, err
	}
	return list[0], nil
}

func (s *Service) one(ctx context.Context, orderID int64, refundRow bool) (Response, error) {
	o, err := getOrder(ctx, s.db, orderID)
	if err != nil {
		return Response{}, err
	}
	return s.Response(ctx, o, refundRow)
}
