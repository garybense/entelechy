"use client";

import React from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Cpu } from "lucide-react";
import { Bar, NoPolicies, PageHeader, POLICY_KEYS, usePolicyHistory, when } from "./pipeline-data";

export default function PolicySynthesisView() {
  const { bank, policies, error, loading, reload } = usePolicyHistory();
  const latest = policies?.[0];

  return (
    <div className="p-4 space-y-6">
      <PageHeader
        icon={<Cpu className="w-8 h-8 text-primary" />}
        title="Policy Synthesis (Stage B)"
        blurb="The policy vector the modulator derived from Vector F and the state vector, with the reasoning behind it."
        onReload={reload}
        loading={loading}
      />
      {!latest ? (
        <NoPolicies bank={bank} error={error} />
      ) : (
        <>
          <Card>
            <CardHeader>
              <CardTitle>Current policy</CardTitle>
              <CardDescription>
                {latest.source} at {when(latest.created_at)}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                {POLICY_KEYS.map((k) => {
                  const v = latest.policy?.[k];
                  return typeof v === "number" ? <Bar key={k} label={k} value={v} /> : null;
                })}
              </div>
              {latest.rationale && (
                <div className="rounded border p-3 text-sm">
                  <div className="font-medium mb-1">Rationale</div>
                  <p className="text-muted-foreground whitespace-pre-wrap">{latest.rationale}</p>
                </div>
              )}
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>History</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>When</TableHead>
                    <TableHead>Source</TableHead>
                    {POLICY_KEYS.map((k) => (
                      <TableHead key={k}>{k.replace("_probability", "")}</TableHead>
                    ))}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {policies!.map((p) => (
                    <TableRow key={p.id}>
                      <TableCell>{when(p.created_at)}</TableCell>
                      <TableCell>{p.source}</TableCell>
                      {POLICY_KEYS.map((k) => {
                        const v = p.policy?.[k];
                        return <TableCell key={k}>{typeof v === "number" ? v.toFixed(3) : ""}</TableCell>;
                      })}
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
