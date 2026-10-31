import React from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { GitBranch } from "lucide-react";

export default function PolicyControlView() {
  return (
    <div className="p-4 space-y-6">
      <div>
        <h1 className="text-3xl font-bold mb-2 text-foreground flex items-center gap-2">
          <GitBranch className="w-8 h-8 text-primary" />
          Policy Control & Inertia
        </h1>
        <p className="text-muted-foreground">
          Monitors and enforces the stability of the policy vector over time. Rejects policy updates that induce unstable drift.
        </p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>No data source yet</CardTitle>
          <CardDescription>
            The API does not expose this stage's measurements, so there is nothing real to show.
            This page previously displayed fixed example numbers, which were removed.
          </CardDescription>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          It will populate once the API publishes an endpoint for it.
        </CardContent>
      </Card>
    </div>
  );
}
