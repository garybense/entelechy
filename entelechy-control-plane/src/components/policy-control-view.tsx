import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { GitBranch, ShieldAlert, CheckCircle2, TrendingUp, AlertTriangle } from "lucide-react";
import { Progress } from "@/components/ui/progress";

export default function PolicyControlView() {
  // Placeholder data for Inertia constraints
  const currentDrift = 0.05;
  const epsilonLimit = 0.15;
  const isAdmissible = currentDrift < epsilonLimit;

  return (
    <div className="p-4 space-y-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold mb-2 text-foreground flex items-center gap-2">
            <GitBranch className="w-8 h-8 text-primary" />
            Policy Control & Inertia
          </h1>
          <p className="text-muted-foreground">
            Monitors and enforces the stability of the policy vector over time. Rejects policy updates that induce unstable drift.
          </p>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-muted-foreground" />
              Current Drift ($||P_t - P_{"{t-1}"}||$)
            </CardTitle>
            <CardDescription>Measured change between previous and proposed policy vectors.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-4xl font-bold text-primary mb-4">{currentDrift.toFixed(3)}</div>
            <Progress value={(currentDrift / epsilonLimit) * 100} className="h-3" />
            <div className="flex justify-between text-xs text-muted-foreground mt-2">
              <span>0.0</span>
              <span>$\epsilon$-Limit: {epsilonLimit.toFixed(3)}</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ShieldAlert className="w-5 h-5 text-muted-foreground" />
              Admissibility Status
            </CardTitle>
            <CardDescription>Determines if the proposed policy vector is allowed to be injected.</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col items-center justify-center py-6">
            {isAdmissible ? (
              <>
                <CheckCircle2 className="w-16 h-16 text-green-500 mb-4" />
                <h3 className="text-xl font-bold text-green-500">ADMISSIBLE</h3>
                <p className="text-sm text-muted-foreground text-center mt-2">Drift is within acceptable parameters. Policy update approved.</p>
              </>
            ) : (
              <>
                <AlertTriangle className="w-16 h-16 text-destructive mb-4" />
                <h3 className="text-xl font-bold text-destructive">REJECTED: UNSTABLE DRIFT</h3>
                <p className="text-sm text-muted-foreground text-center mt-2">Policy change exceeds $\epsilon$-limit. Enforcing inertia; previous policy retained.</p>
              </>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Inertia Protocol Rules</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="list-disc pl-5 space-y-2 text-sm text-muted-foreground">
            <li><strong>Objective:</strong> Prevent rapid, unpredictable changes in agent personality or methodology (Drift Collapse).</li>
            <li><strong>Mechanism:</strong> Calculate the Euclidean distance between $P_t$ (proposed) and $P_{"{t-1}"}$ (current).</li>
            <li><strong>Constraint ($\epsilon$):</strong> The maximum allowable distance is currently bounded at {epsilonLimit}.</li>
            <li><strong>Action:</strong> If distance &lt; $\epsilon$, inject $P_t$. If distance $\ge \epsilon$, clamp to boundary or retain $P_{"{t-1}"}$.</li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}

