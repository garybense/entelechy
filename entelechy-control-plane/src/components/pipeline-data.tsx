"use client";

import { useCallback, useEffect, useState } from "react";
import { client, PolicyRecord } from "@/lib/api";
import { useBank } from "@/lib/bank-context";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { RefreshCw } from "lucide-react";

export const POLICY_KEYS = [
  "verbosity",
  "abstraction",
  "creativity",
  "empathy",
  "rigor",
  "tool_use_probability",
] as const;

/** Loads the bank's policy history. Every figure the pipeline pages show comes from this. */
export function usePolicyHistory() {
  const { currentBank } = useBank();
  const [policies, setPolicies] = useState<PolicyRecord[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    if (!currentBank) return;
    setLoading(true);
    setError(null);
    try {
      const res = await client.listPolicies(currentBank, 100);
      setPolicies(res.policies);
    } catch (e) {
      setPolicies(null);
      setError(e instanceof Error ? e.message : "Failed to load policies");
    } finally {
      setLoading(false);
    }
  }, [currentBank]);

  useEffect(() => {
    load();
  }, [load]);

  return { bank: currentBank, policies, error, loading, reload: load };
}

export function PageHeader({
  icon,
  title,
  blurb,
  onReload,
  loading,
}: {
  icon: React.ReactNode;
  title: string;
  blurb: string;
  onReload?: () => void;
  loading?: boolean;
}) {
  return (
    <div className="flex items-start justify-between gap-4">
      <div>
        <h1 className="text-3xl font-bold mb-2 text-foreground flex items-center gap-2">
          {icon}
          {title}
        </h1>
        <p className="text-muted-foreground">{blurb}</p>
      </div>
      {onReload && (
        <Button variant="outline" size="sm" onClick={onReload} disabled={loading}>
          <RefreshCw className={`w-4 h-4 mr-2 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </Button>
      )}
    </div>
  );
}

/** Shown when the bank has no stored policies yet, or loading failed. States the real reason. */
export function NoPolicies({ bank, error }: { bank: string | null; error: string | null }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{error ? "Could not load policy history" : "No policies recorded yet"}</CardTitle>
        <CardDescription>
          {error
            ? error
            : !bank
              ? "Select a bank."
              : `Bank ${bank} has no stored policy. A policy is recorded each time a session is bootstrapped or the bank is distilled; run one from the Chat Simulator or call POST /sessions/bootstrap.`}
        </CardDescription>
      </CardHeader>
    </Card>
  );
}

export function Bar({ label, value }: { label: string; value: number }) {
  const pct = Math.max(0, Math.min(1, value)) * 100;
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-sm">
        <span className="font-mono text-muted-foreground">{label}</span>
        <span className="font-mono text-foreground">{value.toFixed(3)}</span>
      </div>
      <div className="h-2 rounded bg-muted overflow-hidden">
        <div className="h-full bg-primary" style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

export function numericEntries(obj: Record<string, unknown> | null | undefined): [string, number][] {
  return Object.entries(obj ?? {}).filter(
    (e): e is [string, number] => typeof e[1] === "number" && Number.isFinite(e[1])
  );
}

export function when(iso: string | null): string {
  return iso ? new Date(iso).toLocaleString() : "";
}
