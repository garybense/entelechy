"use client";

import React from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Beaker } from "lucide-react";
import { Bar, NoPolicies, PageHeader, numericEntries, usePolicyHistory, when } from "./pipeline-data";

export default function FeatureExtractionView() {
  const { bank, policies, error, loading, reload } = usePolicyHistory();
  const withF = (policies ?? []).filter((p) => p.vector_f);
  const latest = withF[0];

  const scalars = numericEntries(latest?.vector_f).filter(([k]) => k !== "total_memories" && k !== "mean_age_seconds");
  const counts = numericEntries(latest?.vector_f).filter(([k]) => k === "total_memories" || k === "mean_age_seconds");
  const tags = latest?.vector_f?.tag_recency_weighted as Record<string, number> | undefined;
  const topTags = Object.entries(tags ?? {})
    .sort((a, b) => b[1] - a[1])
    .slice(0, 8);
  const state = numericEntries(latest?.state_vector);

  return (
    <div className="p-4 space-y-6">
      <PageHeader
        icon={<Beaker className="w-8 h-8 text-primary" />}
        title="Feature Extraction (Stage A)"
        blurb="Vector F as measured from the bank's memories at the last bootstrap: frequency, recency, affect, success rate, diversity and stability."
        onReload={reload}
        loading={loading}
      />
      {!latest ? (
        <NoPolicies bank={bank} error={error} />
      ) : (
        <>
          <Card>
            <CardHeader>
              <CardTitle>Latest Vector F</CardTitle>
              <CardDescription>
                {latest.source} at {when(latest.created_at)}
                {counts.map(([k, v]) => ` · ${k}: ${Math.round(v)}`).join("")}
              </CardDescription>
            </CardHeader>
            <CardContent className="grid gap-4 md:grid-cols-2">
              {scalars.map(([k, v]) => (
                <Bar key={k} label={k} value={v} />
              ))}
            </CardContent>
          </Card>
          {state.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>State vector</CardTitle>
                <CardDescription>Reconstructed from the same session (SRL).</CardDescription>
              </CardHeader>
              <CardContent className="grid gap-4 md:grid-cols-2">
                {state.map(([k, v]) => (
                  <Bar key={k} label={k} value={v} />
                ))}
              </CardContent>
            </Card>
          )}
          {topTags.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Top tags (recency weighted)</CardTitle>
              </CardHeader>
              <CardContent className="flex flex-wrap gap-2">
                {topTags.map(([t, w]) => (
                  <span key={t} className="px-2 py-1 rounded border text-sm font-mono">
                    {t} <span className="text-muted-foreground">{w.toFixed(2)}</span>
                  </span>
                ))}
              </CardContent>
            </Card>
          )}
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
                    <TableHead>Memories</TableHead>
                    <TableHead>Success rate</TableHead>
                    <TableHead>Diversity</TableHead>
                    <TableHead>Stability</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {withF.map((p) => {
                    const f = p.vector_f as Record<string, number>;
                    const n = (v: unknown) => (typeof v === "number" ? v.toFixed(3) : "");
                    return (
                      <TableRow key={p.id}>
                        <TableCell>{when(p.created_at)}</TableCell>
                        <TableCell>{p.source}</TableCell>
                        <TableCell>{f.total_memories ?? ""}</TableCell>
                        <TableCell>{n(f.success_rate)}</TableCell>
                        <TableCell>{n(f.semantic_diversity)}</TableCell>
                        <TableCell>{n(f.user_stability)}</TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
