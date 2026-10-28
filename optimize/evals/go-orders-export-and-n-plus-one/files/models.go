package main

import "time"

type Order struct {
	ID         int64     `json:"id"`
	CustomerID int       `json:"customer_id"`
	Status     string    `json:"status"`
	TotalCents int       `json:"total_cents"`
	Note       string    `json:"-"`
	CreatedAt  time.Time `json:"created_at"`
}

type Summary struct {
	CustomerID   int   `json:"customer_id"`
	Orders       int   `json:"orders"`
	Items        int   `json:"items"`
	RevenueCents int64 `json:"revenue_cents"`
}
