package api

import (
	"context"
	"database/sql"
	"fmt"
	"math"
	"net/http"
	"strconv"
	"time"

	"github.com/WilliamFeng7/CaffeeOrder/apps/backend/internal/store"
)

func round(v float64, places int) float64 {
	p := math.Pow(10, float64(places))
	return math.Round(v*p) / p
}

func (s *Server) scalar(ctx context.Context, query string, args ...any) (int64, error) {
	var v sql.NullInt64
	err := s.db.QueryRowContext(ctx, query, args...).Scan(&v)
	return v.Int64, err
}

// netSales is order payments minus refunds in [from, to), never below zero.
func (s *Server) netSales(ctx context.Context, from, to time.Time) (int64, error) {
	paid, err := s.scalar(ctx, `SELECT sum(amount) FROM "transaction" WHERE type = 'order' AND created_at >= ? AND created_at < ?`,
		store.DBTime(from), store.DBTime(to))
	if err != nil {
		return 0, err
	}
	refunded, err := s.scalar(ctx, `SELECT sum(amount) FROM "transaction" WHERE type = 'refund' AND created_at >= ? AND created_at < ?`,
		store.DBTime(from), store.DBTime(to))
	if err != nil {
		return 0, err
	}
	return max(0, abs(paid)-refunded), nil
}

func abs(v int64) int64 {
	if v < 0 {
		return -v
	}
	return v
}

func growth(today, yesterday int64) float64 {
	if yesterday <= 0 {
		return 0
	}
	return round(float64(today-yesterday)/float64(yesterday)*100, 1)
}

func (s *Server) dashboardStats(w http.ResponseWriter, r *http.Request) error {
	if _, err := s.requireRole(r, "admin"); err != nil {
		return err
	}
	ctx := r.Context()
	now := store.Now()
	today := store.StartOfDay(now)
	yesterday := today.AddDate(0, 0, -1)
	tomorrow := today.AddDate(0, 0, 1)

	revenueToday, err := s.netSales(ctx, today, tomorrow)
	if err != nil {
		return err
	}
	revenueYesterday, err := s.netSales(ctx, yesterday, today)
	if err != nil {
		return err
	}
	countToday, err := s.scalar(ctx, `SELECT count(*) FROM "order" WHERE created_at >= ?`, store.DBTime(today))
	if err != nil {
		return err
	}
	countYesterday, err := s.scalar(ctx, `SELECT count(*) FROM "order" WHERE created_at >= ? AND created_at < ?`,
		store.DBTime(yesterday), store.DBTime(today))
	if err != nil {
		return err
	}
	newMembers, err := s.scalar(ctx, `SELECT count(*) FROM user WHERE role = 'STUDENT' AND created_at >= ?`, store.DBTime(today))
	if err != nil {
		return err
	}

	// Live counts are today's orders only: unfinished orders from earlier days
	// are a backlog to clean up, not the current queue.
	statusCounts := map[string]int64{}
	rows, err := s.db.QueryContext(ctx, `SELECT status, count(*) FROM "order" WHERE created_at >= ? GROUP BY status`, store.DBTime(today))
	if err != nil {
		return err
	}
	for rows.Next() {
		var st string
		var n int64
		if err := rows.Scan(&st, &n); err != nil {
			rows.Close()
			return err
		}
		statusCounts[store.APIEnum(st)] = n
	}
	rows.Close()
	funnel := map[string]int64{
		"pending":    statusCounts["created"],
		"processing": statusCounts["processing"],
		"ready":      statusCounts["ready"],
		"completed":  statusCounts["completed"],
		"cancelled":  statusCounts["refunded"],
	}
	pending := funnel["pending"] + funnel["processing"] + funnel["ready"]

	trend, err := s.hourlyTrend(ctx, now)
	if err != nil {
		return err
	}
	top, err := s.topSelling(ctx, today)
	if err != nil {
		return err
	}
	soldOut, err := s.soldOut(ctx)
	if err != nil {
		return err
	}

	aov := 0.0
	if countToday > 0 {
		aov = float64(revenueToday) / float64(countToday)
	}
	return ok(w, map[string]any{
		"overview": map[string]any{
			"total_revenue_today":  float64(revenueToday) / 100,
			"revenue_growth":       growth(revenueToday, revenueYesterday),
			"total_orders_today":   countToday,
			"orders_growth":        growth(countToday, countYesterday),
			"aov_today":            round(aov/100, 2),
			"new_members_today":    newMembers,
			"pending_orders_count": pending,
		},
		"operations": map[string]any{
			"funnel":                 funnel,
			"estimated_wait_minutes": (funnel["pending"] + funnel["processing"]) * 3,
			"trend":                  trend,
		},
		"inventory": map[string]any{
			"top_selling_items": top,
			"sold_out_items":    soldOut,
		},
	})
}

