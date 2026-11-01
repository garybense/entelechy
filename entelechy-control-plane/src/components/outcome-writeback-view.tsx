"use client";

import React, { useCallback, useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Save } from "lucide-react";
import { toast } from "sonner";
import { client, OutcomeRecord } from "@/lib/api";
import { useBank } from "@/lib/bank-context";
import { PageHeader, when } from "./pipeline-data";

export default function OutcomeWritebackView() {
  const { currentBank } = useBank();
  const [data, setData] = useState<{ successes: number; failures: number; outcomes: OutcomeRecord[] } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState("");
  const [note, setNote] = useState("");
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    if (!currentBank) return;
    setLoading(true);
    setError(null);
    try {
      setData(await client.listOutcomes(currentBank));
    } catch (e) {
      setData(null);
      setError(e instanceof Error ? e.message : "Failed to load outcomes");
    } finally {
      setLoading(false);
    }
  }, [currentBank]);

  useEffect(() => {
    load();
  }, [load]);

  const write = async (outcome: "success" | "failure") => {
    if (!currentBank) return;
    setSaving(true);
    try {
      await client.writeOutcome({
        bank_id: currentBank,
        outcome,
        session_id: sessionId.trim() || undefined,
        note: note.trim() || undefined,
      });
      toast.success("Outcome queued. It appears below once extraction has run.");
      setNote("");
      setSessionId("");
      load();
    } catch {
      // the client already reports the failure
    } finally {
      setSaving(false);
    }
  };

  const total = data ? data.successes + data.failures : 0;

  return (
    <div className="p-4 space-y-6">
      <PageHeader
        icon={<Save className="w-8 h-8 text-primary" />}
        title="Outcome Writeback"
        blurb="Results of acting on a policy, stored as tagged memories. The next bootstrap derives Vector F success rate from them."
        onReload={load}
        loading={loading}
      />
      <Card>
        <CardHeader>
          <CardTitle>Record an outcome</CardTitle>
          <CardDescription>
            Reusing a session id replaces that session&apos;s earlier outcome.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid gap-3 md:grid-cols-2">
            <Input placeholder="Session id (optional)" value={sessionId} onChange={(e) => setSessionId(e.target.value)} />
            <Input placeholder="What happened (optional)" value={note} onChange={(e) => setNote(e.target.value)} />
          </div>
          <div className="flex gap-2">
            <Button disabled={saving || !currentBank} onClick={() => write("success")}>
              Mark success
            </Button>
            <Button variant="outline" disabled={saving || !currentBank} onClick={() => write("failure")}>
              Mark failure
            </Button>
          </div>
        </CardContent>
      </Card>
      {error && (
        <Card>
          <CardHeader>
            <CardTitle>Could not load outcomes</CardTitle>
            <CardDescription>{error}</CardDescription>
          </CardHeader>
        </Card>
      )}
      {data && (
        <>
          <div className="grid gap-4 md:grid-cols-3">
            <Card>
              <CardHeader>
                <CardDescription>Successes</CardDescription>
                <CardTitle>{data.successes}</CardTitle>
              </CardHeader>
            </Card>
            <Card>
              <CardHeader>
                <CardDescription>Failures</CardDescription>
                <CardTitle>{data.failures}</CardTitle>
              </CardHeader>
            </Card>
            <Card>
              <CardHeader>
                <CardDescription>Success rate</CardDescription>
                <CardTitle>{total ? (data.successes / total).toFixed(3) : "no outcomes yet"}</CardTitle>
              </CardHeader>
            </Card>
          </div>
          <Card>
            <CardHeader>
              <CardTitle>Recorded outcomes</CardTitle>
            </CardHeader>
            <CardContent>
              {data.outcomes.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  None yet for this bank. Outcomes show here after their retain operation has extracted facts.
                </p>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>When</TableHead>
                      <TableHead>Outcome</TableHead>
                      <TableHead>Memory</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {data.outcomes.map((o) => (
                      <TableRow key={o.id}>
                        <TableCell>{when(o.created_at)}</TableCell>
                        <TableCell>{o.outcome}</TableCell>
                        <TableCell className="max-w-xl truncate">{o.text}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
