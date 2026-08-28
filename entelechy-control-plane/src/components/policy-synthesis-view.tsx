import React, { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Atom, MessageSquare, Lightbulb, Puzzle, Scale, Wrench } from "lucide-react";
import { Progress } from "@/components/ui/progress";
import { useBank } from "@/lib/bank-context";
import { client } from "@/lib/api";

export default function PolicySynthesisView() {
  const { currentBank } = useBank();
  const [data, setData] = useState<{
    verbosity: number;
    abstraction: number;
    creativity: number;
    empathy: number;
    rigor: number;
    tool_use_prob: number;
    rationale?: string;
  } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    async function loadStats() {
      if (!currentBank) return;
      setLoading(true);
      try {
        const res = await client.getMwpmcStats(currentBank || "default");
        if (active && res && res.vectorP) {
          setData(res.vectorP);
        }
      } catch (e) {
        console.error("Failed to load MWPMC stats", e);
      } finally {
        if (active) setLoading(false);
      }
    }
    loadStats();
    return () => {
      active = false;
    };
  }, [currentBank]);

  const vectorP = data || {
    verbosity: 0.2,
    abstraction: 0.85,
    creativity: 0.2,
    empathy: 0.1,
    rigor: 0.95,
    tool_use_prob: 0.9,
  };

  return (
    <div className="p-4 space-y-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold mb-2 text-foreground flex items-center gap-2">
            <Atom className="w-8 h-8 text-primary" />
            Policy Synthesis (Stage B)
          </h1>
          <p className="text-muted-foreground">
            Translates feature metrics (Vector F) into operational directives (Policy Vector P) for
            bank: <span className="font-mono text-primary">{currentBank}</span>.
          </p>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card className="col-span-full">
          <CardHeader>
            <CardTitle>Synthesized Policy Vector (P)</CardTitle>
            <CardDescription>
              The current active control vector modulating inference. Values closer to 1 indicate
              stronger enforcement.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="flex items-center gap-2 font-medium">
                  <MessageSquare className="w-4 h-4 text-muted-foreground" />
                  Verbosity
                </span>
                <span className="font-mono">{loading ? "..." : vectorP.verbosity.toFixed(2)}</span>
              </div>
              <Progress value={vectorP.verbosity * 100} className="h-2" />
              <p className="text-xs text-muted-foreground">
                Controls output length. Low values enforce extreme conciseness.
              </p>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="flex items-center gap-2 font-medium">
                  <Lightbulb className="w-4 h-4 text-muted-foreground" />
                  Abstraction
                </span>
                <span className="font-mono">
                  {loading ? "..." : vectorP.abstraction.toFixed(2)}
                </span>
              </div>
              <Progress value={vectorP.abstraction * 100} className="h-2" />
              <p className="text-xs text-muted-foreground">
                Level of conceptual vs literal interpretation.
              </p>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="flex items-center gap-2 font-medium">
                  <Puzzle className="w-4 h-4 text-muted-foreground" />
                  Creativity (Temperature)
                </span>
                <span className="font-mono">{loading ? "..." : vectorP.creativity.toFixed(2)}</span>
              </div>
              <Progress value={vectorP.creativity * 100} className="h-2" />
              <p className="text-xs text-muted-foreground">
                Allows novelty vs enforcing deterministic adherence to protocol.
              </p>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="flex items-center gap-2 font-medium">
                  <Scale className="w-4 h-4 text-muted-foreground" />
                  Rigor
                </span>
                <span className="font-mono">{loading ? "..." : vectorP.rigor.toFixed(2)}</span>
              </div>
              <Progress value={vectorP.rigor * 100} className="h-2" />
              <p className="text-xs text-muted-foreground">
                Strictness of constraint application and rule-following.
              </p>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="flex items-center gap-2 font-medium">
                  <Wrench className="w-4 h-4 text-muted-foreground" />
                  Tool Use Probability
                </span>
                <span className="font-mono">
                  {loading ? "..." : vectorP.tool_use_prob.toFixed(2)}
                </span>
              </div>
              <Progress value={vectorP.tool_use_prob * 100} className="h-2" />
              <p className="text-xs text-muted-foreground">
                Likelihood of delegating to external functions vs internal generation.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Raw Vector P</CardTitle>
          <CardDescription>The synthesized array injected into the agent prompt.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="bg-muted p-4 rounded-md font-mono text-sm overflow-x-auto text-primary">
            [ V:{vectorP.verbosity}, A:{vectorP.abstraction}, C:{vectorP.creativity}, E:
            {vectorP.empathy}, R:{vectorP.rigor}, T:{vectorP.tool_use_prob} ]
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
