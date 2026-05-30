import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Save, History, ActivitySquare, CheckCircle } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";

export default function OutcomeWritebackView() {
  // Placeholder data for recent writebacks
  const recentWritebacks = [
    {
      id: "wb-001",
      timestamp: "2026-05-29T10:15:00Z",
      action: "SVT-CP Complete",
      outcome: "Success",
      vectorF: "[0.12, 0.45, 0.95, 0.88]",
      vectorP: "[0.20, 0.85, 0.20, 0.10, 0.95, 0.90]"
    },
    {
      id: "wb-002",
      timestamp: "2026-05-29T10:20:00Z",
      action: "Policy Injection",
      outcome: "Success",
      vectorF: "[0.15, 0.42, 0.96, 0.85]",
      vectorP: "[0.22, 0.84, 0.18, 0.12, 0.96, 0.88]"
    },
     {
      id: "wb-003",
      timestamp: "2026-05-29T10:25:00Z",
      action: "Policy Injection",
      outcome: "Rejected (Drift)",
      vectorF: "[0.85, 0.92, 0.16, 0.15]",
      vectorP: "[0.92, 0.14, 0.88, 0.92, 0.16, 0.18]"
    }
  ];

  return (
    <div className="p-4 space-y-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold mb-2 text-foreground flex items-center gap-2">
            <Save className="w-8 h-8 text-primary" />
            Outcome Writeback
          </h1>
          <p className="text-muted-foreground">
            Logs the results of policy execution back into the memory graph as Experiences, closing the SVT-CP loop.
          </p>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        <Card className="col-span-1">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ActivitySquare className="w-5 h-5 text-muted-foreground" />
              Writeback Status
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col items-center justify-center py-8">
            <CheckCircle className="w-16 h-16 text-green-500 mb-4" />
            <h3 className="text-xl font-bold text-foreground">Loop Closed</h3>
            <p className="text-sm text-muted-foreground text-center mt-2">The latest interaction outcome has been successfully written to the memory bank.</p>
          </CardContent>
        </Card>

        <Card className="col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <History className="w-5 h-5 text-muted-foreground" />
              Recent Writeback Logs
            </CardTitle>
            <CardDescription>Historical record of injected policies and their outcomes.</CardDescription>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[300px] w-full rounded-md border p-4">
              <div className="space-y-4">
                {recentWritebacks.map((log) => (
                  <div key={log.id} className="flex flex-col space-y-2 pb-4 border-b last:border-0 last:pb-0">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-sm">{log.action}</span>
                      <span className="text-xs text-muted-foreground">{new Date(log.timestamp).toLocaleTimeString()}</span>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div>
                        <span className="text-muted-foreground block">Outcome:</span>
                        <span className={`font-medium ${log.outcome === 'Success' ? 'text-green-500' : 'text-destructive'}`}>
                          {log.outcome}
                        </span>
                      </div>
                      <div>
                        <span className="text-muted-foreground block">Vectors:</span>
                        <span className="font-mono block truncate">F: {log.vectorF}</span>
                        <span className="font-mono block truncate">P: {log.vectorP}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
