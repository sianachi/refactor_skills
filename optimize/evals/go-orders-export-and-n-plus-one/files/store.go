package main

import (
	"context"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

func allOrders(ctx context.Context, db *pgxpool.Pool) ([]Order, error) {
	rows, err := db.Query(ctx, `SELECT * FROM orders ORDER BY id`)
	if err != nil {
		return nil, err
	}
	return pgx.CollectRows(rows, func(r pgx.CollectableRow) (Order, error) {
		var o Order
		err := r.Scan(&o.ID, &o.CustomerID, &o.Status, &o.TotalCents, &o.Note, &o.CreatedAt)
		return o, err
	})
}

func customerExists(ctx context.Context, db *pgxpool.Pool, id int) (bool, error) {
	var ok bool
	err := db.QueryRow(ctx, `SELECT EXISTS (SELECT 1 FROM customers WHERE id = $1)`, id).Scan(&ok)
	return ok, err
}

func ordersForCustomer(ctx context.Context, db *pgxpool.Pool, customerID int) ([]Order, error) {
	all, err := allOrders(ctx, db)
	if err != nil {
		return nil, err
	}
	var out []Order
	for _, o := range all {
		if o.CustomerID == customerID {
			out = append(out, o)
		}
	}
	return out, nil
}

func itemTotals(ctx context.Context, db *pgxpool.Pool, orderID int64) (int, int64, error) {
	var count int
	var revenue int64
	err := db.QueryRow(ctx,
		`SELECT COUNT(*), COALESCE(SUM(qty * price_cents), 0) FROM order_items WHERE order_id = $1`, orderID,
	).Scan(&count, &revenue)
	return count, revenue, err
}
