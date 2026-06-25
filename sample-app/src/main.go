package main

import (
	"encoding/json"
	"log"
	"net/http"
	"os"
)

var version = envOr("VERSION", "dev")

func envOr(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}

func main() {
	hostname, _ := os.Hostname()

	mux := http.NewServeMux()
	mux.HandleFunc("/healthz", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte("ok"))
	})
	mux.HandleFunc("/version", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		_ = json.NewEncoder(w).Encode(map[string]string{
			"version":  version,
			"hostname": hostname,
		})
	})
	mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		_, _ = w.Write([]byte("Hello from sample-app " + version + " (" + hostname + ")\n"))
	})

	log.Printf("sample-app %s listening on :8080", version)
	if err := http.ListenAndServe(":8080", mux); err != nil {
		log.Fatal(err)
	}
}
