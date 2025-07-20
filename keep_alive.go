package main

import (
	"fmt"
	"net/http"
)

func StartKeepAlive() {
	go func() {
		http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
			fmt.Fprintf(w, "I'm alive! Tabel-Go-Bot for Render.com")
		})
		http.ListenAndServe(":10000", nil)
	}()
}