// hourlyTrend is 24 hourly buckets ending with the current hour.
func (s *Server) hourlyTrend(ctx context.Context, now time.Time) ([]map[string]any, error) {
	start := now.Truncate(time.Hour).Add(-23 * time.Hour)
	rows, err := s.db.QueryContext(ctx,
		`SELECT strftime('%Y-%m-%d %H', created_at), count(*), sum(total_amount) FROM "order" WHERE created_at >= ? GROUP BY 1`,
		store.DBTime(start))
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	type bucket struct{ orders, revenue int64 }
	buckets := map[string]bucket{}
	for rows.Next() {
		var key string
		var b bucket
		var revenue sql.NullInt64
		if err := rows.Scan(&key, &b.orders, &revenue); err != nil {
			return nil, err
		}
		b.revenue = revenue.Int64
		buckets[key] = b
	}
	if err := rows.Err(); err != nil {
		return nil, err
	}
	out := make([]map[string]any, 0, 24)
	for i := 0; i < 24; i++ {
		h := start.Add(time.Duration(i) * time.Hour)
		b := buckets[h.Format("2006-01-02 15")]
		out = append(out, map[string]any{"hour": h.Format("15:00"), "orders": b.orders, "revenue": float64(b.revenue) / 100})
	}
	return out, nil
}

func (s *Server) topSelling(ctx context.Context, since time.Time) ([]map[string]any, error) {
	rows, err := s.db.QueryContext(ctx,
		`SELECT oi.item_name, sum(oi.quantity) AS qty FROM orderitem oi JOIN "order" o ON o.id = oi.order_id
		 WHERE o.created_at >= ? AND o.status = 'COMPLETED' GROUP BY oi.item_name ORDER BY qty DESC LIMIT 3`,
		store.DBTime(since))
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	out := []map[string]any{}
	for rows.Next() {
		var name string
		var qty int64
		if err := rows.Scan(&name, &qty); err != nil {
			return nil, err
		}
		out = append(out, map[string]any{"name": name, "sales": qty})
	}
	return out, rows.Err()
}

