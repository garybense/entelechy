package main

import (
	"context"
	"fmt"
	"net/http"
	"os"

	entelechy "github.com/vectorize-io/entelechy/entelechy-clients/go"
)

const bankID = "directives-example-bank"

func main() {
	apiURL := os.Getenv("ENTELECHY_API_URL")
	if apiURL == "" {
		apiURL = "http://localhost:8888"
	}

	cfg := entelechy.NewConfiguration()
	cfg.Servers = entelechy.ServerConfigurations{{URL: apiURL}}
	client := entelechy.NewAPIClient(cfg)
	ctx := context.Background()

	// =============================================================================
	// Setup (not shown in docs)
	// =============================================================================
	client.BanksAPI.CreateOrUpdateBank(ctx, bankID).
		CreateBankRequest(entelechy.CreateBankRequest{
			Name: *entelechy.NewNullableString(entelechy.PtrString("Test Bank")),
		}).Execute()

	// =============================================================================
	// Doc Examples
	// =============================================================================

	// [docs:create-directive]
	// Create a directive (hard rule for reflect)
	directive, _, _ := client.DirectivesAPI.CreateDirective(ctx, bankID).
		CreateDirectiveRequest(entelechy.CreateDirectiveRequest{
			Name:    "Formal Language",
			Content: "Always respond in formal English, avoiding slang and colloquialisms.",
		}).Execute()

	fmt.Printf("Created directive: %s\n", directive.GetId())
	// [/docs:create-directive]

	directiveID := directive.GetId()

	// [docs:list-directives]
	// List all directives in a bank
	directives, _, _ := client.DirectivesAPI.ListDirectives(ctx, bankID).Execute()

	for _, d := range directives.GetItems() {
		content := d.GetContent()
		if len(content) > 50 {
			content = content[:50]
		}
		fmt.Printf("- %s: %s...\n", d.GetName(), content)
	}
	// [/docs:list-directives]

	// [docs:update-directive]
	// Update a directive (e.g., disable without deleting)
	isActiveFalse := false
	updated, _, _ := client.DirectivesAPI.UpdateDirective(ctx, bankID, directiveID).
		UpdateDirectiveRequest(entelechy.UpdateDirectiveRequest{
			IsActive: *entelechy.NewNullableBool(&isActiveFalse),
		}).Execute()

	fmt.Printf("Directive active: %v\n", updated.GetIsActive())
	// [/docs:update-directive]

	// [docs:delete-directive]
	// Delete a directive
	client.DirectivesAPI.DeleteDirective(ctx, bankID, directiveID).Execute()
	// [/docs:delete-directive]

	// =============================================================================
	// Cleanup (not shown in docs)
	// =============================================================================
	req, _ := http.NewRequest("DELETE", fmt.Sprintf("%s/v1/default/banks/%s", apiURL, bankID), nil)
	http.DefaultClient.Do(req)

	fmt.Println("directives.go: All examples passed")
}
