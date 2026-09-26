package api

import (
	"encoding/json"
	"fmt"
	"net/http"
	"strconv"
	"strings"

	"github.com/WilliamFeng7/CaffeeOrder/apps/backend/internal/orders"
)

func (s *Server) myOrders(w http.ResponseWriter, r *http.Request) error {
	u, err := s.currentUser(r)
	if err != nil {
		return err
	}
	p, err := pagination(r, 20)
	if err != nil {
		return err
	}
	list, err := s.orders.ForUser(r.Context(), u.ID, p.skip, p.limit)
	if err != nil {
		return err
	}
	return ok(w, list)
}

type orderLine struct {
	MenuItemID *int64          `json:"menu_item_id"`
	Spec       json.RawMessage `json:"spec"`
	Quantity   *Number         `json:"quantity"`
}

type orderBody struct {
	Items *[]orderLine `json:"items"`
}

// parseOrder validates the body the way the Python schema did: 1–50 lines,
// quantity 1–99, options a flat string map.
func parseOrder(r *http.Request) ([]orders.LineInput, error) {
	var body orderBody
	if err := decodeJSON(r, &body); err != nil {
		return nil, err
	}
	if body.Items == nil {
		return nil, missingField("body", "items")
	}
	items := *body.Items
	if len(items) < 1 {
		return nil, validation([]any{"body", "items"}, "List should have at least 1 item after validation, not 0", "too_short")
	}
	if len(items) > 50 {
		return nil, validation([]any{"body", "items"},
			fmt.Sprintf("List should have at most 50 items after validation, not %d", len(items)), "too_long")
	}
	lines := make([]orders.LineInput, 0, len(items))
	for i, it := range items {
		loc := func(field string) []any { return []any{"body", "items", i, field} }
		if it.MenuItemID == nil {
			return nil, validation(loc("menu_item_id"), "Field required", "missing")
		}
		qty := int64(1)
		if it.Quantity != nil && it.Quantity.Set && !it.Quantity.Null {
			qty = it.Quantity.Value
		}
		if qty < 1 {
			return nil, validation(loc("quantity"), "Input should be greater than or equal to 1", "greater_than_equal")
		}
		if qty > 99 {
			return nil, validation(loc("quantity"), "Input should be less than or equal to 99", "less_than_equal")
		}
		spec := map[string]string{}
		if len(it.Spec) > 0 && string(it.Spec) != "null" {
			var raw map[string]any
			if err := json.Unmarshal(it.Spec, &raw); err != nil {
				return nil, validation(loc("spec"), "Input should be a valid dictionary", "dict_type")
			}
			for k, v := range raw {
				str, isStr := v.(string)
				if !isStr {
					return nil, validation(append(loc("spec"), k), "Input should be a valid string", "string_type")
				}
				spec[k] = str
			}
		}
		lines = append(lines, orders.LineInput{MenuItemID: *it.MenuItemID, Spec: spec, Quantity: qty})
	}
	return lines, nil
}

func (s *Server) createOrder(w http.ResponseWriter, r *http.Request) error {
	u, err := s.currentUser(r)
	if err != nil {
		return err
	}
	lines, err := parseOrder(r)
	if err != nil {
		return err
	}
	// The "closed" switch in the admin console used to be decorative.
	if open, _, err := s.shopState(r.Context()); err != nil {
		return err
	} else if !open {
		return fail(http.StatusConflict, "本店暂停营业，暂时无法下单 (The shop is closed)")
	}
	resp, err := s.orders.Create(r.Context(), u.ID, lines)
	if err != nil {
		return err
	}
	return ok(w, resp)
}

func (s *Server) cancelOrder(w http.ResponseWriter, r *http.Request) error {
	u, err := s.currentUser(r)
	if err != nil {
		return err
	}
	id, err := pathID(r, "id")
	if err != nil {
		return err
	}
	resp, err := s.orders.Cancel(r.Context(), id, u.ID, u.Role)
	if err != nil {
		return err
	}
	return ok(w, resp)
}

