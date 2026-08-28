import React, { useState } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  CardFooter,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Send,
  Bot,
  Cpu,
  Play,
  Pause,
  RotateCcw,
  Sparkles,
  Database,
  Network,
  Code2,
  ChevronDown,
  ChevronRight,
  Info,
} from "lucide-react";
import { useBank } from "@/lib/bank-context";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  SvtPipelineVisualizer,
  PipelineStageData,
  StageStatus,
} from "@/components/svt-pipeline-visualizer";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  pipelineData?: {
    bootstrap?: any;
    routing?: any;
    response?: any;
    retain_async?: any;
  };
}

interface ScriptScenario {
  id: string;
  title: string;
  description: string;
  prompts: string[];
}

const PRESET_SCENARIOS: ScriptScenario[] = [
  {
    id: "policy-learning",
    title: "Scenario A: Policy & Preference Evolution",
    description:
      "Observes how repeated preferences evolve background observations and graph state.",
    prompts: [
      "Hello, I prefer technical explanations focusing on architectural trade-offs.",
      "Can you remind me of my preferred communication style for new project reviews?",
      "What core principles should we prioritize when designing graph memory structures?",
    ],
  },
  {
    id: "orchestrator-routing",
    title: "Scenario B: Multi-Turn Orchestrator Routing",
    description: "Tests routing choices and context retrieval across consecutive queries.",
    prompts: [
      "Let's analyze the current SVT-CP policy control settings for this bank.",
      "How does the /bootstrap injection affect model system prompts in zero-intervention mode?",
      "Summarize how /retain_async operates without blocking the response.",
    ],
  },
];

