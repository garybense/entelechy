"use client";

import React from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { GitBranch } from "lucide-react";
import { NoPolicies, PageHeader, POLICY_KEYS, usePolicyHistory, when } from "./pipeline-data";

/** Largest per-parameter change between a policy and the one stored before it. */
function maxDelta(cur: Record<string, unknown> | null, prev: Record<string, unknown> | null | undefined) {
  if (!cur || !prev) return null;
  let max = 0;
  let key = "";
  for (const k of POLICY_KEYS) {
    const a = cur[k];
    const b = prev[k];
    if (typeof a === "number" && typeof b === "number" && Math.abs(a - b) >= max) {
      max = Math.abs(a - b);
      key = k;
    }
  }
  return key ? { max, key } : null;
}

export default function PolicyControlView() {
  const { bank, policies, error, loading, reload } = usePolicyHistory();
  const rows = (policies ?? []).map((p, i, all) => ({ p, delta: maxDelta(p.policy, all[i + 1]?.policy) }));
  const clamped = (policies ?? []).filter((p) => p.inertia_applied).length;
  const withDelta = rows.filter((r) => r.delta);
  const worst = withDelta.reduce((m, r) => Math.max(m, r.delta!.max), 0);

  return (
    <div className="p-4 space-y-6">
      <PageHeader
        icon={<GitBranch className="w-8 h-8 text-primary" />}
        title="Policy Control & Inertia"
        blurb="How far each new policy moved from the previous one, and when policy inertia clamped the change to keep it stable."
        onReload={reload}
        loading={loading}
      />
      {!policies || policies.length === 0 ? (
        <NoPolicies bank={bank} error={error} />
      ) : (
        <>
          <div className="grid gap-4 md:grid-cols-3">
            <Card>
              <CardHeader>
                <CardDescription>Policies stored</CardDescription>
                <CardTitle>{policies.length}</CardTitle>
              </CardHeader>
            </Card>
            <Card>
              <CardHeader>
                <CardDescription>Clamped by inertia</CardDescription>
                <CardTitle>{clamped}</CardTitle>
              </CardHeader>
            </Card>
            <Card>
              <CardHeader>
                <CardDescription>Largest single-step change</CardDescription>
                <CardTitle>{withDelta.length ? worst.toFixed(3) : "n/a"}</CardTitle>
              </CardHeader>
            </Card>
          </div>
          <Card>
            <CardHeader>
              <CardTitle>Step-by-step drift</CardTitle>
              <CardDescription>Change is measured against the policy stored immediately before.</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>When</TableHead>
                    <TableHead>Source</TableHead>
                    <TableHead>Largest change</TableHead>
                    <TableHead>Parameter</TableHead>
                    <TableHead>Inertia</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {rows.map(({ p, delta }) => (
                    <TableRow key={p.id}>
                      <TableCell>{when(p.created_at)}</TableCell>
                      <TableCell>{p.source}</TableCell>
                      <TableCell>{delta ? delta.max.toFixed(3) : "first policy"}</TableCell>
                      <TableCell>{delta?.key ?? ""}</TableCell>
                      <TableCell>{p.inertia_applied ? "clamped" : "free"}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
