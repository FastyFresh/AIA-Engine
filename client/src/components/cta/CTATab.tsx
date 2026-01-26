import { useState, useEffect } from "react";
import { 
  RefreshCw, 
  Copy, 
  Check, 
  Sparkles, 
  FileText, 
  MessageSquare, 
  Zap,
  ExternalLink
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useToast } from "@/hooks/use-toast";
import { LogEntryType } from "@/components/gallery/types";

interface CTATabProps {
  backendUrl: string;
  addLog: (agent: string, message: string, type?: LogEntryType) => void;
}

interface OptimizationData {
  suggested_bio: {
    bio: string;
    source: string;
    character_count: number;
  };
  suggested_pinned_post: {
    content: string;
    source: string;
    character_count?: number;
  };
  cta_templates: Record<string, string[]>;
  post_cta: string;
  optimization_tips: string[];
  generated_at: string;
}

export function CTATab({ backendUrl, addLog }: CTATabProps) {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<OptimizationData | null>(null);
  const [copiedField, setCopiedField] = useState<string | null>(null);
  const { toast } = useToast();

  const fetchOptimizations = async () => {
    setLoading(true);
    addLog("CTA", "Generating AI-optimized CTAs...", "info");
    
    try {
      const response = await fetch(`${backendUrl}/api/cta/optimize?persona=starbright_monroe`);
      if (!response.ok) throw new Error("Failed to fetch optimizations");
      
      const result = await response.json();
      setData(result);
      addLog("CTA", "CTA optimization complete", "success");
      
      toast({
        title: "Optimizations Ready",
        description: "AI-generated suggestions are ready to use"
      });
    } catch (error) {
      addLog("CTA", `Error: ${error}`, "error");
      toast({
        title: "Error",
        description: "Failed to generate optimizations",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = async (text: string, field: string) => {
    await navigator.clipboard.writeText(text);
    setCopiedField(field);
    setTimeout(() => setCopiedField(null), 2000);
    
    toast({
      title: "Copied!",
      description: "Text copied to clipboard"
    });
  };

  const regenerateBio = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/cta/bio?persona=starbright_monroe`);
      if (!response.ok) throw new Error("Failed to regenerate bio");
      
      const result = await response.json();
      if (data) {
        setData({ ...data, suggested_bio: result });
      }
      
      toast({
        title: "New Bio Generated",
        description: "Fresh AI-generated bio suggestion"
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to regenerate bio",
        variant: "destructive"
      });
    }
  };

  const regeneratePinned = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/cta/pinned?persona=starbright_monroe`);
      if (!response.ok) throw new Error("Failed to regenerate pinned post");
      
      const result = await response.json();
      if (data) {
        setData({ ...data, suggested_pinned_post: result });
      }
      
      toast({
        title: "New Pinned Post Generated",
        description: "Fresh AI-generated pinned post suggestion"
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to regenerate pinned post",
        variant: "destructive"
      });
    }
  };

  useEffect(() => {
    fetchOptimizations();
  }, []);

  const CopyButton = ({ text, field }: { text: string; field: string }) => (
    <Button
      size="sm"
      variant="ghost"
      className="h-8 w-8 p-0"
      onClick={() => copyToClipboard(text, field)}
    >
      {copiedField === field ? (
        <Check className="h-4 w-4 text-green-500" />
      ) : (
        <Copy className="h-4 w-4" />
      )}
    </Button>
  );

  return (
    <div className="h-full flex flex-col gap-4 overflow-auto">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold flex items-center gap-2">
            <Zap className="h-5 w-5 text-purple-400" />
            DFans CTA Optimizer
          </h2>
          <p className="text-sm text-muted-foreground">
            AI-optimized CTAs to maximize X to DFans conversions
          </p>
        </div>
        <Button 
          onClick={fetchOptimizations} 
          disabled={loading}
          className="bg-purple-600 hover:bg-purple-700"
        >
          <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          {loading ? "Generating..." : "Regenerate All"}
        </Button>
      </div>

      {data ? (
        <Tabs defaultValue="bio" className="flex-1">
          <TabsList className="bg-black/40 border border-white/5">
            <TabsTrigger value="bio" className="text-xs font-mono">BIO</TabsTrigger>
            <TabsTrigger value="pinned" className="text-xs font-mono">PINNED_POST</TabsTrigger>
            <TabsTrigger value="ctas" className="text-xs font-mono">CTA_LIBRARY</TabsTrigger>
            <TabsTrigger value="tips" className="text-xs font-mono">TIPS</TabsTrigger>
          </TabsList>

          <TabsContent value="bio" className="mt-4">
            <Card className="glass-panel">
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-sm flex items-center gap-2">
                      <FileText className="h-4 w-4 text-purple-400" />
                      Suggested Bio
                    </CardTitle>
                    <CardDescription className="text-xs">
                      {data.suggested_bio.character_count}/160 characters
                      <Badge variant="outline" className="ml-2 text-xs">
                        {data.suggested_bio.source === "grok_ai" ? "Grok AI" : "Template"}
                      </Badge>
                    </CardDescription>
                  </div>
                  <div className="flex gap-2">
                    <Button size="sm" variant="outline" onClick={regenerateBio}>
                      <RefreshCw className="h-3 w-3 mr-1" />
                      New
                    </Button>
                    <CopyButton text={data.suggested_bio.bio} field="bio" />
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="bg-black/40 p-4 rounded-lg border border-white/10 font-medium text-lg">
                  {data.suggested_bio.bio}
                </div>
                <p className="text-xs text-muted-foreground mt-3">
                  Copy and paste this into your X profile bio. Update weekly for freshness.
                </p>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="pinned" className="mt-4">
            <Card className="glass-panel">
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-sm flex items-center gap-2">
                      <MessageSquare className="h-4 w-4 text-purple-400" />
                      Suggested Pinned Post
                    </CardTitle>
                    <CardDescription className="text-xs">
                      {data.suggested_pinned_post.character_count || data.suggested_pinned_post.content.length}/280 characters
                      <Badge variant="outline" className="ml-2 text-xs">
                        {data.suggested_pinned_post.source === "grok_ai" ? "Grok AI" : "Template"}
                      </Badge>
                    </CardDescription>
                  </div>
                  <div className="flex gap-2">
                    <Button size="sm" variant="outline" onClick={regeneratePinned}>
                      <RefreshCw className="h-3 w-3 mr-1" />
                      New
                    </Button>
                    <CopyButton text={data.suggested_pinned_post.content} field="pinned" />
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="bg-black/40 p-4 rounded-lg border border-white/10 whitespace-pre-wrap">
                  {data.suggested_pinned_post.content}
                </div>
                <p className="text-xs text-muted-foreground mt-3">
                  Pin this tweet to your profile. New followers see this first!
                </p>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="ctas" className="mt-4">
            <div className="grid gap-4">
              {Object.entries(data.cta_templates).map(([category, ctas]) => (
                <Card key={category} className="glass-panel">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm capitalize flex items-center gap-2">
                      <Sparkles className="h-4 w-4 text-purple-400" />
                      {category.replace("_", " ")}
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid gap-2">
                      {ctas.map((cta, index) => (
                        <div 
                          key={index}
                          className="flex items-center justify-between bg-black/40 p-3 rounded-lg border border-white/10 group hover:border-purple-500/30 transition-colors"
                        >
                          <span className="text-sm">{cta}</span>
                          <CopyButton text={cta} field={`${category}-${index}`} />
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="tips" className="mt-4">
            <Card className="glass-panel">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm flex items-center gap-2">
                  <Zap className="h-4 w-4 text-yellow-400" />
                  Optimization Tips
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-3">
                  {data.optimization_tips.map((tip, index) => (
                    <li key={index} className="flex items-start gap-3 text-sm">
                      <span className="text-purple-400 font-bold">{index + 1}.</span>
                      <span>{tip}</span>
                    </li>
                  ))}
                </ul>
                <div className="mt-6 p-4 bg-purple-500/10 border border-purple-500/20 rounded-lg">
                  <h4 className="font-bold text-sm mb-2 flex items-center gap-2">
                    <ExternalLink className="h-4 w-4" />
                    Quick Actions
                  </h4>
                  <div className="flex gap-2 flex-wrap">
                    <a 
                      href="https://twitter.com/settings/profile" 
                      target="_blank" 
                      rel="noopener noreferrer"
                    >
                      <Button size="sm" variant="outline">
                        Update X Bio
                      </Button>
                    </a>
                    <a 
                      href="https://twitter.com/Starbright2003" 
                      target="_blank" 
                      rel="noopener noreferrer"
                    >
                      <Button size="sm" variant="outline">
                        View Profile
                      </Button>
                    </a>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      ) : (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <Sparkles className="h-12 w-12 mx-auto text-purple-400 mb-4" />
            <p className="text-muted-foreground">
              {loading ? "Generating AI optimizations..." : "Click 'Regenerate All' to get started"}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

export default CTATab;
