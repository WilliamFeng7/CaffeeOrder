package api

import (
	"context"
	"database/sql"
	"net/http"
	"strings"
	"time"
)

type MenuItem struct {
	ID             int64   `json:"id"`
	Name           string  `json:"name"`
	NameCN         *string `json:"name_cn"`
	Description    *string `json:"description"`
	Price          int64   `json:"price"`
	Category       string  `json:"category"`
	ImagePath      string  `json:"image_path"`
	IsActive       bool    `json:"is_active"`
	IsRecommend    bool    `json:"is_recommend"`
	InventoryCount int64   `json:"inventory_count"`
}

const menuColumns = `id, name, name_cn, description, price, category, image_path, is_active, is_recommend, inventory_count`

func (s *Server) products(ctx context.Context, where string, args ...any) ([]MenuItem, error) {
	rows, err := s.db.QueryContext(ctx, `SELECT `+menuColumns+` FROM menuitem `+where, args...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	list := []MenuItem{}
	for rows.Next() {
		var m MenuItem
		var nameCN, desc sql.NullString
		if err := rows.Scan(&m.ID, &m.Name, &nameCN, &desc, &m.Price, &m.Category, &m.ImagePath,
			&m.IsActive, &m.IsRecommend, &m.InventoryCount); err != nil {
			return nil, err
		}
		m.NameCN, m.Description = nullable(nameCN), nullable(desc)
		list = append(list, m)
	}
	return list, rows.Err()
}

const menuTTL = 5 * time.Minute

// listMenu is public: the active products, served from memory for up to five minutes.
func (s *Server) listMenu(w http.ResponseWriter, r *http.Request) error {
	s.menu.mu.Lock()
	items := s.menu.items
	fresh := items != nil && time.Since(s.menu.loadedAt) < menuTTL
	s.menu.mu.Unlock()
	if !fresh {
		var err error
		if items, err = s.products(r.Context(), `WHERE is_active = 1 ORDER BY id`); err != nil {
			return err
		}
		s.menu.mu.Lock()
		s.menu.items, s.menu.loadedAt = items, time.Now()
		s.menu.mu.Unlock()
	}
	w.Header().Set("Cache-Control", "public, max-age=60")
	return ok(w, items)
}

func (s *Server) listProducts(w http.ResponseWriter, r *http.Request) error {
	if _, err := s.requireRole(r, "admin"); err != nil {
		return err
	}
	list, err := s.products(r.Context(), `ORDER BY id`)
	if err != nil {
		return err
	}
	return ok(w, list)
}

type productInput struct {
	Name           Optional `json:"name"`
	NameCN         Optional `json:"name_cn"`
	Description    Optional `json:"description"`
	Price          Number   `json:"price"`
	Category       Optional `json:"category"`
	ImagePath      Optional `json:"image_path"`
	IsActive       *bool    `json:"is_active"`
	IsRecommend    *bool    `json:"is_recommend"`
	InventoryCount Number   `json:"inventory_count"`
}

func (in productInput) validate() error {
	if in.Name.Set && !in.Name.Null && (strings.TrimSpace(in.Name.Value) == "" || len([]rune(in.Name.Value)) > 80) {
		return invalidField("body", "name", "商品名称需为 1-80 个字符 (Name must be 1-80 characters)")
	}
	if in.Price.Set && !in.Price.Null && (in.Price.Value < 0 || in.Price.Value > 1_000_000) {
		return invalidField("body", "price", "价格需在 0 到 1000000 分之间 (Price must be between 0 and 1000000 cents)")
	}
	if in.InventoryCount.Set && !in.InventoryCount.Null && (in.InventoryCount.Value < 0 || in.InventoryCount.Value > 100_000) {
		return invalidField("body", "inventory_count", "库存需在 0 到 100000 之间 (Inventory must be between 0 and 100000)")
	}
	if in.Category.Set && !in.Category.Null && strings.TrimSpace(in.Category.Value) == "" {
		return invalidField("body", "category", "分类不能为空 (Category must not be blank)")
	}
	return nil
}

func (s *Server) productByID(ctx context.Context, id int64) (*MenuItem, error) {
	list, err := s.products(ctx, `WHERE id = ?`, id)
	if err != nil {
		return nil, err
	}
	if len(list) == 0 {
		return nil, fail(http.StatusNotFound, "Product not found")
	}
	return &list[0], nil
}

func (s *Server) createProduct(w http.ResponseWriter, r *http.Request) error {
	if _, err := s.requireRole(r, "admin"); err != nil {
		return err
	}
	var in productInput
	if err := decodeJSON(r, &in); err != nil {
		return err
	}
	switch {
	case !in.Name.Set || in.Name.Null:
		return missingField("body", "name")
	case !in.Price.Set || in.Price.Null:
		return missingField("body", "price")
	case !in.Category.Set || in.Category.Null:
		return missingField("body", "category")
	}
	if err := in.validate(); err != nil {
		return err
	}
	image := "/static/default.png"
	if in.ImagePath.Set && !in.ImagePath.Null && strings.TrimSpace(in.ImagePath.Value) != "" {
		image = strings.TrimSpace(in.ImagePath.Value)
	}
	active, recommend, stock := true, false, int64(999)
	if in.IsActive != nil {
		active = *in.IsActive
	}
	if in.IsRecommend != nil {
		recommend = *in.IsRecommend
	}
	if in.InventoryCount.Set && !in.InventoryCount.Null {
		stock = in.InventoryCount.Value
	}
	res, err := s.db.ExecContext(r.Context(),
		`INSERT INTO menuitem (name, name_cn, description, price, category, image_path, is_active, is_recommend, inventory_count)
		 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`,
		strings.TrimSpace(in.Name.Value), in.NameCN.Ptr(), in.Description.Ptr(), in.Price.Value,
		strings.TrimSpace(in.Category.Value), image, active, recommend, stock)
	if err != nil {
		return err
	}
	s.menu.invalidate()
	id, _ := res.LastInsertId()
	item, err := s.productByID(r.Context(), id)
	if err != nil {
		return err
	}
	return ok(w, item)
}

func (s *Server) updateProduct(w http.ResponseWriter, r *http.Request) error {
	if _, err := s.requireRole(r, "admin"); err != nil {
		return err
	}
	id, err := pathID(r, "id")
	if err != nil {
		return err
	}
	var in productInput
	if err := decodeJSON(r, &in); err != nil {
		return err
	}
	if err := in.validate(); err != nil {
		return err
	}
	if _, err := s.productByID(r.Context(), id); err != nil {
		return err
	}
	sets, args := []string{}, []any{}
	add := func(col string, v any) { sets, args = append(sets, col+" = ?"), append(args, v) }
	// NOT NULL columns ignore an explicit null instead of failing the write.
	if in.Name.Set && !in.Name.Null {
		add("name", strings.TrimSpace(in.Name.Value))
	}
	if in.NameCN.Set {
		add("name_cn", in.NameCN.Ptr())
	}
	if in.Description.Set {
		add("description", in.Description.Ptr())
	}
	if in.Price.Set && !in.Price.Null {
		add("price", in.Price.Value)
	}
	if in.Category.Set && !in.Category.Null {
		add("category", strings.TrimSpace(in.Category.Value))
	}
	if in.ImagePath.Set && !in.ImagePath.Null {
		add("image_path", in.ImagePath.Value)
	}
	if in.IsActive != nil {
		add("is_active", *in.IsActive)
	}
	if in.IsRecommend != nil {
		add("is_recommend", *in.IsRecommend)
	}
	if in.InventoryCount.Set && !in.InventoryCount.Null {
		add("inventory_count", in.InventoryCount.Value)
	}
	if len(sets) > 0 {
		if _, err := s.db.ExecContext(r.Context(), `UPDATE menuitem SET `+strings.Join(sets, ", ")+` WHERE id = ?`,
			append(args, id)...); err != nil {
			return err
		}
		s.menu.invalidate()
	}
	item, err := s.productByID(r.Context(), id)
	if err != nil {
		return err
	}
	return ok(w, item)
}

func (s *Server) deleteProduct(w http.ResponseWriter, r *http.Request) error {
	if _, err := s.requireRole(r, "admin"); err != nil {
		return err
	}
	id, err := pathID(r, "id")
	if err != nil {
		return err
	}
	res, err := s.db.ExecContext(r.Context(), `DELETE FROM menuitem WHERE id = ?`, id)
	if err != nil {
		return err
	}
	if n, _ := res.RowsAffected(); n == 0 {
		return fail(http.StatusNotFound, "Product not found")
	}
	s.menu.invalidate()
	return ok(w, map[string]bool{"ok": true})
}