func (s *Server) soldOut(ctx context.Context) ([]map[string]any, error) {
	rows, err := s.db.QueryContext(ctx,
		`SELECT CASE WHEN name_cn IS NULL OR name_cn = '' THEN name ELSE name_cn END, category FROM menuitem WHERE inventory_count <= 0 ORDER BY id`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	out := []map[string]any{}
	for rows.Next() {
		var name, category string
		if err := rows.Scan(&name, &category); err != nil {
			return nil, err
		}
		out = append(out, map[string]any{"name": name, "category": category})
	}
	return out, rows.Err()
}

func (s *Server) financeStats(w http.ResponseWriter, r *http.Request) error {
	if _, err := s.requireRole(r, "admin"); err != nil {
		return err
	}
	ctx := r.Context()
	today := store.StartOfDay(store.Now())
	liability, err := s.scalar(ctx, `SELECT sum(balance) FROM user WHERE role = 'STUDENT'`)
	if err != nil {
		return err
	}
	sales, err := s.netSales(ctx, today, today.AddDate(0, 0, 1))
	if err != nil {
		return err
	}
	deposits, err := s.scalar(ctx, `SELECT sum(amount) FROM "transaction" WHERE type = 'deposit' AND created_at >= ?`, store.DBTime(today))
	if err != nil {
		return err
	}
	return ok(w, map[string]any{
		"total_liability":  liability,
		"today_sales":      sales,
		"today_deposits":   deposits,
		"consumption_rate": 100,
	})
}

// financeChart is deposits vs spending per day (or per minute over the last
// 24 hours when days=1), plus a count of deposits by amount.
func (s *Server) financeChart(w http.ResponseWriter, r *http.Request) error {
	if _, err := s.requireRole(r, "admin"); err != nil {
		return err
	}
	days := 7
	if v := r.URL.Query().Get("days"); v != "" {
		n, err := strconv.Atoi(v)
		if err != nil || n < 1 || n > 366 {
			return validation([]any{"query", "days"}, "Input should be between 1 and 366", "less_than_equal")
		}
		days = n
	}
	ctx := r.Context()
	now := store.Now()

	var start time.Time
	var bucketFormat, labelFormat, sqlFormat string
	var points int
	var step time.Duration
	if days == 1 {
		start = now.Truncate(time.Minute).Add(-24 * time.Hour)
		sqlFormat, bucketFormat, labelFormat = "%Y-%m-%d %H:%M", "2006-01-02 15:04", "15:04"
		points, step = 24*60, time.Minute
	} else {
		start = store.StartOfDay(now).AddDate(0, 0, -(days - 1))
		sqlFormat, bucketFormat, labelFormat = "%Y-%m-%d", "2006-01-02", "2006-01-02"
		points, step = days, 24*time.Hour
	}

	sums := func(kind string) (map[string]int64, error) {
		rows, err := s.db.QueryContext(ctx,
			`SELECT strftime(?, created_at), sum(amount) FROM "transaction" WHERE type = ? AND created_at >= ? GROUP BY 1`,
			sqlFormat, kind, store.DBTime(start))
		if err != nil {
			return nil, err
		}
		defer rows.Close()
		out := map[string]int64{}
		for rows.Next() {
			var key string
			var total int64
			if err := rows.Scan(&key, &total); err != nil {
				return nil, err
			}
			out[key] = abs(total)
		}
		return out, rows.Err()
	}
	spending, err := sums("order")
	if err != nil {
		return err
	}
	deposits, err := sums("deposit")
	if err != nil {
		return err
	}

	line := make([]map[string]any, 0, points)
	for i := 0; i < points; i++ {
		t := start.Add(time.Duration(i) * step)
		if days != 1 {
			t = start.AddDate(0, 0, i)
		}
		key := t.Format(bucketFormat)
		line = append(line, map[string]any{
			"date":     t.Format(labelFormat),
			"deposit":  float64(deposits[key]) / 100,
			"spending": float64(spending[key]) / 100,
		})
	}

	rows, err := s.db.QueryContext(ctx,
		`SELECT amount, count(*) FROM "transaction" WHERE type = 'deposit' AND created_at >= ? GROUP BY amount ORDER BY amount`,
		store.DBTime(start))
	if err != nil {
		return err
	}
	defer rows.Close()
	pie := []map[string]any{}
	index := map[string]int{}
	for rows.Next() {
		var amount, count int64
		if err := rows.Scan(&amount, &count); err != nil {
			return err
		}
		label := fmt.Sprintf("¥%d", amount/100)
		if i, seen := index[label]; seen {
			pie[i]["value"] = pie[i]["value"].(int64) + count
			continue
		}
		index[label] = len(pie)
		pie = append(pie, map[string]any{"name": label, "value": count})
	}
	if err := rows.Err(); err != nil {
		return err
	}
	return ok(w, map[string]any{"line_chart": line, "pie_chart": pie})
}

func (s *Server) financeTransactions(w http.ResponseWriter, r *http.Request) error {
	if _, err := s.requireRole(r, "admin"); err != nil {
		return err
	}
	p, err := pagination(r, 20)
	if err != nil {
		return err
	}
	kind := r.URL.Query().Get("type")
	if kind == "" {
		kind = "order"
	}
	rows, err := s.db.QueryContext(r.Context(),
		`SELECT t.id, t.external_transaction_id, t.order_id, u.id, u.name, u.username, t.amount, t.balance_after,
		        t.created_at, t.description, t.payment_method
		 FROM "transaction" t LEFT JOIN user u ON u.id = t.user_id
		 WHERE t.type = ? ORDER BY t.created_at DESC, t.id DESC LIMIT ? OFFSET ?`, kind, p.limit, p.skip)
	if err != nil {
		return err
	}
	defer rows.Close()
	out := []map[string]any{}
	for rows.Next() {
		var id, amount, balanceAfter int64
		var ext, name, username, desc, method sql.NullString
		var orderID, userID sql.NullInt64
		var created store.Time
		if err := rows.Scan(&id, &ext, &orderID, &userID, &name, &username, &amount, &balanceAfter, &created, &desc, &method); err != nil {
			return err
		}
		ref := ext.String
		if ref == "" {
			ref = strconv.FormatInt(id, 10)
		}
		row := map[string]any{
			"id":            ref,
			"order_id":      nil,
			"user_name":     "Unknown",
			"username":      "Unknown",
			"amount":        amount,
			"balance_after": balanceAfter,
			"created_at":    created.ISO(),
			"description":   nullable(desc),
			"channel":       method.String,
		}
		if orderID.Valid {
			row["order_id"] = orderID.Int64
		}
		if userID.Valid {
			row["user_name"], row["username"] = nullable(name), username.String
		}
		out = append(out, row)
	}
	if err := rows.Err(); err != nil {
		return err
	}
	return ok(w, out)
}
