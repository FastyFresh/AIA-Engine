import { useState, useEffect, useRef, useCallback } from "react";
import {
  Activity,
  Terminal,
  Cpu,
  Image as ImageIcon,
  Share2,
  BarChart3,
  Play,
  CheckCircle2,
  AlertCircle,
  Loader2,
  User,
  Zap,
  Layers,
  Settings,
  Server
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { useToast } from "@/hooks/use-toast";
import { GalleryTab, INFLUENCERS, LogEntryType } from "@/components/gallery";
import { ManualQueueTab } from "@/components/queue";
import { LoopsTab } from "@/components/loops";
import { CTATab } from "@/components/cta";
import { CalendarTab } from "@/components/calendar/CalendarTab";
import { LoRATab } from "@/components/lora";
import { CurationTab } from "@/components/CurationTab";
import { ResearchTab } from "@/components/research";

import {
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area
} from "recharts";

type AgentStatus = "idle" | "running" | "success" | "error";

interface LogEntry {
  id: string;
  timestamp: string;
  agent: string;
  message: string;
  type: LogEntryType;
}

interface AgentState {
  id: string;
  name: string;
  role: string;
  status: AgentStatus;
  currentTask?: string;
}

const StatusBadge = ({ status }: { status: AgentStatus }) => {
  switch (status) {
    case "running":
      return <Badge variant="outline" className="bg-yellow-500/10 text-yellow-500 border-yellow-500/20 animate-pulse"><Loader2 className="w-3 h-3 mr-1 animate-spin" /> Processing</Badge>;
    case "success":
      return <Badge variant="outline" className="bg-green-500/10 text-green-500 border-green-500/20"><CheckCircle2 className="w-3 h-3 mr-1" /> Ready</Badge>;
    case "error":
      return <Badge variant="outline" className="bg-red-500/10 text-red-500 border-red-500/20"><AlertCircle className="w-3 h-3 mr-1" /> Error</Badge>;
    default:
      return <Badge variant="outline" className="bg-slate-500/10 text-slate-500 border-slate-500/20">Idle</Badge>;
  }
};

const ConsoleLog = ({ logs }: { logs: LogEntry[] }) => {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  return (
    <div className="font-mono text-xs h-full bg-black/40 p-4 rounded-md border border-white/5 overflow-hidden flex flex-col">
      <div className="flex items-center gap-2 text-muted-foreground mb-2 pb-2 border-b border-white/5">
        <Terminal className="w-3 h-3" />
        <span>ORCHESTRATOR_LOGS</span>
      </div>
      <div ref={scrollRef} className="overflow-y-auto flex-1 space-y-1 pr-2">
        {logs.length === 0 && <span className="text-muted-foreground/50">System ready. Waiting for command...</span>}
        {logs.map((log) => (
          <div key={log.id} className="flex gap-3 animate-in fade-in slide-in-from-left-1 duration-200">
            <span className="text-muted-foreground opacity-50 w-16 shrink-0">{log.timestamp}</span>
            <span className={`font-bold w-24 shrink-0 ${
              log.agent === "ORCHESTRATOR" ? "text-primary" :
              log.agent === "CONTENT" ? "text-pink-400" :
              log.agent === "POSTING" ? "text-blue-400" :
              log.agent === "ANALYTICS" ? "text-green-400" :
              log.agent === "GALLERY" ? "text-cyan-400" :
              log.agent === "QUALITY" ? "text-purple-400" : "text-gray-400"
            }`}>[{log.agent}]</span>
            <span className={`${
              log.type === "error" ? "text-red-400" :
              log.type === "success" ? "text-green-400" :
              log.type === "warning" ? "text-yellow-400" :
              "text-gray-300"
            }`}>{log.message}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

const MetricCard = ({ label, value, trend, icon: Icon, color }: any) => (
  <Card className="glass-panel border-l-4" style={{ borderLeftColor: color }}>
    <CardContent className="p-4">
      <div className="flex justify-between items-start">
        <div>
          <p className="text-xs text-muted-foreground font-medium uppercase tracking-wider">{label}</p>
          <h3 className="text-2xl font-bold mt-1">{value}</h3>
        </div>
        <div className={`p-2 rounded-full bg-white/5 ${color.replace('border-', 'text-')}`}>
          <Icon className="w-4 h-4" />
        </div>
      </div>
      <div className="mt-2 text-xs flex items-center gap-1">
        <span className="text-green-400 font-bold">{trend}</span>
        <span className="text-muted-foreground">vs yesterday</span>
      </div>
    </CardContent>
  </Card>
);

const AnalyticsChart = () => {
  const data = [
    { time: "00:00", engagement: 120, reach: 450 },
    { time: "04:00", engagement: 80, reach: 320 },
    { time: "08:00", engagement: 250, reach: 980 },
    { time: "12:00", engagement: 890, reach: 2400 },
    { time: "16:00", engagement: 640, reach: 1800 },
    { time: "20:00", engagement: 1100, reach: 3200 },
    { time: "23:59", engagement: 560, reach: 1500 },
  ];

  return (
    <div className="h-[300px] w-full mt-4">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data}>
          <defs>
            <linearGradient id="colorReach" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="hsl(262 83% 58%)" stopOpacity={0.3}/>
              <stop offset="95%" stopColor="hsl(262 83% 58%)" stopOpacity={0}/>
            </linearGradient>
            <linearGradient id="colorEng" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="hsl(199 89% 48%)" stopOpacity={0.3}/>
              <stop offset="95%" stopColor="hsl(199 89% 48%)" stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
          <XAxis dataKey="time" stroke="#666" fontSize={12} tickLine={false} axisLine={false} />
          <YAxis stroke="#666" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(value) => `${value}`} />
          <Tooltip
            contentStyle={{ backgroundColor: 'rgba(17, 24, 39, 0.9)', borderColor: 'rgba(255,255,255,0.1)', borderRadius: '8px' }}
            itemStyle={{ color: '#fff' }}
          />
          <Area type="monotone" dataKey="reach" stroke="hsl(262 83% 58%)" fillOpacity={1} fill="url(#colorReach)" strokeWidth={2} />
          <Area type="monotone" dataKey="engagement" stroke="hsl(199 89% 48%)" fillOpacity={1} fill="url(#colorEng)" strokeWidth={2} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};

const ConnectionDialog = ({ 
  isOpen, 
  setIsOpen, 
  backendUrl, 
  setBackendUrl, 
  useLiveMode, 
  setUseLiveMode 
}: any) => {
  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogContent className="glass-panel border-white/10 text-foreground sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Server className="w-5 h-5 text-primary" />
            Core Connection
          </DialogTitle>
          <DialogDescription className="text-muted-foreground">
            Connect this dashboard to your AIA Engine Core (Python/FastAPI) instance.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-6 py-4">
          <div className="flex items-center justify-between space-x-2">
            <Label htmlFor="live-mode" className="flex flex-col space-y-1">
              <span>Live Mode</span>
              <span className="font-normal text-xs text-muted-foreground">Use external backend API</span>
            </Label>
            <Switch id="live-mode" checked={useLiveMode} onCheckedChange={setUseLiveMode} />
          </div>
          
          {useLiveMode && (
            <div className="grid gap-2 animate-in fade-in slide-in-from-top-2">
              <Label htmlFor="url">Backend URL</Label>
              <Input
                id="url"
                placeholder="https://your-repl-url.replit.app"
                value={backendUrl}
                onChange={(e) => setBackendUrl(e.target.value)}
                className="bg-black/20 border-white/10"
              />
              <p className="text-[10px] text-muted-foreground">
                Leave empty to use same-origin (default). Only set if connecting to external backend.
              </p>
            </div>
          )}
        </div>
        <DialogFooter>
          <Button onClick={() => setIsOpen(false)}>Save Settings</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default function Dashboard() {
  const { toast } = useToast();
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [progress, setProgress] = useState(0);

  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [backendUrl, setBackendUrl] = useState("");
  const [useLiveMode, setUseLiveMode] = useState(false);

  const [agents, setAgents] = useState<Record<string, AgentState>>({
    content: { id: "content", name: "Content Agent", role: "Generator", status: "idle" },
    editing: { id: "editing", name: "Editing Agent", role: "Processor", status: "idle" },
    posting: { id: "posting", name: "Posting Agent", role: "Scheduler", status: "idle" },
    dfans: { id: "dfans", name: "DFans Agent", role: "Funnel", status: "idle" },
    analytics: { id: "analytics", name: "Analytics Agent", role: "Analyst", status: "idle" },
  });

  const addLog = useCallback((agent: string, message: string, type: LogEntryType = "info") => {
    const now = new Date();
    const timeString = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`;
    setLogs(prev => [...prev, {
      id: Math.random().toString(36).substr(2, 9),
      timestamp: timeString,
      agent,
      message,
      type
    }]);
  }, []);

  const updateAgent = (id: string, updates: Partial<AgentState>) => {
    setAgents(prev => ({
      ...prev,
      [id]: { ...prev[id], ...updates }
    }));
  };

  const getApiBase = () => {
    if (backendUrl) return backendUrl.replace(/\/$/, "");
    return window.location.origin;
  };

  const runLiveCycle = async () => {
    try {
      addLog("ORCHESTRATOR", `Connecting to Core at ${getApiBase()}...`, "info");
      const response = await fetch(`${getApiBase()}/daily_cycle`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });

      if (!response.ok) throw new Error(`API Error: ${response.statusText}`);

      const result = await response.json();
      addLog("ORCHESTRATOR", "Received response from Core", "success");
      addLog("ORCHESTRATOR", JSON.stringify(result, null, 2), "info");
      setProgress(100);
      
    } catch (error: any) {
      addLog("ORCHESTRATOR", `Connection Failed: ${error.message}`, "error");
      toast({
        title: "Connection Failed",
        description: "Could not connect to the backend. Check URL and CORS settings.",
        variant: "destructive",
      });
    } finally {
      setIsRunning(false);
    }
  };

  const runSimulationCycle = async () => {
    Object.keys(agents).forEach(key => updateAgent(key, { status: "idle", currentTask: undefined }));

    addLog("ORCHESTRATOR", "Initializing Daily Cycle (SIMULATION MODE)...", "info");
    await new Promise(r => setTimeout(r, 800));

    updateAgent("content", { status: "running", currentTask: "Generating concepts..." });
    addLog("CONTENT", "Fetching trending topics from sources...", "info");
    await new Promise(r => setTimeout(r, 1500));
    
    addLog("CONTENT", "Generated 4 concepts for Luna Vale", "success");
    addLog("CONTENT", "Generated 4 concepts for Starbright Monroe", "success");
    setProgress(25);
    updateAgent("content", { status: "success", currentTask: "8 concepts created" });

    updateAgent("editing", { status: "running", currentTask: "Processing assets..." });
    addLog("ORCHESTRATOR", "Handing off to Editing Agent...", "info");
    await new Promise(r => setTimeout(r, 1200));
    
    addLog("EDITING", "Applied 'Cinematic' preset to Luna assets", "info");
    addLog("EDITING", "Applied 'Soft Glow' preset to Starbright assets", "info");
    setProgress(50);
    updateAgent("editing", { status: "success", currentTask: "Assets optimized" });

    updateAgent("posting", { status: "running", currentTask: "Scheduling posts..." });
    addLog("POSTING", "Connecting to Metricool API (Stub)...", "warning");
    await new Promise(r => setTimeout(r, 1000));
    
    addLog("POSTING", "Scheduled 2 posts for 18:00 UTC", "success");
    addLog("POSTING", "Scheduled 2 posts for 21:00 UTC", "success");
    setProgress(75);
    updateAgent("posting", { status: "success", currentTask: "Schedule confirmed" });

    updateAgent("dfans", { status: "running", currentTask: "Drafting DMs..." });
    addLog("DFANS", "Analyzing subscriber engagement...", "info");
    await new Promise(r => setTimeout(r, 800));
    addLog("DFANS", "Drafted 2 broadcast messages", "success");
    updateAgent("dfans", { status: "success", currentTask: "Funnel active" });

    updateAgent("analytics", { status: "running", currentTask: "Compiling report..." });
    await new Promise(r => setTimeout(r, 1000));
    addLog("ANALYTICS", "Daily report generated. Reach +12%", "success");
    updateAgent("analytics", { status: "success", currentTask: "Report ready" });
    
    setProgress(100);
    addLog("ORCHESTRATOR", "Daily Cycle Completed Successfully.", "success");
    setIsRunning(false);
  };

  const handleRunCycle = () => {
    if (isRunning) return;
    setIsRunning(true);
    setLogs([]);
    setProgress(0);

    if (useLiveMode) {
      runLiveCycle();
    } else {
      runSimulationCycle();
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col font-sans selection:bg-primary/30">
      <ConnectionDialog 
        isOpen={isSettingsOpen} 
        setIsOpen={setIsSettingsOpen} 
        backendUrl={backendUrl} 
        setBackendUrl={setBackendUrl}
        useLiveMode={useLiveMode}
        setUseLiveMode={setUseLiveMode}
      />

      <header className="border-b border-white/5 bg-card/50 backdrop-blur-md sticky top-0 z-10">
        <div className="container mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center border border-primary/20">
              <Zap className="w-6 h-6 text-primary" />
            </div>
            <div>
              <h1 className="font-bold tracking-tight text-lg">AIA ENGINE <span className="text-primary text-xs align-top">v1</span></h1>
              <p className="text-xs text-muted-foreground font-mono">ORCHESTRATOR // REPLIT_HUB</p>
            </div>
          </div>
          
          <div className="flex items-center gap-4">
            <Button 
              variant="ghost" 
              size="icon" 
              onClick={() => setIsSettingsOpen(true)}
              className="text-muted-foreground hover:text-white hover:bg-white/5"
            >
              <Settings className={`w-5 h-5 ${useLiveMode ? 'text-green-400' : ''}`} />
            </Button>

            <div className={`flex items-center gap-2 px-3 py-1 rounded-full border text-xs font-mono transition-colors ${
              useLiveMode 
                ? "bg-green-500/10 border-green-500/20 text-green-500" 
                : "bg-white/5 border-white/5 text-muted-foreground"
            }`}>
              <div className={`w-2 h-2 rounded-full ${
                isRunning ? "bg-yellow-500 animate-pulse" : useLiveMode ? "bg-green-500" : "bg-slate-500"
              }`} />
              {useLiveMode ? "LIVE_LINK_ACTIVE" : "SIMULATION_MODE"}
            </div>

            <Button 
              size="sm" 
              onClick={handleRunCycle} 
              disabled={isRunning}
              className={`font-mono transition-all ${isRunning ? 'opacity-80' : 'hover:shadow-[0_0_20px_rgba(124,58,237,0.3)]'}`}
            >
              {isRunning ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Play className="w-4 h-4 mr-2" />}
              RUN_DAILY_CYCLE
            </Button>
          </div>
        </div>
      </header>

      <main className="flex-1 container mx-auto px-6 py-8 flex flex-col gap-8">
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard label="Total Reach" value="1.2M" trend="+12%" icon={Activity} color="border-purple-500" />
          <MetricCard label="Engagement Rate" value="4.8%" trend="+0.5%" icon={BarChart3} color="border-cyan-500" />
          <MetricCard label="Content Assets" value="842" trend="+24" icon={Layers} color="border-pink-500" />
          <MetricCard label="DFans Revenue" value="$12.4k" trend="+8%" icon={Share2} color="border-green-500" />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 flex-1 min-h-[600px]">
          
          <div className="space-y-6 flex flex-col">
            <Card className="glass-panel flex-1 flex flex-col">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-mono uppercase text-muted-foreground flex items-center gap-2">
                  <Cpu className="w-4 h-4" /> Active Agents
                </CardTitle>
              </CardHeader>
              <CardContent className="flex-1 flex flex-col gap-3">
                {Object.values(agents).map((agent) => (
                  <div key={agent.id} className="flex items-center justify-between p-3 rounded-lg bg-white/5 border border-white/5 hover:bg-white/10 transition-colors">
                    <div className="flex items-center gap-3">
                      <div className={`p-2 rounded-md ${
                        agent.status === 'running' ? 'bg-primary/20 text-primary' : 'bg-slate-800 text-slate-400'
                      }`}>
                        {agent.id === 'content' ? <ImageIcon className="w-4 h-4" /> :
                         agent.id === 'editing' ? <Layers className="w-4 h-4" /> :
                         agent.id === 'posting' ? <Share2 className="w-4 h-4" /> :
                         agent.id === 'dfans' ? <User className="w-4 h-4" /> :
                         <BarChart3 className="w-4 h-4" />}
                      </div>
                      <div>
                        <div className="font-medium text-sm">{agent.name}</div>
                        <div className="text-xs text-muted-foreground">{agent.currentTask || agent.role}</div>
                      </div>
                    </div>
                    <StatusBadge status={agent.status} />
                  </div>
                ))}
              </CardContent>
            </Card>
            
            <Card className="glass-panel">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-mono uppercase text-muted-foreground">Influencer Profiles</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {INFLUENCERS.map(inf => (
                  <div key={inf.id} className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-2">
                      <div className={`w-2 h-2 rounded-full bg-current ${inf.color}`} />
                      <span className="font-medium">{inf.name}</span>
                    </div>
                    <span className="text-muted-foreground text-xs">{inf.niche}</span>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>

          <div className="lg:col-span-2 flex flex-col gap-6">
            <Tabs defaultValue="logs" className="flex-1 flex flex-col">
              <div className="flex flex-col gap-2 mb-2">
                <div className="flex items-center justify-between gap-2">
                  <TabsList className="bg-black/40 border border-white/5">
                    <TabsTrigger value="logs" className="text-xs font-mono">LOGS</TabsTrigger>
                    <TabsTrigger value="analytics" className="text-xs font-mono">ANALYTICS</TabsTrigger>
                    <TabsTrigger value="content" className="text-xs font-mono">GALLERY</TabsTrigger>
                    <TabsTrigger value="loops" className="text-xs font-mono">LOOPS</TabsTrigger>
                    <TabsTrigger value="cta" className="text-xs font-mono">CTA</TabsTrigger>
                    <TabsTrigger value="calendar" className="text-xs font-mono">CALENDAR</TabsTrigger>
                  </TabsList>
                  {isRunning && (
                    <div className="flex items-center gap-2 w-48">
                      <span className="text-xs font-mono text-muted-foreground">PROGRESS</span>
                      <Progress value={progress} className="h-1" />
                    </div>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <TabsList className="bg-black/40 border border-white/5 w-fit">
                    <TabsTrigger value="lora" className="text-xs font-mono">LORA</TabsTrigger>
                    <TabsTrigger value="curation" className="text-xs font-mono">CURATION</TabsTrigger>
                    <TabsTrigger value="queue" className="text-xs font-mono">QUEUE</TabsTrigger>
                    <TabsTrigger value="research" className="text-xs font-mono">RESEARCH</TabsTrigger>
                  </TabsList>
                  <a href="/dashboard/content" className="inline-flex items-center justify-center rounded-md px-3 py-1.5 text-xs font-mono bg-pink-500/20 text-pink-400 border border-pink-500/30 hover:bg-pink-500/30 transition-colors">
                    TELEGRAM CONTENT
                  </a>
                  <a href="/upload" className="inline-flex items-center justify-center rounded-md px-3 py-1.5 text-xs font-mono bg-green-500/20 text-green-400 border border-green-500/30 hover:bg-green-500/30 transition-colors">
                    UPLOAD
                  </a>
                </div>
              </div>

              <TabsContent value="logs" className="flex-1 mt-0 min-h-0">
                <ConsoleLog logs={logs} />
              </TabsContent>

              <TabsContent value="analytics" className="flex-1 mt-0 min-h-0 glass-panel p-6 rounded-lg border border-white/5">
                <div className="flex items-center justify-between">
                   <h3 className="font-bold text-lg">Performance Overview (24h)</h3>
                   <Badge variant="secondary">Live Data</Badge>
                </div>
                <AnalyticsChart />
              </TabsContent>
              
              <TabsContent value="content" className="flex-1 mt-0 min-h-0 glass-panel p-4 rounded-lg border border-white/5 overflow-hidden">
                <GalleryTab 
                  backendUrl={backendUrl} 
                  useLiveMode={useLiveMode}
                  addLog={addLog}
                />
              </TabsContent>
              
              <TabsContent value="loops" className="flex-1 mt-0 min-h-0 glass-panel p-4 rounded-lg border border-white/5 overflow-hidden">
                <LoopsTab 
                  backendUrl={backendUrl} 
                  useLiveMode={useLiveMode}
                  addLog={addLog}
                />
              </TabsContent>
              
              <TabsContent value="cta" className="flex-1 mt-0 min-h-0 glass-panel p-4 rounded-lg border border-white/5 overflow-hidden">
                <CTATab 
                  backendUrl={backendUrl} 
                  addLog={addLog}
                />
              </TabsContent>
              
              <TabsContent value="calendar" className="flex-1 mt-0 min-h-0 glass-panel p-4 rounded-lg border border-white/5 overflow-auto">
                <CalendarTab />
              </TabsContent>
              
              <TabsContent value="lora" className="flex-1 mt-0 min-h-0 glass-panel p-4 rounded-lg border border-white/5 overflow-auto">
                <LoRATab 
                  backendUrl={backendUrl} 
                  addLog={addLog}
                />
              </TabsContent>
              
              <TabsContent value="curation" className="flex-1 mt-0 min-h-0 glass-panel p-4 rounded-lg border border-white/5 overflow-auto">
                <CurationTab 
                  backendUrl={backendUrl} 
                  addLog={addLog}
                />
              </TabsContent>
              
              <TabsContent value="queue" className="flex-1 mt-0 min-h-0 glass-panel p-4 rounded-lg border border-white/5 overflow-hidden">
                <ManualQueueTab 
                  backendUrl={backendUrl} 
                  useLiveMode={useLiveMode}
                  addLog={addLog}
                />
              </TabsContent>
              
              <TabsContent value="research" className="flex-1 mt-0 min-h-0 glass-panel p-4 rounded-lg border border-white/5 overflow-auto">
                <ResearchTab 
                  backendUrl={backendUrl} 
                  addLog={addLog}
                />
              </TabsContent>
            </Tabs>
          </div>

        </div>
      </main>
    </div>
  );
}