// staff is the barista/admin gate used by the /orders staff routes.
func (s *Server) staff(r *http.Request) (*User, error) {
	u, err := s.currentUser(r)
	if err != nil {
		return nil, err
	}
	if u.Role != "admin" && u.Role != "barista" {
		return nil, fail(http.StatusForbidden, "Permission denied")
	}
	return u, nil
}

func (s *Server) completeOrder(w http.ResponseWriter, r *http.Request) error {
	if _, err := s.staff(r); err != nil {
		return err
	}
	id, err := pathID(r, "id")
	if err != nil {
		return err
	}
	resp, err := s.orders.Complete(r.Context(), id)
	if err != nil {
		return err
	}
	return ok(w, resp)
}

func (s *Server) syncOrders(w http.ResponseWriter, r *http.Request) error {
	if _, err := s.staff(r); err != nil {
		return err
	}
	since := 0.0
	if v := r.URL.Query().Get("since"); v != "" {
		f, err := strconv.ParseFloat(v, 64)
		if err != nil || f < 0 {
			return validation([]any{"query", "since"}, "Input should be a number >= 0", "greater_than_equal")
		}
		since = f
	}
	list, err := s.orders.Sync(r.Context(), since)
	if err != nil {
		return err
	}
	return ok(w, list)
}

// statusValue reads a status given as the API value ("processing") or the
// stored name ("PROCESSING").
func statusValue(v string) (string, error) {
	st := strings.ToLower(strings.TrimSpace(v))
	if !orders.ValidStatus(st) {
		return "", fmt.Errorf("unknown status %q", v)
	}
	return st, nil
}

func (s *Server) patchOrderStatus(w http.ResponseWriter, r *http.Request) error {
	u, err := s.staff(r)
	if err != nil {
		return err
	}
	id, err := pathID(r, "id")
	if err != nil {
		return err
	}
	var body struct {
		Status *string `json:"status"`
	}
	if err := decodeJSON(r, &body); err != nil {
		return err
	}
	if body.Status == nil {
		return missingField("body", "status")
	}
	to, err := statusValue(*body.Status)
	if err != nil {
		return validation([]any{"body", "status"}, "Input should be 'created', 'processing', 'ready', 'completed' or 'refunded'", "enum")
	}
	o, err := s.orders.ChangeStatus(r.Context(), id, to, u.Role, nil)
	if err != nil {
		return err
	}
	resp, err := s.orders.Response(r.Context(), o, to == orders.Refunded)
	if err != nil {
		return err
	}
	return ok(w, resp)
}

func (s *Server) adminOrders(w http.ResponseWriter, r *http.Request) error {
	if _, err := s.requireRole(r, "admin", "barista"); err != nil {
		return err
	}
	// Both old consoles call this without paging; 20 rows is why the kitchen
	// board lost orders. The default is now the maximum page.
	p, err := pagination(r, 200)
	if err != nil {
		return err
	}
	status := ""
	if v := r.URL.Query().Get("status"); v != "" {
		if status, err = statusValue(v); err != nil {
			return ok(w, []orders.Response{})
		}
	}
	list, err := s.orders.All(r.Context(), status, p.skip, p.limit)
	if err != nil {
		return err
	}
	return ok(w, list)
}

// adminOrderStatus is the console's move: the lifecycle plus a direct jump to
// completed from created/processing. It answers with the plain order row.
func (s *Server) adminOrderStatus(w http.ResponseWriter, r *http.Request) error {
	u, err := s.requireRole(r, "admin", "barista")
	if err != nil {
		return err
	}
	id, err := pathID(r, "id")
	if err != nil {
		return err
	}
	to, err := statusValue(r.URL.Query().Get("status"))
	if err != nil {
		return validation([]any{"query", "status"}, "Input should be 'created', 'processing', 'ready', 'completed' or 'refunded'", "enum")
	}
	o, err := s.orders.ChangeStatus(r.Context(), id, to, u.Role, orders.CompleteShortcuts)
	if err != nil {
		return err
	}
	return ok(w, o.Raw())
}
