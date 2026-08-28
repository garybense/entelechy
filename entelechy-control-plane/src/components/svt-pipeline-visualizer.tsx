import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  CheckCircle2,
  Clock,
  AlertCircle,
  Loader2,
  ArrowRight,
  Code2,
  Cpu,
  Database,
  Network,
  Sparkles,
} from "lucide-react";

export type StageStatus = "idle" | "running" | "completed" | "failed";

export interface PipelineStageData {
  id: "query" | "bootstrap" | "routing" | "response" | "retain_async";
  title: string;
  subtitle: string;
  icon: string;
  status: StageStatus;
  durationMs?: number;
  payload?: any;
}

interface SvtPipelineVisualizerProps {
  stages: PipelineStageData[];
  activeStageId?: string | null;
}

export function SvtPipelineVisualizer({ stages, activeStageId }: SvtPipelineVisualizerProps) {
  const getStatusBadge = (status: StageStatus) => {
    switch (status) {
      case "running":
        return (
          <span className="flex items-center gap-1.5 px-2 py-0.5 text-xs font-medium bg-blue-500/10 text-blue-500 rounded-full border border-blue-500/20">
            <Loader2 className="w-3 h-3 animate-spin" />
            Active
          </span>
        );
      case "completed":
        return (
          <span className="flex items-center gap-1.5 px-2 py-0.5 text-xs font-medium bg-emerald-500/10 text-emerald-500 rounded-full border border-emerald-500/20">
            <CheckCircle2 className="w-3 h-3" />
            Done
          </span>
        );
      case "failed":
        return (
          <span className="flex items-center gap-1.5 px-2 py-0.5 text-xs font-medium bg-red-500/10 text-red-500 rounded-full border border-red-500/20">
            <AlertCircle className="w-3 h-3" />
            Error
          </span>
        );
      default:
        return (
          <span className="flex items-center gap-1.5 px-2 py-0.5 text-xs font-medium bg-muted text-muted-foreground rounded-full border border-border">
            <Clock className="w-3 h-3" />
            Pending
          </span>
        );
    }
  };

  const renderIcon = (id: string) => {
    switch (id) {
      case "query":
        return <Code2 className="w-4 h-4 text-purple-400" />;
      case "bootstrap":
        return <Sparkles className="w-4 h-4 text-amber-400" />;
      case "routing":
        return <Network className="w-4 h-4 text-blue-400" />;
      case "response":
        return <Cpu className="w-4 h-4 text-indigo-400" />;
      case "retain_async":
        return <Database className="w-4 h-4 text-emerald-400" />;
      default:
        return <Cpu className="w-4 h-4 text-primary" />;
    }
  };

  return (
    <Card className="border-border bg-card/60 backdrop-blur">
      <CardHeader className="pb-3 border-b border-border/50">
        <CardTitle className="text-sm font-semibold flex items-center gap-2">
          <Network className="w-4 h-4 text-primary" />
          SVT-CP Execution Pipeline
        </CardTitle>
      </CardHeader>
      <CardContent className="p-4 space-y-3">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
          {stages.map((stage, index) => {
            const isActive = activeStageId === stage.id;
            return (
              <div
                key={stage.id}
                className={`relative rounded-lg p-3 border transition-all flex flex-col justify-between ${
                  isActive
                    ? "border-primary bg-primary/5 shadow-sm ring-1 ring-primary/30"
                    : stage.status === "completed"
                      ? "border-emerald-500/30 bg-emerald-500/5"
                      : stage.status === "failed"
                        ? "border-red-500/30 bg-red-500/5"
                        : "border-border/60 bg-muted/20"
                }`}
              >
                <div>
                  <div className="flex items-center justify-between gap-1 mb-2">
                    <div className="flex items-center gap-1.5 font-medium text-xs">
                      {renderIcon(stage.id)}
                      <span className="truncate">{stage.title}</span>
                    </div>
                    {getStatusBadge(stage.status)}
                  </div>
                  <p className="text-[11px] text-muted-foreground line-clamp-2 mb-2">
                    {stage.subtitle}
                  </p>
                </div>

                <div className="pt-2 border-t border-border/40 flex items-center justify-between text-[10px] text-muted-foreground font-mono">
                  <span>Stage {index + 1}</span>
                  {stage.durationMs !== undefined && <span>{stage.durationMs}ms</span>}
                </div>

                {index < stages.length - 1 && (
                  <div className="hidden md:block absolute -right-2.5 top-1/2 -translate-y-1/2 z-10 text-muted-foreground/40">
                    <ArrowRight className="w-3.5 h-3.5" />
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
