import React, { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Beaker, Database, Hash, BarChart3, Activity } from "lucide-react";
import { useBank } from "@/lib/bank-context";
import { client } from "@/lib/api";

export default function FeatureExtractionView() {
  const { currentBank } = useBank();
  const [data, setData] = useState<{
    avg_affect: number;
    semantic_diversity: number;
    structural_rigor: number;
    temporal_density: number;
  } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    async function loadStats() {
      setLoading(true);
      try {
        const res = await client.getMwpmcStats(currentBank);
        if (active && res && res.vectorF) {
          setData(res.vectorF);
        }
      } catch (e) {
        console.error("Failed to load MWPMC stats", e);
      } finally {
        if (active) setLoading(false);
      }
    }
    loadStats();
    return () => { active = false; };
  }, [currentBank]);

  const vectorF = data || {
    avg_affect: 0.12,
    semantic_diversity: 0.45,
    structural_rigor: 0.95,
    temporal_density: 0.88,
  };

  return (
    <div className="p-4 space-y-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold mb-2 text-foreground flex items-center gap-2">
            <Beaker className="w-8 h-8 text-primary" />
            Feature Extraction (Stage A)
          </h1>
          <p className="text-muted-foreground">
            Extracts metrics and structural features from the raw memory graph for bank:{" "}
            <span className="font-mono text-primary">{currentBank}</span>. This stage distills
            meaning into quantifiable parameters (Vector F).
          </p>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        {/* Metric Cards */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Average Affect</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-primary">{loading ? "..." : vectorF.avg_affect.toFixed(2)}</div>
            <p className="text-xs text-muted-foreground mt-1">
              Emotional valence of recent memories.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Semantic Diversity</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-primary">
              {loading ? "..." : vectorF.semantic_diversity.toFixed(2)}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Breadth of topics in current context.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Structural Rigor</CardTitle>
            <Hash className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-primary">
              {loading ? "..." : vectorF.structural_rigor.toFixed(2)}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Adherence to defined memory schemas.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Temporal Density</CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-primary">
              {loading ? "..." : vectorF.temporal_density.toFixed(2)}
            </div>
            <p className="text-xs text-muted-foreground mt-1">Frequency of recent interactions.</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Vector F (Feature Vector)</CardTitle>
          <CardDescription>
            The raw numerical representation extracted from the input subgraph.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="bg-muted p-4 rounded-md font-mono text-sm overflow-x-auto text-primary">
            [ {vectorF.avg_affect}, {vectorF.semantic_diversity}, {vectorF.structural_rigor},{" "}
            {vectorF.temporal_density} ]
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
