package main

import (
	"context"
	"log"
	"net/http"
	"os"
)

func main() {
	ctx := context.Background()
	db, err := openDB(ctx)
	if err != nil {
		log.Fatal(err)
	}
	if err := migrate(ctx, db); err != nil {
		log.Fatal("migrate: ", err)
	}
	s := &server{db: db}
	mux := http.NewServeMux()
	mux.HandleFunc("GET /export/orders.csv", s.exportOrders)
	mux.HandleFunc("GET /customers/{id}/summary", s.customerSummary)
	mux.HandleFunc("GET /orders", s.listOrders)
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}
	log.Fatal(http.ListenAndServe("127.0.0.1:"+port, mux))
}
