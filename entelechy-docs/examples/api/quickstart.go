package main

import (
	"context"
	"fmt"
	"log"
	"net/http"
	"os"
	"time"

	entelechy "github.com/vectorize-io/entelechy/entelechy-clients/go"
)

func main() {
	apiURL := os.Getenv("ENTELECHY_API_URL")
	if apiURL == "" {
		apiURL = "http://localhost:8888"
	}

	// [docs:quickstart-full]
	cfg := entelechy.NewConfiguration()
	cfg.Servers = entelechy.ServerConfigurations{
		{URL: "http://localhost:8888"},
	}
	client := entelechy.NewAPIClient(cfg)
	ctx := context.Background()

	// Retain a memory
	retainReq := entelechy.RetainRequest{
		Items: []entelechy.MemoryItem{
			{Content: "Alice works at Google"},
		},
	}
	client.MemoryAPI.RetainMemories(ctx, "my-bank").RetainRequest(retainReq).Execute()

	// Recall memories
	recallReq := entelechy.RecallRequest{
		Query: "What does Alice do?",
	}
	resp, _, _ := client.MemoryAPI.RecallMemories(ctx, "my-bank").RecallRequest(recallReq).Execute()
	for _, r := range resp.Results {
		fmt.Println(r.Text)
	}

	// Reflect - generate response
	reflectReq := entelechy.ReflectRequest{
		Query: "Tell me about Alice",
	}
	answer, _, _ := client.MemoryAPI.Reflect(ctx, "my-bank").ReflectRequest(reflectReq).Execute()
	fmt.Println(answer.GetText())
	// [/docs:quickstart-full]

	// Cleanup (not shown in docs)
	req, _ := http.NewRequest("DELETE", fmt.Sprintf("%s/v1/default/banks/my-bank", apiURL), nil)
	http.DefaultClient.Do(req)

	// [docs:nullable-fields]
	// Creating nullable values
	timestamp := time.Date(2024, 1, 15, 10, 0, 0, 0, time.UTC)
	retainReq2 := entelechy.RetainRequest{
		Items: []entelechy.MemoryItem{
			{
				Content:   "Alice got promoted",
				Context:   *entelechy.NewNullableString(entelechy.PtrString("career update")),
				Timestamp: *entelechy.NewNullableTimestamp(&entelechy.Timestamp{TimeTime: entelechy.PtrTime(timestamp)}),
				Tags:      []string{"career"},
			},
		},
	}
	retainResp, _, _ := client.MemoryAPI.RetainMemories(ctx, "my-bank").RetainRequest(retainReq2).Execute()

	// Checking if a value is set
	if retainResp.HasOperationId() {
		fmt.Println("OperationId:", retainResp.GetOperationId())
	}
	// [/docs:nullable-fields]

	// [docs:error-handling]
	_, httpResp2, err := client.MemoryAPI.RecallMemories(ctx, "my-bank").
		RecallRequest(recallReq).
		Execute()

	if err != nil {
		log.Fatalf("Recall failed: %v", err)
	}
	defer httpResp2.Body.Close()
	// [/docs:error-handling]

	fmt.Println("quickstart.go: All examples passed")
}
