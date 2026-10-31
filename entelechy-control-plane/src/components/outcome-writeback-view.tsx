import React from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Save } from "lucide-react";

export default function OutcomeWritebackView() {
  return (
    <div className="p-4 space-y-6">
      <div>
        <h1 className="text-3xl font-bold mb-2 text-foreground flex items-center gap-2">
          <Save className="w-8 h-8 text-primary" />
          Outcome Writeback
        </h1>
        <p className="text-muted-foreground">
          Logs the results of policy execution back into the memory graph as Experiences, closing the SVT-CP loop.
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
