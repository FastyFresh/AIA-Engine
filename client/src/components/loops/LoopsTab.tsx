import { useState, useEffect, useCallback } from "react";
import { Video, Image as ImageIcon, RefreshCw, Loader2, Play, Shuffle, Type, Download, Trash2, Twitter, Send, CheckCircle, Upload, Sparkles, Music } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useToast } from "@/hooks/use-toast";
import { LogEntryType, INFLUENCERS, getApiBase } from "@/components/gallery/types";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";

interface LoopsTabProps {
  backendUrl: string;
  useLiveMode: boolean;
  addLog: (agent: string, message: string, type: LogEntryType) => void;
}

interface HeroRef {
  filename: string;
  path: string;
  size_kb: number;
  created: string;
}

interface LoopVideo {
  filename: string;
  path: string;
  size_kb: number;
  created: string;
  movement_type?: string;
  hero_ref?: string;
}

interface MovementPrompts {
  [key: string]: string;
}

export function LoopsTab({ backendUrl, useLiveMode, addLog }: LoopsTabProps) {
  const { toast } = useToast();
  const [selectedInfluencer, setSelectedInfluencer] = useState("luna_vale");
  const [heroRefs, setHeroRefs] = useState<HeroRef[]>([]);
  const [loops, setLoops] = useState<LoopVideo[]>([]);
  const [movements, setMovements] = useState<string[]>([]);
  const [movementPrompts, setMovementPrompts] = useState<MovementPrompts>({});
  const [isLoadingRefs, setIsLoadingRefs] = useState(false);
  const [isLoadingLoops, setIsLoadingLoops] = useState(false);
  const [generatingFor, setGeneratingFor] = useState<string | null>(null);
  const [selectedMovement, setSelectedMovement] = useState<string>("random");
  const [workflowType, setWorkflowType] = useState<string | null>(null);
  
  const [previewVideo, setPreviewVideo] = useState<LoopVideo | null>(null);
  const [generateDialogOpen, setGenerateDialogOpen] = useState(false);
  const [selectedHeroForGenerate, setSelectedHeroForGenerate] = useState<HeroRef | null>(null);
  
  const [captionText, setCaptionText] = useState("");
  const [captionPosition, setCaptionPosition] = useState<string>("center");
  const [captionFontSize, setCaptionFontSize] = useState<number>(24);
  const [isAddingCaption, setIsAddingCaption] = useState(false);
  const [showCaptionForm, setShowCaptionForm] = useState(false);
  
  const [captionedVideos, setCaptionedVideos] = useState<LoopVideo[]>([]);
  const [isLoadingCaptioned, setIsLoadingCaptioned] = useState(false);
  
  const [captionSuggestions, setCaptionSuggestions] = useState<Array<{id: string; lines: string[]; theme?: string; pattern?: string; emotional_mode?: string; formatted: string; source?: string}>>([]);
  const [isLoadingSuggestions, setIsLoadingSuggestions] = useState(false);
  const [selectedTheme, setSelectedTheme] = useState<string>("all");
  const [useAiCaptions, setUseAiCaptions] = useState(true);
  const [captionSource, setCaptionSource] = useState<string>("");

  const [twitterDialogOpen, setTwitterDialogOpen] = useState(false);
  const [twitterVideoToShare, setTwitterVideoToShare] = useState<LoopVideo | null>(null);
  const [tweetText, setTweetText] = useState("");
  const [isPostingTweet, setIsPostingTweet] = useState(false);
  const [twitterConnected, setTwitterConnected] = useState(false);
  const [twitterMediaReady, setTwitterMediaReady] = useState(false);
  const [includeCTA, setIncludeCTA] = useState(true);
  const [includeHashtags, setIncludeHashtags] = useState(true);
  const [composedPreview, setComposedPreview] = useState<string>("");

  const [musicTracks, setMusicTracks] = useState<Array<{id: string; title: string; mood: string; tempo: string; genre: string; filename: string}>>([]);
  const [selectedMusic, setSelectedMusic] = useState<string | null>(null);
  const [includeMusic, setIncludeMusic] = useState(false);
  const [isLoadingMusicRec, setIsLoadingMusicRec] = useState(false);
  const [musicRecommendation, setMusicRecommendation] = useState<{track_id: string; reasoning: string} | null>(null);
  const [isMergingMusic, setIsMergingMusic] = useState(false);

  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [uploadInfluencer, setUploadInfluencer] = useState<string>("starbright_monroe");
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<{
    outfit?: string;
    setting?: string;
    mood?: string;
    details?: string;
    suggested_filename?: string;
    description?: string;
  } | null>(null);
  const [customFilename, setCustomFilename] = useState<string>("");

  const apiBase = getApiBase(backendUrl);

  const loadWorkflowType = useCallback(async () => {
    try {
      const response = await fetch(`${apiBase}/influencer/workflow_type?influencer=${selectedInfluencer}`);
      if (response.ok) {
        const data = await response.json();
        setWorkflowType(data.workflow_type);
      }
    } catch (error) {
      console.error("Failed to load workflow type:", error);
    }
  }, [apiBase, selectedInfluencer]);

  const loadHeroRefs = useCallback(async () => {
    setIsLoadingRefs(true);
    try {
      const response = await fetch(`${apiBase}/micro_loop/hero_refs?influencer=${selectedInfluencer}`);
      if (!response.ok) throw new Error("Failed to load hero refs");
      
      const data = await response.json();
      setHeroRefs(data.hero_refs || []);
      addLog("LOOPS", `Loaded ${data.count || 0} hero refs for ${selectedInfluencer}`, "info");
    } catch (error: any) {
      toast({
        title: "Failed to load hero refs",
        description: error.message,
        variant: "destructive"
      });
    } finally {
      setIsLoadingRefs(false);
    }
  }, [apiBase, selectedInfluencer, addLog, toast]);

  const loadLoops = useCallback(async () => {
    setIsLoadingLoops(true);
    try {
      const response = await fetch(`${apiBase}/micro_loop/list?influencer=${selectedInfluencer}`);
      if (!response.ok) throw new Error("Failed to load loops");
      
      const data = await response.json();
      setLoops(data.loops || []);
      addLog("LOOPS", `Loaded ${data.count || 0} loops for ${selectedInfluencer}`, "info");
    } catch (error: any) {
      toast({
        title: "Failed to load loops",
        description: error.message,
        variant: "destructive"
      });
    } finally {
      setIsLoadingLoops(false);
    }
  }, [apiBase, selectedInfluencer, addLog, toast]);

  const loadMovements = useCallback(async () => {
    try {
      const response = await fetch(`${apiBase}/micro_loop/movements`);
      if (!response.ok) throw new Error("Failed to load movements");
      
      const data = await response.json();
      setMovements(data.movements || []);
      setMovementPrompts(data.prompts || {});
    } catch (error: any) {
      console.error("Failed to load movements:", error);
    }
  }, [apiBase]);

  const loadCaptioned = useCallback(async () => {
    setIsLoadingCaptioned(true);
    try {
      const response = await fetch(`${apiBase}/micro_loop/captioned`);
      if (!response.ok) throw new Error("Failed to load captioned videos");
      
      const data = await response.json();
      setCaptionedVideos(data.videos || []);
      addLog("LOOPS", `Loaded ${data.count || 0} captioned videos`, "info");
    } catch (error: any) {
      console.error("Failed to load captioned videos:", error);
    } finally {
      setIsLoadingCaptioned(false);
    }
  }, [apiBase, addLog]);

  const checkTwitterStatus = useCallback(async () => {
    try {
      const response = await fetch(`${apiBase}/api/twitter/status`);
      if (response.ok) {
        const data = await response.json();
        setTwitterConnected(data.authorized === true);
        setTwitterMediaReady(data.media_upload_ready === true);
      }
    } catch (error) {
      console.error("Failed to check Twitter status:", error);
    }
  }, [apiBase]);

  const loadComposedPreview = useCallback(async (caption: string) => {
    try {
      const params = new URLSearchParams({
        caption: caption,
        influencer: selectedInfluencer,
        include_cta: includeCTA.toString(),
        include_hashtags: includeHashtags.toString()
      });
      const response = await fetch(`${apiBase}/api/twitter/compose?${params}`);
      if (response.ok) {
        const data = await response.json();
        setComposedPreview(data.composed_text);
      }
    } catch (error) {
      console.error("Failed to load compose preview:", error);
    }
  }, [apiBase, selectedInfluencer, includeCTA, includeHashtags]);

  const loadMusicTracks = useCallback(async () => {
    try {
      const response = await fetch(`${apiBase}/api/music/tracks`);
      if (response.ok) {
        const data = await response.json();
        setMusicTracks(data.tracks || []);
      }
    } catch (error) {
      console.error("Failed to load music tracks:", error);
    }
  }, [apiBase]);

  const getMusicRecommendation = useCallback(async (videoFilename: string, captionText: string) => {
    setIsLoadingMusicRec(true);
    try {
      const params = new URLSearchParams({
        video_filename: videoFilename,
        influencer: selectedInfluencer,
        caption: captionText
      });
      const response = await fetch(`${apiBase}/api/music/recommend?${params}`);
      if (response.ok) {
        const data = await response.json();
        if (data.success && data.recommendation) {
          setMusicRecommendation({
            track_id: data.recommendation.recommended_track_id,
            reasoning: data.recommendation.reasoning
          });
          setSelectedMusic(data.recommendation.recommended_track_id);
        }
      }
    } catch (error) {
      console.error("Failed to get music recommendation:", error);
    } finally {
      setIsLoadingMusicRec(false);
    }
  }, [apiBase, selectedInfluencer]);

  const handleShareOnTwitter = async (video: LoopVideo) => {
    setTwitterVideoToShare(video);
    setTweetText("");
    setComposedPreview("");
    setSelectedMusic(null);
    setMusicRecommendation(null);
    setIncludeMusic(false);
    setTwitterDialogOpen(true);
    await loadMusicTracks();
  };

  const handlePostTweet = async () => {
    if (!tweetText.trim() || !twitterVideoToShare) return;
    
    setIsPostingTweet(true);
    try {
      // Use the full package endpoint with video
      const params = new URLSearchParams({
        caption: tweetText,
        media_path: twitterVideoToShare.path,
        influencer: selectedInfluencer,
        include_cta: includeCTA.toString(),
        include_hashtags: includeHashtags.toString(),
        include_music: includeMusic.toString()
      });
      
      // Add music track if selected
      if (includeMusic && selectedMusic) {
        params.append("music_track_id", selectedMusic);
      }
      
      const response = await fetch(`${apiBase}/api/twitter/post_full?${params}`, {
        method: "POST"
      });
      
      const data = await response.json();
      
      if (data.status === "success") {
        addLog("TWITTER", `Posted tweet with video: ${data.tweet_url}`, "success");
        toast({
          title: "Posted to Twitter!",
          description: (
            <a href={data.tweet_url} target="_blank" rel="noopener noreferrer" className="underline">
              View your tweet
            </a>
          )
        });
        setTwitterDialogOpen(false);
        setTweetText("");
        setTwitterVideoToShare(null);
        setComposedPreview("");
      } else {
        throw new Error(data.error || data.detail?.error || "Failed to post");
      }
    } catch (error: any) {
      addLog("TWITTER", `Failed to post: ${error.message}`, "error");
      toast({
        title: "Failed to post",
        description: error.message,
        variant: "destructive"
      });
    } finally {
      setIsPostingTweet(false);
    }
  };

  const loadCaptionSuggestions = useCallback(async (theme?: string, useAi: boolean = true, heroImage?: string, movementType?: string) => {
    setIsLoadingSuggestions(true);
    try {
      let response;
      if (useAi) {
        const heroParam = heroImage ? `&hero_image=${encodeURIComponent(heroImage)}` : "";
        const movementParam = movementType ? `&movement_type=${encodeURIComponent(movementType)}` : "";
        const influencerParam = `&influencer=${encodeURIComponent(selectedInfluencer)}`;
        response = await fetch(`${apiBase}/micro_loop/generate_caption?count=5${heroParam}${movementParam}${influencerParam}`);
      } else {
        const themeParam = theme && theme !== "all" ? `&theme=${theme}` : "";
        const influencerParam = `&influencer=${encodeURIComponent(selectedInfluencer)}`;
        response = await fetch(`${apiBase}/micro_loop/caption_suggestions?count=6${themeParam}${influencerParam}`);
      }
      
      if (!response.ok) throw new Error("Failed to load suggestions");
      
      const data = await response.json();
      setCaptionSuggestions(data.suggestions || []);
      setCaptionSource(data.source || (useAi ? "ai" : "templates"));
    } catch (error: any) {
      console.error("Failed to load caption suggestions:", error);
    } finally {
      setIsLoadingSuggestions(false);
    }
  }, [apiBase, selectedInfluencer]);

  useEffect(() => {
    loadWorkflowType();
    loadHeroRefs();
    loadLoops();
    loadMovements();
    loadCaptioned();
    checkTwitterStatus();
  }, [selectedInfluencer, loadWorkflowType, loadHeroRefs, loadLoops, loadMovements, loadCaptioned, checkTwitterStatus]);

  useEffect(() => {
    if (showCaptionForm && previewVideo && captionSuggestions.length === 0) {
      loadCaptionSuggestions(selectedTheme, useAiCaptions, previewVideo.hero_ref, previewVideo.movement_type);
    }
  }, [showCaptionForm, previewVideo, captionSuggestions.length, loadCaptionSuggestions, selectedTheme, useAiCaptions]);

  const handleGenerateLoop = async (heroRef: HeroRef, movement: string) => {
    setGeneratingFor(heroRef.path);
    setGenerateDialogOpen(false);
    
    try {
      const movementParam = movement === "random" ? "" : `&movement_type=${movement}`;
      const response = await fetch(
        `${apiBase}/micro_loop/generate?hero_image_path=${encodeURIComponent(heroRef.path)}&influencer=${selectedInfluencer}${movementParam}`,
        { method: "POST" }
      );
      
      const data = await response.json();
      
      if (data.status === "success") {
        addLog("LOOPS", `Generated loop: ${data.output_path?.split('/').pop() || 'video'}`, "success");
        toast({ 
          title: "Loop generated!", 
          description: `Movement: ${data.movement_type || movement}`
        });
        await loadLoops();
      } else {
        throw new Error(data.error || "Generation failed");
      }
    } catch (error: any) {
      addLog("LOOPS", `Generation failed: ${error.message}`, "error");
      toast({ 
        title: "Generation failed", 
        description: error.message, 
        variant: "destructive" 
      });
    } finally {
      setGeneratingFor(null);
    }
  };

  const openGenerateDialog = (heroRef: HeroRef) => {
    setSelectedHeroForGenerate(heroRef);
    setSelectedMovement("random");
    setGenerateDialogOpen(true);
  };

  const handleAddCaption = async () => {
    console.log("handleAddCaption called", { previewVideo, captionText, captionPosition });
    
    if (!previewVideo || !captionText.trim()) {
      console.log("Early return - no video or caption text");
      return;
    }
    
    setIsAddingCaption(true);
    try {
      const captionLines = captionText.replace(/\n/g, "|");
      const params = new URLSearchParams({
        video_path: previewVideo.path,
        caption_lines: captionLines,
        position: captionPosition,
        font_size: captionFontSize.toString()
      });
      
      console.log("Making API call to:", `${apiBase}/micro_loop/caption?${params.toString()}`);
      
      const response = await fetch(`${apiBase}/micro_loop/caption?${params.toString()}`, {
        method: "POST"
      });
      
      const data = await response.json();
      
      if (data.success) {
        addLog("LOOPS", `Caption added: ${data.output_path?.split('/').pop() || 'video'}`, "success");
        toast({ 
          title: "Caption added!", 
          description: "Video with caption saved to captioned folder"
        });
        setShowCaptionForm(false);
        setCaptionText("");
        setPreviewVideo(null);
        await loadLoops();
        await loadCaptioned();
      } else {
        throw new Error(data.error || "Failed to add caption");
      }
    } catch (error: any) {
      addLog("LOOPS", `Caption failed: ${error.message}`, "error");
      toast({ 
        title: "Caption failed", 
        description: error.message, 
        variant: "destructive" 
      });
    } finally {
      setIsAddingCaption(false);
    }
  };

  const handleDelete = async (filePath: string, contentType: "hero_ref" | "loop" | "captioned") => {
    if (!confirm(`Are you sure you want to delete this ${contentType.replace("_", " ")}? It will be moved to archives and can be recovered.`)) {
      return;
    }

    try {
      const response = await fetch(
        `${apiBase}/content/delete?file_path=${encodeURIComponent(filePath)}&content_type=${contentType}&influencer=${selectedInfluencer}`,
        { method: "DELETE" }
      );

      const data = await response.json();

      if (data.status === "deleted") {
        addLog("LOOPS", `Deleted: ${filePath.split('/').pop()}`, "success");
        toast({
          title: "Deleted successfully",
          description: "File moved to archives (recoverable)"
        });
        
        if (contentType === "hero_ref") {
          await loadHeroRefs();
        } else if (contentType === "loop") {
          await loadLoops();
        } else {
          await loadCaptioned();
        }
      } else {
        throw new Error(data.detail || "Delete failed");
      }
    } catch (error: any) {
      addLog("LOOPS", `Delete failed: ${error.message}`, "error");
      toast({
        title: "Delete failed",
        description: error.message,
        variant: "destructive"
      });
    }
  };

  const microLoopInfluencers = INFLUENCERS.filter(inf => 
    inf.id === "luna_vale"
  );

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    setUploadFile(file);
    setAnalysisResult(null);
    setCustomFilename("");
    
    setIsAnalyzing(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("influencer", uploadInfluencer);
      
      const response = await fetch(`${apiBase}/micro_loop/analyze_hero`, {
        method: "POST",
        body: formData
      });
      
      const data = await response.json();
      if (data.success) {
        setAnalysisResult(data);
        setCustomFilename(data.suggested_filename || "");
        addLog("UPLOAD", `Analyzed: ${data.outfit}/${data.setting}`, "info");
      } else {
        addLog("UPLOAD", `Analysis failed: ${data.error}`, "warning");
      }
    } catch (error: any) {
      addLog("UPLOAD", `Analysis error: ${error.message}`, "error");
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleUploadHero = async () => {
    if (!uploadFile) return;
    
    setIsUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", uploadFile);
      formData.append("influencer", uploadInfluencer);
      if (customFilename.trim()) {
        formData.append("custom_name", customFilename.trim());
      }
      
      const response = await fetch(`${apiBase}/micro_loop/upload_hero`, {
        method: "POST",
        body: formData
      });
      
      const data = await response.json();
      if (data.success) {
        addLog("UPLOAD", `Uploaded: ${data.filename}`, "success");
        toast({
          title: "Hero image uploaded!",
          description: `Saved as ${data.filename}`
        });
        setUploadDialogOpen(false);
        setUploadFile(null);
        setAnalysisResult(null);
        setCustomFilename("");
        if (uploadInfluencer !== selectedInfluencer) {
          setSelectedInfluencer(uploadInfluencer);
        } else {
          await loadHeroRefs();
        }
      } else {
        throw new Error(data.detail || "Upload failed");
      }
    } catch (error: any) {
      addLog("UPLOAD", `Upload failed: ${error.message}`, "error");
      toast({
        title: "Upload failed",
        description: error.message,
        variant: "destructive"
      });
    } finally {
      setIsUploading(false);
    }
  };

  const openUploadDialog = () => {
    setUploadFile(null);
    setAnalysisResult(null);
    setCustomFilename("");
    setUploadInfluencer(selectedInfluencer);
    setUploadDialogOpen(true);
  };

  if (workflowType === null) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-muted-foreground">
        <Loader2 className="w-8 h-8 animate-spin text-primary mb-4" />
        <p className="text-sm">Loading workflow configuration...</p>
      </div>
    );
  }

  if (workflowType === "lora_full") {
    return (
      <div className="h-full flex flex-col items-center justify-center text-muted-foreground">
        <Video className="w-12 h-12 mb-4 opacity-30" />
        <p className="text-lg font-medium">Full LoRA Workflow</p>
        <p className="text-sm mt-2">This influencer uses the full LoRA generation pipeline.</p>
        <p className="text-sm">Use the Content Gallery tab for image management.</p>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <Select value={selectedInfluencer} onValueChange={setSelectedInfluencer}>
            <SelectTrigger className="w-48 bg-black/20 border-white/10">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {INFLUENCERS.map(inf => (
                <SelectItem key={inf.id} value={inf.id}>{inf.name}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          
          <Button 
            variant="outline" 
            size="sm" 
            onClick={() => { loadHeroRefs(); loadLoops(); loadCaptioned(); }}
            disabled={isLoadingRefs || isLoadingLoops || isLoadingCaptioned}
            className="border-white/10"
          >
            <RefreshCw className={`w-4 h-4 mr-1 ${(isLoadingRefs || isLoadingLoops || isLoadingCaptioned) ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          
          <Button 
            size="sm" 
            onClick={openUploadDialog}
            className="bg-purple-600 hover:bg-purple-500"
          >
            <Upload className="w-4 h-4 mr-1" />
            Upload Hero
          </Button>
        </div>
        
        <div className="flex items-center gap-2 text-xs">
          <span className="text-purple-400">{heroRefs.length} hero refs</span>
          <span className="text-cyan-400">{loops.length} loops</span>
          <span className="text-pink-400">{captionedVideos.length} captioned</span>
        </div>
      </div>

      <Tabs defaultValue="hero_refs" className="flex-1 flex flex-col">
        <TabsList className="bg-black/40 border border-white/5 mb-4">
          <TabsTrigger value="hero_refs" className="text-xs font-mono">
            <ImageIcon className="w-3 h-3 mr-1" />
            HERO_REFS
          </TabsTrigger>
          <TabsTrigger value="loops" className="text-xs font-mono">
            <Video className="w-3 h-3 mr-1" />
            GENERATED_LOOPS
          </TabsTrigger>
          <TabsTrigger value="captioned" className="text-xs font-mono">
            <Type className="w-3 h-3 mr-1" />
            CAPTIONED
          </TabsTrigger>
        </TabsList>

        <TabsContent value="hero_refs" className="flex-1 mt-0">
          <ScrollArea className="h-full">
            {isLoadingRefs ? (
              <div className="flex items-center justify-center h-40">
                <Loader2 className="w-8 h-8 animate-spin text-primary" />
              </div>
            ) : heroRefs.length === 0 ? (
              <div className="text-center py-12 text-muted-foreground">
                <ImageIcon className="w-10 h-10 mx-auto mb-3 opacity-30" />
                <p>No hero reference images yet</p>
                <p className="text-xs mt-2">Upload images to content/references/{selectedInfluencer}/hero/</p>
              </div>
            ) : (
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {heroRefs.map((ref) => (
                  <div 
                    key={ref.path}
                    className="relative group rounded-lg overflow-hidden border border-white/10 hover:border-purple-500/50 transition-all"
                  >
                    <img 
                      src={`${apiBase}/gallery/image/${ref.path}`} 
                      alt={ref.filename}
                      className="w-full aspect-[3/4] object-cover"
                      loading="lazy"
                    />
                    
                    <div className="absolute top-2 left-2 px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-purple-500/90">
                      HERO
                    </div>
                    
                    <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity">
                      <div className="absolute bottom-0 left-0 right-0 p-3">
                        <p className="text-[10px] text-white/80 truncate mb-2">{ref.filename}</p>
                        
                        <div className="flex gap-1">
                          <Button 
                            size="sm" 
                            className="flex-1 h-8 text-xs bg-cyan-600/90 hover:bg-cyan-600"
                            onClick={() => openGenerateDialog(ref)}
                            disabled={generatingFor === ref.path}
                          >
                            {generatingFor === ref.path ? (
                              <>
                                <Loader2 className="w-3 h-3 mr-1 animate-spin" />
                                Generating...
                              </>
                            ) : (
                              <>
                                <Play className="w-3 h-3 mr-1" />
                                Generate
                              </>
                            )}
                          </Button>
                          <Button
                            size="sm"
                            variant="destructive"
                            className="h-8 w-8 p-0"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDelete(ref.path, "hero_ref");
                            }}
                          >
                            <Trash2 className="w-3 h-3" />
                          </Button>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </ScrollArea>
        </TabsContent>

        <TabsContent value="loops" className="flex-1 mt-0">
          <ScrollArea className="h-full">
            {isLoadingLoops ? (
              <div className="flex items-center justify-center h-40">
                <Loader2 className="w-8 h-8 animate-spin text-primary" />
              </div>
            ) : loops.length === 0 ? (
              <div className="text-center py-12 text-muted-foreground">
                <Video className="w-10 h-10 mx-auto mb-3 opacity-30" />
                <p>No loops generated yet</p>
                <p className="text-xs mt-2">Select a hero ref and click Generate Loop</p>
              </div>
            ) : (
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {loops.map((loop) => (
                  <div 
                    key={loop.path}
                    className="relative group rounded-lg overflow-hidden border border-white/10 hover:border-cyan-500/50 transition-all cursor-pointer"
                    onClick={() => setPreviewVideo(loop)}
                  >
                    <div className="w-full aspect-[9/16] bg-black/40 flex items-center justify-center">
                      <video 
                        src={`${apiBase}/micro_loop/video/${selectedInfluencer}/${loop.filename}`}
                        className="w-full h-full object-cover"
                        muted
                        loop
                        playsInline
                        onMouseEnter={(e) => e.currentTarget.play()}
                        onMouseLeave={(e) => { e.currentTarget.pause(); e.currentTarget.currentTime = 0; }}
                      />
                    </div>
                    
                    <div className="absolute top-2 left-2 px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-cyan-500/90">
                      LOOP
                    </div>
                    
                    {loop.movement_type && (
                      <div className="absolute top-2 right-2 px-2 py-0.5 rounded text-[10px] font-medium bg-black/70">
                        {loop.movement_type.replace(/_/g, ' ')}
                      </div>
                    )}
                    
                    <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity">
                      <div className="absolute bottom-0 left-0 right-0 p-3">
                        <p className="text-[10px] text-white/80 truncate">{loop.filename}</p>
                        <div className="flex items-center justify-between mt-1">
                          <p className="text-[9px] text-white/50">{Math.round(loop.size_kb)}KB</p>
                          <Button
                            size="sm"
                            variant="destructive"
                            className="h-6 w-6 p-0"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDelete(loop.path, "loop");
                            }}
                          >
                            <Trash2 className="w-3 h-3" />
                          </Button>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </ScrollArea>
        </TabsContent>

        <TabsContent value="captioned" className="flex-1 mt-0">
          <ScrollArea className="h-full">
            {isLoadingCaptioned ? (
              <div className="flex items-center justify-center h-40">
                <Loader2 className="w-8 h-8 animate-spin text-primary" />
              </div>
            ) : captionedVideos.length === 0 ? (
              <div className="text-center py-12 text-muted-foreground">
                <Type className="w-10 h-10 mx-auto mb-3 opacity-30" />
                <p>No captioned videos yet</p>
                <p className="text-xs mt-2">Add captions to loops from the GENERATED_LOOPS tab</p>
              </div>
            ) : (
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {captionedVideos.map((video) => (
                  <div 
                    key={video.path}
                    className="relative group rounded-lg overflow-hidden border border-white/10 hover:border-pink-500/50 transition-all"
                  >
                    <div className="w-full aspect-[9/16] bg-black/40 flex items-center justify-center">
                      <video 
                        src={`${apiBase}/micro_loop/video/captioned/${video.filename}`}
                        className="w-full h-full object-cover"
                        muted
                        loop
                        playsInline
                        controls
                      />
                    </div>
                    
                    <div className="absolute top-2 left-2 px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-pink-500/90">
                      CAPTIONED
                    </div>
                    
                    <div className="absolute bottom-0 left-0 right-0 p-3 bg-gradient-to-t from-black/80 to-transparent">
                      <p className="text-[10px] text-white/80 truncate">{video.filename}</p>
                      <p className="text-[9px] text-white/50 mt-1">{Math.round(video.size_kb)}KB</p>
                      <div className="flex flex-col gap-1.5 mt-2">
                        <div className="flex items-center gap-1">
                          {twitterConnected ? (
                            <Button
                              size="sm"
                              className="flex-1 h-7 bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-400 hover:to-blue-500 text-[10px] font-semibold shadow-lg shadow-blue-500/30"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleShareOnTwitter(video);
                              }}
                            >
                              <Twitter className="w-3 h-3 mr-1" />
                              Share on Twitter
                            </Button>
                          ) : (
                            <a
                              href="/api/twitter/auth"
                              target="_blank"
                              className="flex-1 inline-flex items-center justify-center gap-1 h-7 px-2 bg-gray-600 hover:bg-gray-500 rounded text-[10px] font-medium"
                              onClick={(e) => e.stopPropagation()}
                            >
                              <Twitter className="w-3 h-3" />
                              Connect Twitter
                            </a>
                          )}
                          <a 
                            href={`${apiBase}/micro_loop/video/captioned/${video.filename}`}
                            download={video.filename}
                            className="inline-flex items-center justify-center h-7 w-7 bg-pink-600 hover:bg-pink-500 rounded"
                            onClick={(e) => e.stopPropagation()}
                            title="Download video"
                          >
                            <Download className="w-3 h-3" />
                          </a>
                          <Button
                            size="sm"
                            variant="destructive"
                            className="h-7 w-7 p-0"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDelete(video.path, "captioned");
                            }}
                          >
                            <Trash2 className="w-3 h-3" />
                          </Button>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </ScrollArea>
        </TabsContent>
      </Tabs>

      <Dialog open={generateDialogOpen} onOpenChange={setGenerateDialogOpen}>
        <DialogContent className="glass-panel border-white/10 text-foreground sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Play className="w-5 h-5 text-cyan-400" />
              Generate Micro-Loop
            </DialogTitle>
            <DialogDescription className="text-muted-foreground">
              Select a movement type for the micro-loop video generation.
            </DialogDescription>
          </DialogHeader>
          
          {selectedHeroForGenerate && (
            <div className="py-4">
              <div className="flex gap-4 items-start mb-4">
                <img 
                  src={`${apiBase}/gallery/image/${selectedHeroForGenerate.path}`}
                  alt="Hero ref"
                  className="w-20 h-28 object-cover rounded-md border border-white/10"
                />
                <div className="flex-1">
                  <p className="text-sm font-medium truncate">{selectedHeroForGenerate.filename}</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    {Math.round(selectedHeroForGenerate.size_kb)}KB
                  </p>
                </div>
              </div>
              
              <div className="space-y-3">
                <label className="text-sm font-medium">Movement Type</label>
                <Select value={selectedMovement} onValueChange={setSelectedMovement}>
                  <SelectTrigger className="w-full bg-black/20 border-white/10">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="random">
                      <div className="flex items-center gap-2">
                        <Shuffle className="w-3 h-3" />
                        Random Movement
                      </div>
                    </SelectItem>
                    {movements.map(m => (
                      <SelectItem key={m} value={m}>
                        {m.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                
                {selectedMovement !== "random" && movementPrompts[selectedMovement] && (
                  <div className="text-xs text-muted-foreground p-3 bg-black/20 rounded-md border border-white/5">
                    {movementPrompts[selectedMovement].substring(0, 150)}...
                  </div>
                )}
              </div>
              
              <Button 
                className="w-full mt-4 bg-cyan-600 hover:bg-cyan-500"
                onClick={() => handleGenerateLoop(selectedHeroForGenerate, selectedMovement)}
              >
                <Play className="w-4 h-4 mr-2" />
                Generate Loop
              </Button>
            </div>
          )}
        </DialogContent>
      </Dialog>

      <Dialog open={!!previewVideo} onOpenChange={(open) => { 
        if (!open) { 
          setPreviewVideo(null); 
          setShowCaptionForm(false);
          setCaptionText("");
          setCaptionSuggestions([]);
          setCaptionSource("");
        }
      }}>
        <DialogContent className="glass-panel border-white/10 text-foreground sm:max-w-[500px] max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Video className="w-5 h-5 text-cyan-400" />
              Loop Preview
            </DialogTitle>
          </DialogHeader>
          
          {previewVideo && (
            <div className="py-2">
              {!showCaptionForm && (
                <>
                  <video 
                    src={`${apiBase}/micro_loop/video/${selectedInfluencer}/${previewVideo.filename}`}
                    className="w-full rounded-lg max-h-[50vh] object-contain"
                    controls
                    autoPlay
                    loop
                  />
                  <div className="mt-3 text-sm">
                    <p className="font-medium">{previewVideo.filename}</p>
                    {previewVideo.movement_type && (
                      <p className="text-muted-foreground text-xs mt-1">
                        Movement: {previewVideo.movement_type.replace(/_/g, ' ')}
                      </p>
                    )}
                  </div>
                  <Button 
                    variant="outline" 
                    className="w-full mt-4 border-pink-500/50 text-pink-400 hover:bg-pink-500/10"
                    onClick={() => setShowCaptionForm(true)}
                  >
                    <Type className="w-4 h-4 mr-2" />
                    Add Caption
                  </Button>
                </>
              )}
              
              {showCaptionForm && (
                <div className="space-y-4">
                  <div className="text-sm text-muted-foreground">
                    Adding caption to: <span className="text-foreground font-medium">{previewVideo.filename}</span>
                  </div>
                  
                  <div className="p-3 bg-gradient-to-r from-pink-500/10 to-purple-500/10 rounded-lg border border-pink-500/20">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <Label className="text-sm font-medium text-pink-300">Caption Ideas</Label>
                        {captionSource && (
                          <span className={`text-[9px] px-1.5 py-0.5 rounded ${captionSource === 'ai_generated' ? 'bg-purple-500/30 text-purple-300' : 'bg-gray-500/30 text-gray-300'}`}>
                            {captionSource === 'ai_generated' ? 'AI' : 'Templates'}
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => setUseAiCaptions(!useAiCaptions)}
                          className={`text-[10px] px-2 py-1 rounded border transition-all ${useAiCaptions ? 'bg-purple-500/20 border-purple-500/50 text-purple-300' : 'bg-gray-500/20 border-gray-500/30 text-gray-400'}`}
                        >
                          {useAiCaptions ? '✨ AI Mode' : '📝 Templates'}
                        </button>
                        <Button 
                          variant="ghost" 
                          size="sm" 
                          onClick={() => loadCaptionSuggestions(selectedTheme, useAiCaptions, previewVideo?.hero_ref, previewVideo?.movement_type)}
                          disabled={isLoadingSuggestions}
                          className="h-7 px-2 text-xs"
                        >
                          {isLoadingSuggestions ? <Loader2 className="w-3 h-3 animate-spin" /> : <Shuffle className="w-3 h-3" />}
                        </Button>
                      </div>
                    </div>
                    
                    {captionSuggestions.length === 0 ? (
                      <Button 
                        variant="outline" 
                        size="sm" 
                        onClick={() => loadCaptionSuggestions(selectedTheme, useAiCaptions, previewVideo?.hero_ref, previewVideo?.movement_type)}
                        disabled={isLoadingSuggestions}
                        className="w-full border-pink-500/30 text-pink-300 hover:bg-pink-500/10"
                      >
                        {isLoadingSuggestions ? (
                          <><Loader2 className="w-3 h-3 mr-2 animate-spin" />Generating...</>
                        ) : (
                          <><Shuffle className="w-3 h-3 mr-2" />{useAiCaptions ? 'Generate AI Captions' : 'Get Caption Ideas'}</>
                        )}
                      </Button>
                    ) : (
                      <div className="grid grid-cols-1 gap-2 max-h-[200px] overflow-y-auto">
                        {captionSuggestions.map((suggestion) => (
                          <button
                            key={suggestion.id}
                            onClick={() => setCaptionText(suggestion.formatted)}
                            className="p-2 text-left bg-black/30 hover:bg-pink-500/20 border border-white/10 hover:border-pink-500/40 rounded text-[11px] leading-relaxed transition-all"
                          >
                            <div className="text-white/90 whitespace-pre-line">{suggestion.formatted}</div>
                            <div className="flex items-center gap-2 mt-1.5 text-[9px]">
                              {suggestion.pattern && (
                                <span className="text-purple-400/70">Pattern {suggestion.pattern}</span>
                              )}
                              {suggestion.emotional_mode && (
                                <span className="text-cyan-400/70 capitalize">{suggestion.emotional_mode.replace(/_/g, ' ')}</span>
                              )}
                              {suggestion.theme && (
                                <span className="text-pink-400/70 capitalize">{suggestion.theme.replace("_", " ")}</span>
                              )}
                            </div>
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                  
                  <div>
                    <Label className="text-sm font-medium">Caption Text</Label>
                    <p className="text-xs text-muted-foreground mb-2">Edit as needed. One line per row.</p>
                    <textarea 
                      value={captionText}
                      onChange={(e) => {
                        setCaptionText(e.target.value);
                      }}
                      placeholder={"Honest opinion?\nI'm 5'2\" and 90 pounds.\nAm I too skinny?"}
                      className="w-full bg-black/40 border border-white/20 rounded-md p-3 min-h-[100px] text-sm text-white placeholder:text-white/40 focus:outline-none focus:ring-2 focus:ring-pink-500"
                      style={{ pointerEvents: 'auto' }}
                    />
                  </div>
                  
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <Label className="text-sm font-medium">Position</Label>
                      <select 
                        value={captionPosition} 
                        onChange={(e) => setCaptionPosition(e.target.value)}
                        className="w-full mt-1 bg-black/40 border border-white/20 rounded-md p-2 text-sm text-white"
                      >
                        <option value="top">Top</option>
                        <option value="center">Center</option>
                        <option value="bottom">Bottom</option>
                      </select>
                    </div>
                    
                    <div>
                      <Label className="text-sm font-medium">Font Size</Label>
                      <select 
                        value={captionFontSize} 
                        onChange={(e) => setCaptionFontSize(parseInt(e.target.value))}
                        className="w-full mt-1 bg-black/40 border border-white/20 rounded-md p-2 text-sm text-white"
                      >
                        <option value="18">XS (18px)</option>
                        <option value="20">Small (20px)</option>
                        <option value="24">Medium (24px)</option>
                        <option value="28">Large (28px)</option>
                        <option value="32">XL (32px)</option>
                      </select>
                    </div>
                  </div>
                  
                  <div className="flex gap-2 pt-2">
                    <button 
                      type="button"
                      className="flex-1 px-4 py-2 border border-white/20 rounded-md text-sm hover:bg-white/10"
                      onClick={() => { setShowCaptionForm(false); setCaptionText(""); }}
                    >
                      Cancel
                    </button>
                    <button 
                      type="button"
                      className={`flex-1 px-4 py-2 rounded-md text-sm font-medium flex items-center justify-center gap-2 ${captionText.trim() ? 'bg-pink-600 hover:bg-pink-500 text-white' : 'bg-gray-600 text-gray-400 cursor-not-allowed'}`}
                      onClick={() => {
                        console.log("Button clicked!", { captionText, isAddingCaption });
                        handleAddCaption();
                      }}
                      disabled={isAddingCaption || !captionText.trim()}
                    >
                      {isAddingCaption ? (
                        <>
                          <Loader2 className="w-4 h-4 animate-spin" />
                          Processing...
                        </>
                      ) : (
                        <>
                          <Type className="w-4 h-4" />
                          Apply Caption
                        </>
                      )}
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>

      <Dialog open={twitterDialogOpen} onOpenChange={(open) => {
        if (!open) {
          setTwitterDialogOpen(false);
          setTwitterVideoToShare(null);
          setTweetText("");
          setComposedPreview("");
        }
      }}>
        <DialogContent className="glass-panel border-white/10 text-foreground sm:max-w-[550px]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Twitter className="w-5 h-5 text-blue-400" />
              Share on Twitter
            </DialogTitle>
            <DialogDescription className="text-muted-foreground">
              {twitterMediaReady 
                ? "Post video with caption, Fanvue link, and hashtags." 
                : "Video upload not ready. Configure OAuth 1.0a credentials in Secrets."}
            </DialogDescription>
          </DialogHeader>
          
          {twitterVideoToShare && (
            <div className="py-4 space-y-4">
              <div className="flex gap-4 items-start">
                <video 
                  src={`${apiBase}/micro_loop/video/captioned/${twitterVideoToShare.filename}`}
                  className="w-20 h-32 object-cover rounded-md border border-white/10 flex-shrink-0"
                  muted
                  loop
                  autoPlay
                  playsInline
                />
                <div className="flex-1 min-w-0 overflow-hidden space-y-2">
                  <p className="text-sm font-medium truncate" title={twitterVideoToShare.filename}>{twitterVideoToShare.filename}</p>
                  <div className="flex items-center gap-3">
                    <label className="flex items-center gap-2 text-xs">
                      <input 
                        type="checkbox" 
                        checked={includeCTA} 
                        onChange={(e) => {
                          setIncludeCTA(e.target.checked);
                          loadComposedPreview(tweetText);
                        }}
                        className="rounded"
                      />
                      Fanvue Link
                    </label>
                    <label className="flex items-center gap-2 text-xs">
                      <input 
                        type="checkbox" 
                        checked={includeHashtags} 
                        onChange={(e) => {
                          setIncludeHashtags(e.target.checked);
                          loadComposedPreview(tweetText);
                        }}
                        className="rounded"
                      />
                      Hashtags
                    </label>
                  </div>
                  <a 
                    href={`${apiBase}/micro_loop/video/captioned/${twitterVideoToShare.filename}`}
                    download={twitterVideoToShare.filename}
                    className="inline-flex items-center gap-1 px-2 py-1 bg-pink-600 hover:bg-pink-500 rounded text-[10px] font-medium"
                  >
                    <Download className="w-3 h-3" />
                    Download
                  </a>
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label className="text-sm font-medium">Caption</Label>
                  <Button
                    size="sm"
                    variant="outline"
                    className="h-7 text-xs border-purple-500/50 hover:bg-purple-500/20"
                    onClick={async () => {
                      setIsLoadingSuggestions(true);
                      try {
                        const videoInfluencer = twitterVideoToShare?.filename.includes('starbright') ? 'starbright_monroe' : 
                                                twitterVideoToShare?.filename.includes('luna') ? 'luna_vale' : selectedInfluencer;
                        const response = await fetch(`${apiBase}/micro_loop/generate_caption?count=3&influencer=${videoInfluencer}`);
                        if (response.ok) {
                          const data = await response.json();
                          const captions = data.suggestions || data.captions || [];
                          if (captions.length > 0) {
                            const caption = captions[0].formatted || captions[0].lines?.join(' ') || '';
                            setTweetText(caption);
                            loadComposedPreview(caption);
                            toast({ title: "Caption generated!", description: "AI caption added to your tweet." });
                          }
                        }
                      } catch (err) {
                        console.error("Failed to generate caption:", err);
                        toast({ title: "Failed to generate caption", variant: "destructive" });
                      } finally {
                        setIsLoadingSuggestions(false);
                      }
                    }}
                    disabled={isLoadingSuggestions}
                  >
                    {isLoadingSuggestions ? (
                      <><Loader2 className="w-3 h-3 mr-1 animate-spin" />Generating...</>
                    ) : (
                      <><Sparkles className="w-3 h-3 mr-1" />AI Caption</>
                    )}
                  </Button>
                </div>
                <Textarea
                  value={tweetText}
                  onChange={(e) => {
                    setTweetText(e.target.value);
                    loadComposedPreview(e.target.value);
                  }}
                  placeholder="Enter your tweet caption..."
                  className="min-h-[60px] bg-black/20 border-white/10 resize-none text-sm"
                />
              </div>

              <div className="space-y-2 p-3 bg-purple-900/20 border border-purple-500/30 rounded-md">
                <div className="flex items-center justify-between">
                  <Label className="text-sm font-medium flex items-center gap-2">
                    <Music className="w-4 h-4 text-purple-400" />
                    Background Music
                  </Label>
                  <label className="flex items-center gap-2 text-xs">
                    <input 
                      type="checkbox" 
                      checked={includeMusic} 
                      onChange={(e) => setIncludeMusic(e.target.checked)}
                      className="rounded"
                    />
                    Add music
                  </label>
                </div>
                
                {includeMusic && (
                  <div className="space-y-2 pt-2">
                    {musicTracks.length === 0 ? (
                      <div className="space-y-2">
                        <p className="text-xs text-muted-foreground">
                          No music tracks yet. Upload royalty-free tracks below.
                        </p>
                        <input
                          type="file"
                          accept="audio/*"
                          onChange={async (e) => {
                            const file = e.target.files?.[0];
                            if (!file) return;
                            const formData = new FormData();
                            formData.append("file", file);
                            const title = file.name.replace(/\.[^/.]+$/, "").replace(/_/g, " ");
                            const params = new URLSearchParams({
                              title,
                              mood: "chill",
                              tempo: "medium", 
                              genre: "lofi"
                            });
                            try {
                              const res = await fetch(`${apiBase}/api/music/upload?${params}`, {
                                method: "POST",
                                body: formData
                              });
                              if (res.ok) {
                                await loadMusicTracks();
                                toast({ title: "Track uploaded!", description: title });
                              }
                            } catch (err) {
                              console.error("Upload failed:", err);
                            }
                            e.target.value = "";
                          }}
                          className="block w-full text-xs file:mr-2 file:py-1 file:px-2 file:rounded file:border-0 file:text-xs file:bg-purple-600 file:text-white hover:file:bg-purple-500"
                        />
                        <div className="mt-2 p-2 bg-black/30 rounded text-[10px]">
                          <p className="font-medium text-purple-300 mb-1">Curated Picks for Starbright:</p>
                          <div className="space-y-0.5 text-muted-foreground">
                            <p>Chill: <a href="https://pixabay.com/music/beats-chill-vibes-196879/" target="_blank" className="text-purple-400 underline">Chill Vibes</a> | <a href="https://pixabay.com/music/beats-lofi-chill-140858/" target="_blank" className="text-purple-400 underline">Lofi Chill</a></p>
                            <p>Sensual: <a href="https://pixabay.com/music/beats-slow-and-easy-168654/" target="_blank" className="text-purple-400 underline">Slow & Easy</a> | <a href="https://pixabay.com/music/beats-deep-chill-196889/" target="_blank" className="text-purple-400 underline">Deep Chill</a></p>
                            <p>Upbeat: <a href="https://pixabay.com/music/beats-summer-vibes-194447/" target="_blank" className="text-purple-400 underline">Summer Vibes</a> | <a href="https://mixkit.co/free-stock-music/tag/chill/" target="_blank" className="text-purple-400 underline">More on Mixkit</a></p>
                          </div>
                          <p className="mt-1 text-[9px] opacity-70">Click to download, then upload above</p>
                        </div>
                      </div>
                    ) : (
                      <>
                        <div className="flex gap-2">
                          <select
                            value={selectedMusic || ""}
                            onChange={(e) => setSelectedMusic(e.target.value || null)}
                            className="flex-1 px-2 py-1.5 bg-black/40 border border-white/10 rounded text-xs"
                          >
                            <option value="">Select a track...</option>
                            {musicTracks.map((track) => (
                              <option key={track.id} value={track.id}>
                                {track.title} ({track.mood}, {track.genre})
                              </option>
                            ))}
                          </select>
                          <Button
                            size="sm"
                            variant="outline"
                            className="h-7 text-xs border-purple-500/50 hover:bg-purple-500/20"
                            onClick={() => twitterVideoToShare && getMusicRecommendation(twitterVideoToShare.filename, tweetText)}
                            disabled={isLoadingMusicRec}
                          >
                            {isLoadingMusicRec ? (
                              <Loader2 className="w-3 h-3 animate-spin" />
                            ) : (
                              <>
                                <Sparkles className="w-3 h-3 mr-1" />
                                AI Pick
                              </>
                            )}
                          </Button>
                        </div>
                        {musicRecommendation && (
                          <p className="text-[10px] text-purple-300">
                            AI: {musicRecommendation.reasoning}
                          </p>
                        )}
                        <div className="pt-1">
                          <input
                            type="file"
                            accept="audio/*"
                            onChange={async (e) => {
                              const file = e.target.files?.[0];
                              if (!file) return;
                              const formData = new FormData();
                              formData.append("file", file);
                              const title = file.name.replace(/\.[^/.]+$/, "").replace(/_/g, " ");
                              const params = new URLSearchParams({ title, mood: "chill", tempo: "medium", genre: "lofi" });
                              try {
                                const res = await fetch(`${apiBase}/api/music/upload?${params}`, { method: "POST", body: formData });
                                if (res.ok) { await loadMusicTracks(); toast({ title: "Track uploaded!", description: title }); }
                              } catch (err) { console.error("Upload failed:", err); }
                              e.target.value = "";
                            }}
                            className="block w-full text-[10px] file:mr-2 file:py-0.5 file:px-2 file:rounded file:border-0 file:text-[10px] file:bg-purple-600/50 file:text-white hover:file:bg-purple-500/50"
                          />
                        </div>
                      </>
                    )}
                  </div>
                )}
              </div>

              {composedPreview && (
                <div className="space-y-2">
                  <Label className="text-sm font-medium text-muted-foreground">Preview (full tweet)</Label>
                  <div className="p-3 bg-black/30 border border-white/10 rounded-md text-xs whitespace-pre-wrap font-mono">
                    {composedPreview}
                  </div>
                  <div className="flex justify-between text-[10px] text-muted-foreground">
                    <span>Characters: {composedPreview.length}/280</span>
                    {twitterConnected && (
                      <span className="text-green-400 flex items-center gap-1">
                        <CheckCircle className="w-3 h-3" />
                        @Starbright2003
                      </span>
                    )}
                  </div>
                </div>
              )}

              {!twitterMediaReady && (
                <div className="p-3 bg-yellow-900/30 border border-yellow-500/30 rounded-md">
                  <p className="text-xs text-yellow-300">
                    Video upload requires OAuth 1.0a credentials. Add TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, and TWITTER_ACCESS_TOKEN_SECRET to Secrets.
                  </p>
                </div>
              )}

              <div className="flex gap-2 pt-2">
                <Button
                  variant="outline"
                  className="flex-1 border-white/20"
                  onClick={() => setTwitterDialogOpen(false)}
                >
                  Cancel
                </Button>
                <Button
                  className="flex-1 bg-blue-500 hover:bg-blue-400"
                  onClick={handlePostTweet}
                  disabled={isPostingTweet || !tweetText.trim() || !twitterMediaReady}
                >
                  {isPostingTweet ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Posting...
                    </>
                  ) : (
                    <>
                      <Send className="w-4 h-4 mr-2" />
                      Post with Video
                    </>
                  )}
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      <Dialog open={uploadDialogOpen} onOpenChange={setUploadDialogOpen}>
        <DialogContent className="max-w-lg bg-black/95 border-white/10">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Upload className="w-5 h-5 text-purple-400" />
              Upload Hero Image
            </DialogTitle>
            <DialogDescription>
              Upload a hero reference image. AI will analyze and auto-label it.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div className="space-y-2">
              <Label className="text-sm">Character</Label>
              <Select value={uploadInfluencer} onValueChange={setUploadInfluencer}>
                <SelectTrigger className="bg-black/40 border-white/10">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {INFLUENCERS.map(inf => (
                    <SelectItem key={inf.id} value={inf.id}>{inf.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label className="text-sm">Select Image</Label>
              <Input
                type="file"
                accept="image/*"
                onChange={handleFileSelect}
                className="bg-black/40 border-white/10 file:bg-purple-600 file:text-white file:border-0 file:rounded file:px-3 file:py-1 file:mr-3 file:cursor-pointer"
              />
            </div>

            {uploadFile && (
              <div className="flex gap-4">
                <div className="w-24 h-32 rounded-lg overflow-hidden border border-white/20 flex-shrink-0">
                  <img 
                    src={URL.createObjectURL(uploadFile)} 
                    alt="Preview" 
                    className="w-full h-full object-cover"
                  />
                </div>
                
                <div className="flex-1 space-y-2">
                  {isAnalyzing ? (
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>Analyzing image...</span>
                    </div>
                  ) : analysisResult ? (
                    <div className="space-y-2">
                      <div className="flex items-center gap-2 text-sm text-green-400">
                        <Sparkles className="w-4 h-4" />
                        <span>AI Analysis Complete</span>
                      </div>
                      <div className="grid grid-cols-2 gap-1 text-xs">
                        <span className="text-muted-foreground">Outfit:</span>
                        <span className="text-purple-300">{analysisResult.outfit}</span>
                        <span className="text-muted-foreground">Setting:</span>
                        <span className="text-cyan-300">{analysisResult.setting}</span>
                        <span className="text-muted-foreground">Mood:</span>
                        <span className="text-pink-300">{analysisResult.mood}</span>
                      </div>
                      {analysisResult.description && (
                        <p className="text-[10px] text-muted-foreground italic">
                          {analysisResult.description}
                        </p>
                      )}
                    </div>
                  ) : (
                    <p className="text-xs text-muted-foreground">
                      Select an image to analyze
                    </p>
                  )}
                </div>
              </div>
            )}

            {uploadFile && !isAnalyzing && (
              <div className="space-y-2">
                <Label className="text-sm">Filename (auto-generated, editable)</Label>
                <Input
                  value={customFilename}
                  onChange={(e) => setCustomFilename(e.target.value)}
                  placeholder="e.g., starbright_beach_bikini_sunset"
                  className="bg-black/40 border-white/10 font-mono text-sm"
                />
                <p className="text-[10px] text-muted-foreground">
                  Format: {"{persona}_{setting}_{outfit}_{details}"}
                </p>
              </div>
            )}
          </div>

          <DialogFooter className="gap-2">
            <Button
              variant="outline"
              onClick={() => setUploadDialogOpen(false)}
              className="border-white/20"
            >
              Cancel
            </Button>
            <Button
              onClick={handleUploadHero}
              disabled={!uploadFile || isUploading || isAnalyzing}
              className="bg-purple-600 hover:bg-purple-500"
            >
              {isUploading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Uploading...
                </>
              ) : (
                <>
                  <Upload className="w-4 h-4 mr-2" />
                  Upload & Save
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
