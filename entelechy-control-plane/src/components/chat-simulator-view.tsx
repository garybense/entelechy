import React from 'react';
import { useChat } from '@ai-sdk/react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Send, Bot, Cpu } from "lucide-react";
import { useBank } from "@/lib/bank-context";
import { ScrollArea } from "@/components/ui/scroll-area";

export default function ChatSimulatorView() {
  const { currentBank } = useBank();

  const { messages, input, handleInputChange, handleSubmit, isLoading } = useChat({
    api: '/api/chat',
    body: {
      bankId: currentBank
    }
  });

  return (
    <div className="p-4 h-[calc(100vh-8rem)] flex flex-col lg:flex-row gap-6">
      
      {/* Chat Area */}
      <Card className="flex-1 flex flex-col h-full border-primary/20 shadow-md">
        <CardHeader className="border-b bg-muted/30 pb-4">
          <CardTitle className="flex items-center gap-2">
            <Bot className="w-5 h-5 text-primary" />
            Zero-Intervention Orchestrator
          </CardTitle>
          <CardDescription>
            Chatting with bank: <span className="font-mono text-primary">{currentBank}</span> using Vertex AI
          </CardDescription>
        </CardHeader>
        
        <CardContent className="flex-1 p-0 overflow-hidden relative">
          <ScrollArea className="h-full p-4">
            {messages.length === 0 ? (
               <div className="flex flex-col items-center justify-center h-full text-muted-foreground opacity-50 pt-20">
                 <Bot className="w-16 h-16 mb-4" />
                 <p>Waiting for bootstrap...</p>
               </div>
            ) : (
              <div className="space-y-4 pb-4">
                {messages.map((m) => (
                  <div key={m.id} className={`flex gap-3 ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                    {m.role !== 'user' && (
                      <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                        <Cpu className="w-4 h-4 text-primary" />
                      </div>
                    )}
                    <div className={`rounded-xl px-4 py-2 max-w-[80%] ${m.role === 'user' ? 'bg-primary text-primary-foreground' : 'bg-muted'}`}>
                      <p className="text-sm whitespace-pre-wrap">{m.content}</p>
                    </div>
                  </div>
                ))}
                {isLoading && (
                  <div className="flex gap-3 justify-start">
                     <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                        <Cpu className="w-4 h-4 text-primary animate-pulse" />
                      </div>
                      <div className="rounded-xl px-4 py-2 bg-muted flex items-center gap-1">
                        <div className="w-1.5 h-1.5 rounded-full bg-primary/50 animate-bounce"></div>
                        <div className="w-1.5 h-1.5 rounded-full bg-primary/50 animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                        <div className="w-1.5 h-1.5 rounded-full bg-primary/50 animate-bounce" style={{ animationDelay: '0.4s' }}></div>
                      </div>
                  </div>
                )}
              </div>
            )}
          </ScrollArea>
        </CardContent>

        <CardFooter className="p-4 border-t bg-muted/10">
          <form onSubmit={handleSubmit} className="w-full flex gap-2">
            <Input
              value={input}
              onChange={handleInputChange}
              placeholder="Test the agent's policy..."
              className="flex-1"
              disabled={isLoading}
            />
            <Button type="submit" disabled={isLoading || !input || !input.trim()}>
              <Send className="w-4 h-4" />
            </Button>
          </form>
        </CardFooter>
      </Card>

      {/* X-Ray Debug Panel */}
      <div className="w-full lg:w-80 flex flex-col gap-4">
        <Card className="flex-1">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm flex items-center gap-2">
              <Cpu className="w-4 h-4 text-amber-500" />
              Orchestrator Logs
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4 text-xs font-mono text-muted-foreground">
              {messages.length > 0 && (
                <div className="p-2 bg-muted rounded border-l-2 border-primary">
                  <span className="text-primary font-bold block mb-1">[SYSTEM] /bootstrap</span>
                  State Vector extracted.
                  <br/>Policy synthesized.
                  <br/>System prompt injected invisibly.
                </div>
              )}
              {messages.filter(m => m.role === 'assistant').map((m, i) => (
                <div key={`log-${i}`} className="p-2 bg-muted rounded border-l-2 border-green-500">
                  <span className="text-green-500 font-bold block mb-1">[BACKGROUND] /retain</span>
                  Experience logged to {currentBank}.
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

    </div>
  );
}
