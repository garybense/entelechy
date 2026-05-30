import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { LayoutDashboard, BrainCircuit, Activity, Settings, GitBranch, ArrowRight } from "lucide-react";
import { useBank } from "@/lib/bank-context";

export default function MwpmcOverviewView() {
  const { currentBank } = useBank();

  return (
    <div className="p-4 space-y-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold mb-2 text-foreground flex items-center gap-2">
            <LayoutDashboard className="w-8 h-8 text-primary" />
            MWPMC Dashboard
          </h1>
          <p className="text-muted-foreground">
            System overview of the Memory-Weighted Policy Modulation Controller for bank: <span className="font-mono text-primary">{currentBank}</span>
          </p>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">System Status</CardTitle>
            <Activity className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-foreground">Active</div>
            <p className="text-xs text-muted-foreground mt-1">SVT-CP Loop Online</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Memory Graph</CardTitle>
            <BrainCircuit className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-foreground">Synchronized</div>
            <p className="text-xs text-muted-foreground mt-1">Ready for feature extraction</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Current Drift</CardTitle>
            <GitBranch className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-foreground">0.05</div>
            <p className="text-xs text-muted-foreground mt-1">Well within $\epsilon$-limit (0.15)</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Policy</CardTitle>
            <Settings className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-foreground">Modulating</div>
            <p className="text-xs text-muted-foreground mt-1">Inference strictly controlled</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>SVT Continuation Protocol Pipeline</CardTitle>
          <CardDescription>The current operational state of the feedback loop.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col md:flex-row items-center justify-between gap-4 py-6">
            <div className="flex flex-col items-center p-4 border rounded-lg bg-card shadow-sm flex-1 text-center">
              <span className="font-bold text-lg text-primary mb-2">Stage A</span>
              <span className="text-sm font-medium">Feature Extraction</span>
              <span className="text-xs text-muted-foreground mt-1">Computes Vector F</span>
            </div>
            
            <ArrowRight className="hidden md:block text-muted-foreground" />

            <div className="flex flex-col items-center p-4 border rounded-lg bg-card shadow-sm flex-1 text-center">
              <span className="font-bold text-lg text-primary mb-2">Stage B</span>
              <span className="text-sm font-medium">Policy Synthesis</span>
              <span className="text-xs text-muted-foreground mt-1">Derives Vector P</span>
            </div>

            <ArrowRight className="hidden md:block text-muted-foreground" />

            <div className="flex flex-col items-center p-4 border rounded-lg bg-card shadow-sm flex-1 text-center">
              <span className="font-bold text-lg text-primary mb-2">Control</span>
              <span className="text-sm font-medium">Inertia Check</span>
              <span className="text-xs text-muted-foreground mt-1">Enforces $\epsilon$-boundaries</span>
            </div>

             <ArrowRight className="hidden md:block text-muted-foreground" />

            <div className="flex flex-col items-center p-4 border rounded-lg bg-card shadow-sm flex-1 text-center">
              <span className="font-bold text-lg text-primary mb-2">Outcome</span>
              <span className="text-sm font-medium">Writeback Log</span>
              <span className="text-xs text-muted-foreground mt-1">Records Experience</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