export default function ChatSimulatorView() {
  const { currentBank } = useBank();
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [activeStageId, setActiveStageId] = useState<string | null>(null);
  const [selectedTurnId, setSelectedTurnId] = useState<string | null>(null);

  // Scripted execution state
  const [activeScenarioId, setActiveScenarioId] = useState<string>("policy-learning");
  const [isScriptRunning, setIsScriptRunning] = useState(false);
  const [scriptStepIndex, setScriptStepIndex] = useState<number>(0);

  // Pipeline stage tracking state
  const [pipelineStages, setPipelineStages] = useState<PipelineStageData[]>([
    {
      id: "query",
      title: "Query Input",
      subtitle: "User turn submitted",
      icon: "code",
      status: "idle",
    },
    {
      id: "bootstrap",
      title: "/bootstrap",
      subtitle: "Invisible prompt injection",
      icon: "sparkles",
      status: "idle",
    },
    {
      id: "routing",
      title: "Orchestrator Router",
      subtitle: "Dynamic agent policy",
      icon: "network",
      status: "idle",
    },
    {
      id: "response",
      title: "Completion",
      subtitle: "Model execution",
      icon: "cpu",
      status: "idle",
    },
    {
      id: "retain_async",
      title: "/retain_async",
      subtitle: "Graph background evolution",
      icon: "database",
      status: "idle",
    },
  ]);

  const updateStageStatus = (
    id: PipelineStageData["id"],
    status: StageStatus,
    durationMs?: number,
    payload?: any
  ) => {
    setPipelineStages((prev) =>
      prev.map((s) => (s.id === id ? { ...s, status, durationMs, payload } : s))
    );
  };

  const resetStages = () => {
    setPipelineStages([
      {
        id: "query",
        title: "Query Input",
        subtitle: "User turn submitted",
        icon: "code",
        status: "idle",
      },
      {
        id: "bootstrap",
        title: "/bootstrap",
        subtitle: "Invisible prompt injection",
        icon: "sparkles",
        status: "idle",
      },
      {
        id: "routing",
        title: "Orchestrator Router",
        subtitle: "Dynamic agent policy",
        icon: "network",
        status: "idle",
      },
      {
        id: "response",
        title: "Completion",
        subtitle: "Model execution",
        icon: "cpu",
        status: "idle",
      },
      {
        id: "retain_async",
        title: "/retain_async",
        subtitle: "Graph background evolution",
        icon: "database",
        status: "idle",
      },
    ]);
  };

  const executePipeline = async (userText: string) => {
    if (!userText.trim() || !currentBank) return;

    setIsLoading(true);
    resetStages();

    // Stage 1: Query Input
    setActiveStageId("query");
    updateStageStatus("query", "running");
    await new Promise((r) => setTimeout(r, 100));
    updateStageStatus("query", "completed", 12, { query: userText, bank_id: currentBank });

    const userMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      content: userText,
      timestamp: new Date().toLocaleTimeString(),
    };

    setMessages((prev) => [...prev, userMsg]);

    // Stage 2: /bootstrap Injection
    setActiveStageId("bootstrap");
    updateStageStatus("bootstrap", "running");

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: [...messages, userMsg],
          bankId: currentBank,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error || "Failed to execute pipeline");
      }

      const { pipeline, content } = data;

      // Update Bootstrap Stage
      updateStageStatus(
        "bootstrap",
        "completed",
        pipeline?.bootstrap?.durationMs || 120,
        pipeline?.bootstrap
      );

      // Stage 3: Orchestrator Routing
      setActiveStageId("routing");
      updateStageStatus("routing", "running");
      await new Promise((r) => setTimeout(r, 200));
      updateStageStatus(
        "routing",
        "completed",
        pipeline?.routing?.durationMs || 45,
        pipeline?.routing
      );

      // Stage 4: Model Response Execution
      setActiveStageId("response");
      updateStageStatus("response", "running");
      await new Promise((r) => setTimeout(r, 300));
      updateStageStatus(
        "response",
        "completed",
        pipeline?.response?.durationMs || 320,
        pipeline?.response
      );

      const assistantMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: content || "Response generated.",
        timestamp: new Date().toLocaleTimeString(),
        pipelineData: pipeline,
      };

      setMessages((prev) => [...prev, assistantMsg]);
      setSelectedTurnId(assistantMsg.id);

      // Stage 5: /retain_async Background Graph Evolution
      setActiveStageId("retain_async");
      updateStageStatus("retain_async", "running");
      await new Promise((r) => setTimeout(r, 250));
      updateStageStatus(
        "retain_async",
        "completed",
        pipeline?.retain_async?.durationMs || 150,
        pipeline?.retain_async
      );

      setActiveStageId(null);
    } catch (err: any) {
      console.error(err);
      if (activeStageId) {
        updateStageStatus(activeStageId as PipelineStageData["id"], "failed", 0, {
          error: err.message,
        });
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleManualSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (input.trim() && !isLoading) {
      const text = input;
      setInput("");
      executePipeline(text);
    }
  };

  const handleRunScript = async () => {
    const scenario = PRESET_SCENARIOS.find((s) => s.id === activeScenarioId);
    if (!scenario || isScriptRunning) return;

    setIsScriptRunning(true);
    for (let i = 0; i < scenario.prompts.length; i++) {
      setScriptStepIndex(i);
      await executePipeline(scenario.prompts[i]);
      // Small delay between automated script turns
      await new Promise((r) => setTimeout(r, 1000));
    }
    setIsScriptRunning(false);
  };

  const handleClearHistory = () => {
    setMessages([]);
    resetStages();
    setSelectedTurnId(null);
  };

  const selectedTurn =
    messages.find((m) => m.id === selectedTurnId) || messages[messages.length - 1];

  return (
    <div className="space-y-4">
      {/* Top Banner & SVT-CP Pipeline Visualizer */}
      <div className="flex flex-col gap-2">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-foreground flex items-center gap-2">
              <Bot className="w-6 h-6 text-primary" />
              Zero-Intervention Chat Simulator
            </h1>
            <p className="text-xs text-muted-foreground">
              Simulate SVT-CP zero-intervention turns, monitor /bootstrap injections, watch
              orchestrator routing, and observe /retain_async background evolution.
            </p>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={handleClearHistory}
            disabled={isLoading || isScriptRunning}
          >
            <RotateCcw className="w-3.5 h-3.5 mr-1.5" />
            Clear
          </Button>
        </div>

        {/* Live SVT-CP Pipeline Visualizer */}
        <SvtPipelineVisualizer stages={pipelineStages} activeStageId={activeStageId} />
      </div>

      {/* Main Grid: Multi-turn Scenario Controls, Chat Panel, X-Ray Payload Inspector */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 h-[calc(100vh-20rem)] min-h-[500px]">
        {/* Left Column: Scripted Multi-turn Runs */}
        <Card className="lg:col-span-3 flex flex-col border-border/60">
          <CardHeader className="p-3 border-b border-border/50 bg-muted/20">
            <CardTitle className="text-xs font-semibold flex items-center gap-1.5">
              <Play className="w-3.5 h-3.5 text-emerald-500" />
              Automated Multi-Turn Scenarios
            </CardTitle>
          </CardHeader>
          <CardContent className="p-3 flex-1 flex flex-col gap-3 overflow-y-auto">
            <div className="space-y-2">
              <label className="text-[11px] font-medium text-muted-foreground">
                Select Preset Scenario
              </label>
              <div className="space-y-1.5">
                {PRESET_SCENARIOS.map((scen) => (
                  <button
                    key={scen.id}
                    onClick={() => setActiveScenarioId(scen.id)}
                    disabled={isScriptRunning || isLoading}
                    className={`w-full text-left p-2 rounded-md border text-xs transition-all ${
                      activeScenarioId === scen.id
                        ? "border-primary bg-primary/10 font-medium"
                        : "border-border/60 bg-muted/10 hover:bg-muted/30"
                    }`}
                  >
                    <div className="font-semibold">{scen.title}</div>
                    <p className="text-[10px] text-muted-foreground line-clamp-2 mt-0.5">
                      {scen.description}
                    </p>
                  </button>
                ))}
              </div>
            </div>

            <div className="mt-auto pt-2 border-t border-border/40">
              <Button
                className="w-full text-xs h-8"
                onClick={handleRunScript}
                disabled={isScriptRunning || isLoading || !currentBank}
              >
                {isScriptRunning ? (
                  <>
                    <Pause className="w-3.5 h-3.5 mr-1.5 animate-spin" />
                    Executing Turn {scriptStepIndex + 1}...
                  </>
                ) : (
                  <>
                    <Play className="w-3.5 h-3.5 mr-1.5" />
                    Run Automated Simulation
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Center Column: Zero-Intervention Interactive Chat */}
        <Card className="lg:col-span-5 flex flex-col border-border/60">
          <CardHeader className="p-3 border-b border-border/50 bg-muted/20 flex flex-row items-center justify-between">
            <CardTitle className="text-xs font-semibold flex items-center gap-1.5">
              <Bot className="w-3.5 h-3.5 text-primary" />
              Interactive Chat Stream
            </CardTitle>
            <span className="text-[10px] font-mono text-muted-foreground">Bank: {currentBank}</span>
          </CardHeader>

          <CardContent className="flex-1 p-3 overflow-hidden relative">
            <ScrollArea className="h-full pr-2">
              {messages.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full pt-16 text-muted-foreground/60 text-center">
                  <Bot className="w-10 h-10 mb-2 opacity-40" />
                  <p className="text-xs font-medium">Ready for Zero-Intervention Chat</p>
                  <p className="text-[11px] max-w-xs mt-1">
                    Send a prompt or execute an automated multi-turn scenario to observe real-time
                    SVT-CP pipeline stages.
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {messages.map((m) => (
                    <div
                      key={m.id}
                      onClick={() => setSelectedTurnId(m.id)}
                      className={`flex gap-2 cursor-pointer transition-all ${
                        m.role === "user" ? "justify-end" : "justify-start"
                      }`}
                    >
                      {m.role !== "user" && (
                        <div className="w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center shrink-0 mt-0.5">
                          <Cpu className="w-3.5 h-3.5 text-primary" />
                        </div>
                      )}
                      <div
                        className={`rounded-lg px-3 py-2 text-xs max-w-[85%] border transition-all ${
                          m.role === "user"
                            ? "bg-primary text-primary-foreground border-primary"
                            : selectedTurnId === m.id
                              ? "bg-muted border-primary/50 ring-1 ring-primary/20"
                              : "bg-muted/40 border-border/50 hover:border-border"
                        }`}
                      >
                        <p className="whitespace-pre-wrap">{m.content}</p>
                        <div className="mt-1 text-[9px] opacity-60 text-right font-mono">
                          {m.timestamp}
                        </div>
                      </div>
                    </div>
                  ))}
                  {isLoading && (
                    <div className="flex gap-2 justify-start">
                      <div className="w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                        <Cpu className="w-3.5 h-3.5 text-primary animate-pulse" />
                      </div>
                      <div className="rounded-lg px-3 py-2 bg-muted/40 border border-border/50 text-xs flex items-center gap-1">
                        <span className="text-muted-foreground text-[11px]">
                          SVT-CP Pipeline processing...
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </ScrollArea>
          </CardContent>

          <CardFooter className="p-2 border-t border-border/50 bg-muted/10">
            <form onSubmit={handleManualSubmit} className="w-full flex gap-1.5">
              <Input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Type a message to test Orchestrator routing & /bootstrap..."
                className="text-xs h-8 flex-1"
                disabled={isLoading || isScriptRunning}
              />
              <Button
                type="submit"
                size="sm"
                className="h-8 px-3"
                disabled={isLoading || isScriptRunning || !input.trim()}
              >
                <Send className="w-3.5 h-3.5" />
              </Button>
            </form>
          </CardFooter>
        </Card>

        {/* Right Column: Stage & Payload Inspector */}
        <Card className="lg:col-span-4 flex flex-col border-border/60">
          <CardHeader className="p-3 border-b border-border/50 bg-muted/20">
            <CardTitle className="text-xs font-semibold flex items-center gap-1.5">
              <Info className="w-3.5 h-3.5 text-amber-500" />
              X-Ray Stage Inspector
            </CardTitle>
          </CardHeader>
          <CardContent className="p-3 flex-1 overflow-y-auto space-y-3">
            {selectedTurn?.pipelineData ? (
              <div className="space-y-3 font-mono text-[11px]">
                {/* Bootstrap Payload */}
                <div className="p-2.5 rounded-md border border-amber-500/30 bg-amber-500/5">
                  <div className="flex items-center gap-1.5 text-amber-500 font-bold mb-1">
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>[BOOTSTRAP INJECTION]</span>
                  </div>
                  <div className="text-[10px] text-muted-foreground mb-1">
                    Duration: {selectedTurn.pipelineData.bootstrap?.durationMs || 0}ms
                  </div>
                  <pre className="bg-background/80 p-2 rounded border border-border/50 text-[10px] overflow-x-auto max-h-28 whitespace-pre-wrap">
                    {JSON.stringify(selectedTurn.pipelineData.bootstrap?.payload || {}, null, 2)}
                  </pre>
                </div>

                {/* Routing Payload */}
                <div className="p-2.5 rounded-md border border-blue-500/30 bg-blue-500/5">
                  <div className="flex items-center gap-1.5 text-blue-400 font-bold mb-1">
                    <Network className="w-3.5 h-3.5" />
                    <span>[ROUTING DECISION]</span>
                  </div>
                  <pre className="bg-background/80 p-2 rounded border border-border/50 text-[10px] overflow-x-auto max-h-24 whitespace-pre-wrap">
                    {JSON.stringify(selectedTurn.pipelineData.routing?.payload || {}, null, 2)}
                  </pre>
                </div>

                {/* Retain Async Payload */}
                <div className="p-2.5 rounded-md border border-emerald-500/30 bg-emerald-500/5">
                  <div className="flex items-center gap-1.5 text-emerald-400 font-bold mb-1">
                    <Database className="w-3.5 h-3.5" />
                    <span>[RETAIN_ASYNC GRAPH EVOLUTION]</span>
                  </div>
                  <pre className="bg-background/80 p-2 rounded border border-border/50 text-[10px] overflow-x-auto max-h-24 whitespace-pre-wrap">
                    {JSON.stringify(selectedTurn.pipelineData.retain_async?.payload || {}, null, 2)}
                  </pre>
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-full text-muted-foreground/50 text-center pt-16">
                <Info className="w-8 h-8 mb-2 opacity-30" />
                <p className="text-xs">No stage payload selected</p>
                <p className="text-[10px] mt-0.5">
                  Click on any message turn to view detailed pipeline stage metadata and payloads.
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
