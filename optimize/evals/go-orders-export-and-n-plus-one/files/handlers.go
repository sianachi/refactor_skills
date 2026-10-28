package main

import (
	"bytes"
	"encoding/csv"
	"encoding/json"
	"log"
	"net/http"
	"strconv"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
)

type server struct {
	db *pgxpool.Pool
}

func (s *server) exportOrders(w http.ResponseWriter, r *http.Request) {
	orders, err := allOrders(r.Context(), s.db)
	if err != nil {
		log.Println("export:", err)
		http.Error(w, "export failed", http.StatusInternalServerError)
		return
	}
	status := r.URL.Query().Get("status")
	var buf bytes.Buffer
	cw := csv.NewWriter(&buf)
	cw.Write([]string{"id", "customer_id", "status", "total_cents", "created_at"})
	for _, o := range orders {
		if status != "" && o.Status != status {
			continue
		}
		cw.Write([]string{
			strconv.FormatInt(o.ID, 10),
			strconv.Itoa(o.CustomerID),
			o.Status,
			strconv.Itoa(o.TotalCents),
			o.CreatedAt.UTC().Format(time.RFC3339),
		})
	}
	cw.Flush()
	w.Header().Set("Content-Type", "text/csv")
	w.Write(buf.Bytes())
}

func (s *server) customerSummary(w http.ResponseWriter, r *http.Request) {
	id, err := strconv.Atoi(r.PathValue("id"))
	if err != nil {
		http.Error(w, "bad customer id", http.StatusBadRequest)
		return
	}
	ok, err := customerExists(r.Context(), s.db, id)
	if err != nil {
		http.Error(w, "summary failed", http.StatusInternalServerError)
		return
	}
	if !ok {
		http.Error(w, "customer not found", http.StatusNotFound)
		return
	}
	orders, err := ordersForCustomer(r.Context(), s.db, id)
	if err != nil {
		http.Error(w, "summary failed", http.StatusInternalServerError)
		return
	}
	sum := Summary{CustomerID: id}
	for _, o := range orders {
		count, revenue, err := itemTotals(r.Context(), s.db, o.ID)
		if err != nil {
			http.Error(w, "summary failed", http.StatusInternalServerError)
			return
		}
		sum.Orders++
		sum.Items += count
		sum.RevenueCents += revenue
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(sum)
}

func (s *server) listOrders(w http.ResponseWriter, r *http.Request) {
	q := r.URL.Query()
	status := q.Get("status")
	customerID := 0
	if c := q.Get("customer_id"); c != "" {
		v, err := strconv.Atoi(c)
		if err != nil {
			http.Error(w, "bad customer_id", http.StatusBadRequest)
			return
		}
		customerID = v
	}
	orders, err := allOrders(r.Context(), s.db)
	if err != nil {
		http.Error(w, "list failed", http.StatusInternalServerError)
		return
	}
	out := []Order{}
	for _, o := range orders {
		if status != "" && o.Status != status {
			continue
		}
		if customerID != 0 && o.CustomerID != customerID {
			continue
		}
		out = append(out, o)
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(out)
}
