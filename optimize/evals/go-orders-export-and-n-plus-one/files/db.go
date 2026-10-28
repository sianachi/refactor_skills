package main

import (
	"context"
	"os"
	"path/filepath"
	"sort"

	"github.com/jackc/pgx/v5/pgxpool"
)

func openDB(ctx context.Context) (*pgxpool.Pool, error) {
	return pgxpool.New(ctx, os.Getenv("DATABASE_URL"))
}

// migrate runs every migrations/*.sql file not yet recorded, in name order.
func migrate(ctx context.Context, db *pgxpool.Pool) error {
	if _, err := db.Exec(ctx, `CREATE TABLE IF NOT EXISTS schema_migrations (name text PRIMARY KEY)`); err != nil {
		return err
	}
	files, err := filepath.Glob("migrations/*.sql")
	if err != nil {
		return err
	}
	sort.Strings(files)
	for _, f := range files {
		name := filepath.Base(f)
		var done bool
		if err := db.QueryRow(ctx, `SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE name = $1)`, name).Scan(&done); err != nil {
			return err
		}
		if done {
			continue
		}
		sql, err := os.ReadFile(f)
		if err != nil {
			return err
		}
		if _, err := db.Exec(ctx, string(sql)); err != nil {
			return err
		}
		if _, err := db.Exec(ctx, `INSERT INTO schema_migrations (name) VALUES ($1)`, name); err != nil {
			return err
		}
	}
	return nil
}
