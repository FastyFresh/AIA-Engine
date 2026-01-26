import { useState, useEffect } from "react";
import { 
  Search, 
  Sparkles, 
  Copy, 
  Check, 
  RefreshCw, 
  Instagram,
  Loader2,
  Eye,
  Zap,
  MessageSquare,
  TrendingUp,
  Filter,
  Wand2,
  CheckSquare,
  Square,
  Pencil,
  Lock,
  Unlock
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { useToast } from "@/hooks/use-toast";
import { LogEntryType } from "@/components/gallery/types";

interface ResearchTabProps {
  backendUrl: string;
  addLog: (agent: string, message: string, type?: LogEntryType) => void;
}

interface PromptData {
  id: number;
  category: string;
  prompt: string;
  caption_hook: string;
  engagement_question: string;
  source?: string;
}

interface ResearchStatus {
  apify_configured: boolean;
  xai_configured: boolean;
  prompt_library_exists: boolean;
  prompt_count: number;
}

export function ResearchTab({ backendUrl, addLog }: ResearchTabProps) {
  const [loading, setLoading] = useState(false);
  const [scraping, setScraping] = useState(false);
  const [username, setUsername] = useState("");
  const [prompts, setPrompts] = useState<PromptData[]>([]);
  const [status, setStatus] = useState<ResearchStatus | null>(null);
  const [categoryFilter, setCategoryFilter] = useState<string>("all");
  const [copiedId, setCopiedId] = useState<number | null>(null);
  const [generatingId, setGeneratingId] = useState<number | null>(null);
  const [selectedPrompts, setSelectedPrompts] = useState<Set<number>>(new Set());
  const [batchGenerating, setBatchGenerating] = useState(false);
  const [batchProgress, setBatchProgress] = useState({ current: 0, total: 0 });
  const [editingPrompt, setEditingPrompt] = useState<PromptData | null>(null);
  const [editedText, setEditedText] = useState("");
  const [consistencyMode, setConsistencyMode] = useState(false);
  const [selectedBackground, setSelectedBackground] = useState("luxury_apartment");
  const [selectedInfluencer, setSelectedInfluencer] = useState("starbright_monroe");
  const { toast } = useToast();

  const backgroundOptions = [
    { value: "luxury_apartment", label: "Luxury Apartment" },
    { value: "studio_white", label: "White Studio" },
    { value: "studio_dark", label: "Dark Studio" },
    { value: "bedroom", label: "Bedroom" }
  ];

  const influencerOptions = [
    { value: "starbright_monroe", label: "Starbright Monroe", color: "text-pink-400" },
    { value: "luna_vale", label: "Luna Vale", color: "text-blue-400" }
  ];

  const openEditDialog = (prompt: PromptData) => {
    setEditingPrompt(prompt);
    setEditedText(prompt.prompt);
  };

  const generateEditedPrompt = async () => {
    if (!editingPrompt || !editedText.trim()) return;
    
    setEditingPrompt(null);
    setGeneratingId(editingPrompt.id);
    
    try {
      addLog("RESEARCH", `Generating from edited prompt...`, "info");
      const response = await fetch(`${backendUrl}/api/research/generate-batch`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prompts: [editedText],
          influencer_id: selectedInfluencer,
          consistency_mode: consistencyMode,
          background: selectedBackground
        })
      });
      
      if (response.ok) {
        const result = await response.json();
        addLog("RESEARCH", `Generated image from edited prompt`, "success");
        toast({
          title: "Image Generated",
          description: "Check the Gallery tab for your new image"
        });
      }
    } catch (error) {
      addLog("RESEARCH", `Error: ${error}`, "error");
    } finally {
      setGeneratingId(null);
    }
  };

  const togglePromptSelection = (id: number) => {
    setSelectedPrompts(prev => {
      const newSet = new Set(prev);
      if (newSet.has(id)) {
        newSet.delete(id);
      } else {
        newSet.add(id);
      }
      return newSet;
    });
  };

  const selectAllPrompts = () => {
    if (selectedPrompts.size === prompts.length) {
      setSelectedPrompts(new Set());
    } else {
      setSelectedPrompts(new Set(prompts.map(p => p.id)));
    }
  };

  const generateSelectedBatch = async () => {
    const selected = prompts.filter(p => selectedPrompts.has(p.id));
    if (selected.length === 0) {
      toast({
        title: "No prompts selected",
        description: "Select one or more prompts to generate",
        variant: "destructive"
      });
      return;
    }

    setBatchGenerating(true);
    setBatchProgress({ current: 0, total: selected.length });
    const modeLabel = consistencyMode ? "CONSISTENCY MODE" : "CREATIVE MODE";
    const influencerLabel = influencerOptions.find(i => i.value === selectedInfluencer)?.label;
    addLog("RESEARCH", `Starting batch for ${influencerLabel} (${modeLabel}) - ${selected.length} images...`, "info");
    if (consistencyMode) {
      const bgLabel = backgroundOptions.find(b => b.value === selectedBackground)?.label;
      addLog("RESEARCH", `Background locked to: ${bgLabel}`, "info");
    }

    try {
      const response = await fetch(`${backendUrl}/api/research/generate-batch`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prompts: selected.map(p => p.prompt),
          influencer_id: selectedInfluencer,
          consistency_mode: consistencyMode,
          background: selectedBackground
        })
      });

      const result = await response.json();

      if (result.successful > 0) {
        addLog("RESEARCH", `Batch complete: ${result.successful}/${result.total} images generated`, "success");
        toast({
          title: "Batch Generation Complete",
          description: `${result.successful} of ${result.total} images generated successfully`
        });
      } else {
        addLog("RESEARCH", `Batch failed: ${result.failed} errors`, "error");
        toast({
          title: "Batch Generation Failed",
          description: "No images were generated successfully",
          variant: "destructive"
        });
      }

      setSelectedPrompts(new Set());
    } catch (error) {
      addLog("RESEARCH", `Batch error: ${error}`, "error");
      toast({
        title: "Error",
        description: "Failed to run batch generation",
        variant: "destructive"
      });
    } finally {
      setBatchGenerating(false);
      setBatchProgress({ current: 0, total: 0 });
    }
  };

  useEffect(() => {
    fetchStatus();
    fetchPrompts();
  }, []);

  const fetchStatus = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/research/status`);
      if (response.ok) {
        const data = await response.json();
        setStatus(data);
      }
    } catch (error) {
      console.error("Failed to fetch research status:", error);
    }
  };

  const fetchPrompts = async (category?: string) => {
    try {
      const url = category && category !== "all" 
        ? `${backendUrl}/api/research/prompts?category=${category}`
        : `${backendUrl}/api/research/prompts`;
      const response = await fetch(url);
      if (response.ok) {
        const data = await response.json();
        setPrompts(data.prompts || []);
      }
    } catch (error) {
      console.error("Failed to fetch prompts:", error);
    }
  };

  const analyzeInfluencer = async () => {
    if (!username.trim()) {
      toast({
        title: "Enter Username",
        description: "Please enter an Instagram username to analyze",
        variant: "destructive"
      });
      return;
    }

    setScraping(true);
    addLog("RESEARCH", `Analyzing @${username}...`, "info");

    try {
      const response = await fetch(`${backendUrl}/api/research/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username: username.replace("@", ""),
          persona_name: "Starbright Monroe",
          persona_description: "pale ivory skin, slim athletic figure, dark brown hair, warm olive brown eyes",
          posts_limit: 30,
          num_prompts: 15
        })
      });

      const result = await response.json();

      if (result.success) {
        addLog("RESEARCH", `Generated ${result.prompts?.length || 0} prompts from @${username}`, "success");
        toast({
          title: "Analysis Complete",
          description: `Generated ${result.prompts?.length || 0} prompts from @${username}`
        });
        fetchPrompts();
        fetchStatus();
      } else {
        addLog("RESEARCH", `Error: ${result.error}`, "error");
        toast({
          title: "Analysis Failed",
          description: result.error || "Failed to analyze profile",
          variant: "destructive"
        });
      }
    } catch (error) {
      addLog("RESEARCH", `Error: ${error}`, "error");
      toast({
        title: "Error",
        description: "Failed to analyze influencer",
        variant: "destructive"
      });
    } finally {
      setScraping(false);
    }
  };

  const copyPrompt = async (prompt: PromptData) => {
    await navigator.clipboard.writeText(prompt.prompt);
    setCopiedId(prompt.id);
    setTimeout(() => setCopiedId(null), 2000);
    toast({
      title: "Copied!",
      description: "Prompt copied to clipboard"
    });
  };

  const generateFromPrompt = async (prompt: PromptData) => {
    console.log("Generate clicked for prompt:", prompt.id, prompt.category);
    setGeneratingId(prompt.id);
    addLog("RESEARCH", `Generating image from ${prompt.category} prompt...`, "info");
    
    const url = `${backendUrl}/api/research/generate-from-prompt`;
    console.log("Fetching URL:", url);
    
    try {
      const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prompt: prompt.prompt,
          influencer_id: selectedInfluencer,
          caption_hook: prompt.caption_hook
        })
      });
      
      const result = await response.json();
      
      if (result.success) {
        addLog("RESEARCH", `Image generated: ${result.image_path}`, "success");
        toast({
          title: "Image Generated!",
          description: `Saved to ${result.image_path}`
        });
      } else {
        addLog("RESEARCH", `Generation failed: ${result.error}`, "error");
        toast({
          title: "Generation Failed",
          description: result.error || "Failed to generate image",
          variant: "destructive"
        });
      }
    } catch (error) {
      addLog("RESEARCH", `Error: ${error}`, "error");
      toast({
        title: "Error",
        description: "Failed to generate image",
        variant: "destructive"
      });
    } finally {
      setGeneratingId(null);
    }
  };

  const handleCategoryChange = (value: string) => {
    setCategoryFilter(value);
    setSelectedPrompts(new Set()); // Clear selections when category changes
    fetchPrompts(value);
  };

  const categories = ["all", "intimate", "glamour", "casual", "fitness", "portrait"];

  return (
    <div className="h-full overflow-auto space-y-4">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-lg font-bold flex items-center gap-2">
            <Search className="w-5 h-5 text-primary" />
            Competitor Research
          </h2>
          <p className="text-sm text-muted-foreground">
            Analyze successful AI influencers and generate optimized prompts
          </p>
        </div>
        {status && (
          <div className="flex items-center gap-2">
            <Badge variant={status.apify_configured ? "default" : "destructive"}>
              {status.apify_configured ? "Apify Ready" : "Apify Not Configured"}
            </Badge>
            <Badge variant="secondary">{status.prompt_count} Prompts</Badge>
          </div>
        )}
      </div>

      <Tabs defaultValue="analyze" className="space-y-4">
        <TabsList className="bg-black/40 border border-white/5">
          <TabsTrigger value="analyze" className="text-xs font-mono">
            <Instagram className="w-3 h-3 mr-1" /> ANALYZE
          </TabsTrigger>
          <TabsTrigger value="library" className="text-xs font-mono">
            <Sparkles className="w-3 h-3 mr-1" /> PROMPT LIBRARY
          </TabsTrigger>
          <TabsTrigger value="hooks" className="text-xs font-mono">
            <MessageSquare className="w-3 h-3 mr-1" /> CAPTION HOOKS
          </TabsTrigger>
        </TabsList>

        <TabsContent value="analyze" className="space-y-4">
          <Card className="bg-black/20 border-white/10">
            <CardHeader>
              <CardTitle className="text-sm flex items-center gap-2">
                <Instagram className="w-4 h-4" />
                Analyze Competitor Profile
              </CardTitle>
              <CardDescription>
                Enter an Instagram username to scrape their content and generate prompts
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-2">
                <div className="flex-1">
                  <Label htmlFor="username" className="text-xs text-muted-foreground">
                    Instagram Username
                  </Label>
                  <Input
                    id="username"
                    placeholder="@officegirlchloe"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    className="bg-black/30"
                  />
                </div>
                <div className="flex items-end">
                  <Button 
                    onClick={analyzeInfluencer}
                    disabled={scraping || !status?.apify_configured}
                    className="font-mono"
                  >
                    {scraping ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Analyzing...
                      </>
                    ) : (
                      <>
                        <Search className="w-4 h-4 mr-2" />
                        Analyze
                      </>
                    )}
                  </Button>
                </div>
              </div>

              {!status?.apify_configured && (
                <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-md p-3 text-sm">
                  <p className="text-yellow-400 font-medium">Apify API Key Required</p>
                  <p className="text-muted-foreground text-xs mt-1">
                    Add APIFY_API_TOKEN to your secrets to enable Instagram scraping.
                    Get a free API key at apify.com
                  </p>
                </div>
              )}

              <div className="grid grid-cols-3 gap-3 mt-4">
                <Card className="bg-white/5 border-white/10 p-3">
                  <div className="text-xs text-muted-foreground">Suggested Targets</div>
                  <div className="text-sm font-medium mt-1">@officegirlchloe</div>
                  <div className="text-xs text-green-400">124K followers</div>
                </Card>
                <Card className="bg-white/5 border-white/10 p-3">
                  <div className="text-xs text-muted-foreground">Suggested Targets</div>
                  <div className="text-sm font-medium mt-1">@ia_love2</div>
                  <div className="text-xs text-green-400">60K followers</div>
                </Card>
                <Card className="bg-white/5 border-white/10 p-3">
                  <div className="text-xs text-muted-foreground">Suggested Targets</div>
                  <div className="text-sm font-medium mt-1">@emilypellegrini</div>
                  <div className="text-xs text-green-400">$23K/month</div>
                </Card>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="library" className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4 text-muted-foreground" />
              <Select value={categoryFilter} onValueChange={handleCategoryChange}>
                <SelectTrigger className="w-32 bg-black/30">
                  <SelectValue placeholder="Category" />
                </SelectTrigger>
                <SelectContent>
                  {categories.map(cat => (
                    <SelectItem key={cat} value={cat}>
                      {cat.charAt(0).toUpperCase() + cat.slice(1)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Button
                variant="ghost"
                size="sm"
                onClick={selectAllPrompts}
                className="text-xs"
              >
                {selectedPrompts.size === prompts.length && prompts.length > 0 ? (
                  <><CheckSquare className="w-3 h-3 mr-1" /> Deselect All</>
                ) : (
                  <><Square className="w-3 h-3 mr-1" /> Select All</>
                )}
              </Button>
            </div>
            <div className="flex items-center gap-2">
              {selectedPrompts.size > 0 && (
                <Button
                  size="sm"
                  onClick={generateSelectedBatch}
                  disabled={batchGenerating}
                  className="bg-primary hover:bg-primary/90"
                >
                  {batchGenerating ? (
                    <>
                      <Loader2 className="w-3 h-3 mr-1 animate-spin" />
                      Generating...
                    </>
                  ) : (
                    <>
                      <Wand2 className="w-3 h-3 mr-1" />
                      Generate {selectedPrompts.size} Selected
                    </>
                  )}
                </Button>
              )}
              <Button 
                variant="outline" 
                size="sm" 
                onClick={() => fetchPrompts(categoryFilter)}
              >
                <RefreshCw className="w-3 h-3 mr-1" />
                Refresh
              </Button>
            </div>
          </div>

          {/* Generation Controls */}
          <Card className="border bg-black/20 border-white/10">
            <CardContent className="p-3 space-y-3">
              {/* Influencer Selector */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Label className="text-sm font-medium">Generate for:</Label>
                  <Select value={selectedInfluencer} onValueChange={setSelectedInfluencer}>
                    <SelectTrigger className={`w-48 h-8 bg-black/30 ${
                      selectedInfluencer === 'starbright_monroe' ? 'border-pink-500/50' : 'border-blue-500/50'
                    }`}>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {influencerOptions.map(inf => (
                        <SelectItem key={inf.value} value={inf.value}>
                          <span className={inf.color}>{inf.label}</span>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <Badge variant="outline" className={
                  selectedInfluencer === 'starbright_monroe' ? 'border-pink-500/50 text-pink-400' : 'border-blue-500/50 text-blue-400'
                }>
                  {selectedInfluencer === 'starbright_monroe' ? 'Warm tones' : 'Moody vibes'}
                </Badge>
              </div>

              {/* Consistency Mode Toggle */}
              <div className={`p-2 rounded-md border transition-colors ${consistencyMode ? 'bg-primary/5 border-primary/30' : 'border-white/5'}`}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="flex items-center gap-2">
                      {consistencyMode ? (
                        <Lock className="w-4 h-4 text-primary" />
                      ) : (
                        <Unlock className="w-4 h-4 text-muted-foreground" />
                      )}
                      <Label htmlFor="consistency-mode" className="text-sm font-medium">
                        Consistency Mode
                      </Label>
                    </div>
                    <Switch
                      id="consistency-mode"
                      checked={consistencyMode}
                      onCheckedChange={setConsistencyMode}
                    />
                  </div>
                  
                  {consistencyMode && (
                    <div className="flex items-center gap-2">
                      <Label className="text-xs text-muted-foreground">Background:</Label>
                      <Select value={selectedBackground} onValueChange={setSelectedBackground}>
                        <SelectTrigger className="w-40 h-8 bg-black/30 text-xs">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {backgroundOptions.map(bg => (
                            <SelectItem key={bg.value} value={bg.value}>
                              {bg.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  )}
                </div>
                
                <p className="text-xs text-muted-foreground mt-2">
                  {consistencyMode 
                    ? "Backgrounds will be locked to the selected preset. No earrings/jewelry."
                    : "Using original prompt backgrounds (varied). Toggle for consistent backgrounds."
                  }
                </p>
              </div>
            </CardContent>
          </Card>

          {prompts.length === 0 ? (
            <Card className="bg-black/20 border-white/10 p-8 text-center">
              <Sparkles className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
              <p className="text-muted-foreground">
                No prompts in library yet. Analyze a competitor to generate prompts.
              </p>
            </Card>
          ) : (
            <div className="grid gap-3">
              {prompts.map((prompt, idx) => (
                <Card 
                  key={idx} 
                  className={`bg-black/20 border-white/10 transition-colors ${
                    selectedPrompts.has(prompt.id) ? 'border-primary/50 bg-primary/5' : ''
                  }`}
                >
                  <CardContent className="p-4">
                    <div className="flex items-start gap-3">
                      <div className="pt-1">
                        <Checkbox
                          checked={selectedPrompts.has(prompt.id)}
                          onCheckedChange={() => togglePromptSelection(prompt.id)}
                          className="border-white/30"
                        />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <Badge variant="outline" className="text-xs">
                            {prompt.category}
                          </Badge>
                          {prompt.source && (
                            <Badge variant="secondary" className="text-xs">
                              from @{prompt.source}
                            </Badge>
                          )}
                        </div>
                        <p className="text-sm text-gray-300 leading-relaxed">
                          {prompt.prompt}
                        </p>
                        {prompt.caption_hook && (
                          <div className="mt-2 text-xs text-pink-400">
                            <MessageSquare className="w-3 h-3 inline mr-1" />
                            {prompt.caption_hook}
                          </div>
                        )}
                      </div>
                      <div className="flex items-center gap-1">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => openEditDialog(prompt)}
                          disabled={generatingId !== null || batchGenerating}
                          title="Edit prompt before generating"
                        >
                          <Pencil className="w-4 h-4 text-blue-400" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => generateFromPrompt(prompt)}
                          disabled={generatingId !== null || batchGenerating}
                          title="Generate image from this prompt"
                        >
                          {generatingId === prompt.id ? (
                            <Loader2 className="w-4 h-4 animate-spin text-primary" />
                          ) : (
                            <Wand2 className="w-4 h-4 text-primary" />
                          )}
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => copyPrompt(prompt)}
                          title="Copy prompt to clipboard"
                        >
                          {copiedId === prompt.id ? (
                            <Check className="w-4 h-4 text-green-400" />
                          ) : (
                            <Copy className="w-4 h-4" />
                          )}
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="hooks" className="space-y-4">
          <Card className="bg-black/20 border-white/10">
            <CardHeader>
              <CardTitle className="text-sm flex items-center gap-2">
                <TrendingUp className="w-4 h-4" />
                Proven Engagement Hooks
              </CardTitle>
              <CardDescription>
                High-performing caption formulas from successful AI influencers
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {[
                { hook: "Give me your honest opinion... I'm 18, 5'2 and 90lbs. Yay or nay?", engagement: "Very High" },
                { hook: "If you are a straight guy who likes [type] girls... Stop scrolling and leave a ❤️", engagement: "Very High" },
                { hook: "Rate me 1-10? Be honest 👀", engagement: "High" },
                { hook: "Would you take me on a date? Yes or no?", engagement: "High" },
                { hook: "POV: I'm your girlfriend for the day 💕", engagement: "High" },
                { hook: "What's the first thing you noticed about me?", engagement: "Medium" },
                { hook: "Guess my age... 🤔", engagement: "Medium" }
              ].map((item, idx) => (
                <div key={idx} className="flex items-center justify-between p-3 bg-white/5 rounded-lg">
                  <div className="flex-1">
                    <p className="text-sm">{item.hook}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant={item.engagement === "Very High" ? "default" : "secondary"} className="text-xs">
                      {item.engagement}
                    </Badge>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => {
                        navigator.clipboard.writeText(item.hook);
                        toast({ title: "Copied!", description: "Hook copied to clipboard" });
                      }}
                    >
                      <Copy className="w-3 h-3" />
                    </Button>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <Dialog open={editingPrompt !== null} onOpenChange={(open) => !open && setEditingPrompt(null)}>
        <DialogContent className="max-w-2xl bg-black/95 border-white/10">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Pencil className="w-4 h-4" />
              Edit Prompt
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Prompt Text</Label>
              <Textarea
                value={editedText}
                onChange={(e) => setEditedText(e.target.value)}
                className="min-h-[200px] bg-black/40 border-white/10"
                placeholder="Edit your prompt here..."
              />
            </div>
            <p className="text-xs text-muted-foreground">
              Tip: Add details like "people in the background", "at a cafe with customers", or "crowded beach setting" to make scenes more realistic.
            </p>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditingPrompt(null)}>
              Cancel
            </Button>
            <Button onClick={generateEditedPrompt} className="gap-2">
              <Wand2 className="w-4 h-4" />
              Generate Image
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default ResearchTab;
