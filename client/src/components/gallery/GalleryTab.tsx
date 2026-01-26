import { useState, useEffect, useCallback } from "react";
import { Image as ImageIcon, RefreshCw, Loader2, Check, X, Sparkles, Wand2, Trash2, Download, Video, Send } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useToast } from "@/hooks/use-toast";
import { ImageModal } from "./ImageModal";
import { GalleryImage, QualityScore, LogEntryType, INFLUENCERS, getApiBase } from "./types";

interface GalleryTabProps {
  backendUrl: string;
  useLiveMode: boolean;
  addLog: (agent: string, message: string, type: LogEntryType) => void;
}

export function GalleryTab({ backendUrl, useLiveMode, addLog }: GalleryTabProps) {
  const { toast } = useToast();
  const [images, setImages] = useState<GalleryImage[]>([]);
  const [approvalStatus, setApprovalStatus] = useState<Record<string, string>>({});
  const [selectedInfluencer, setSelectedInfluencer] = useState("starbright_monroe");
  const [filter, setFilter] = useState("all");
  const [sourceFilter, setSourceFilter] = useState("all");
  const [isLoading, setIsLoading] = useState(false);
  const [analyzingImage, setAnalyzingImage] = useState<string | null>(null);
  const [swappingImage, setSwappingImage] = useState<string | null>(null);
  const [generatingLoop, setGeneratingLoop] = useState<string | null>(null);
  const [postingToX, setPostingToX] = useState<string | null>(null);
  const [scores, setScores] = useState<Record<string, QualityScore>>({});
  
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedImageIndex, setSelectedImageIndex] = useState(0);

  const apiBase = getApiBase(backendUrl);

  const loadImages = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`${apiBase}/gallery/images/${selectedInfluencer}?source=${sourceFilter}`);
      if (!response.ok) throw new Error("Failed to load images");
      
      const data = await response.json();
      setImages(data.images || []);
      setApprovalStatus(data.approval_status || {});
      addLog("GALLERY", `Loaded ${data.images?.length || 0} images for ${selectedInfluencer}`, "info");
    } catch (error: any) {
      toast({
        title: "Failed to load gallery",
        description: error.message,
        variant: "destructive"
      });
    } finally {
      setIsLoading(false);
    }
  }, [apiBase, selectedInfluencer, sourceFilter, addLog, toast]);

  useEffect(() => {
    loadImages();
  }, [selectedInfluencer, loadImages]);

  const handleApprove = async (path: string) => {
    try {
      const influencerName = selectedInfluencer === "luna_vale" ? "Luna Vale" : "Starbright Monroe";
      const response = await fetch(
        `${apiBase}/workflow/approve?image_path=${encodeURIComponent(path)}&influencer=${encodeURIComponent(influencerName)}`
      );
      const data = await response.json();
      
      if (data.status === "approved") {
        setApprovalStatus(prev => ({ 
          ...prev, 
          [path]: data.final_path ? "final" : "approved" 
        }));
        addLog("GALLERY", `Approved: ${path.split('/').pop()}`, "success");
        toast({ title: "Image approved", description: "Moved to final folder" });
      }
    } catch (error: any) {
      toast({ title: "Approval failed", description: error.message, variant: "destructive" });
    }
  };

  const handleReject = async (path: string) => {
    try {
      const influencerName = selectedInfluencer === "luna_vale" ? "Luna Vale" : "Starbright Monroe";
      const response = await fetch(
        `${apiBase}/workflow/reject?image_path=${encodeURIComponent(path)}&influencer=${encodeURIComponent(influencerName)}`
      );
      const data = await response.json();
      
      if (data.status === "rejected") {
        addLog("GALLERY", `Rejected and archived: ${path.split('/').pop()}`, "warning");
        toast({ title: "Image rejected", description: "Moved to archive" });
        await loadImages();
      }
    } catch (error: any) {
      toast({ title: "Rejection failed", description: error.message, variant: "destructive" });
    }
  };

  const handleAnalyze = async (path: string) => {
    setAnalyzingImage(path);
    try {
      const influencerName = selectedInfluencer === "luna_vale" ? "Luna Vale" : "Starbright Monroe";
      const response = await fetch(
        `${apiBase}/analyze_image?image_path=${encodeURIComponent(path)}&influencer=${encodeURIComponent(influencerName)}`
      );
      const data = await response.json();
      
      if (data.analyzed && data.score) {
        const s = data.score;
        setScores(prev => ({ ...prev, [path]: s }));
        const breakdown = `Overall: ${(s.overall * 100).toFixed(0)}% | Skin: ${(s.skin_realism * 100).toFixed(0)}% | Face: ${(s.face_consistency * 100).toFixed(0)}% | Light: ${(s.lighting_quality * 100).toFixed(0)}% | Comp: ${(s.composition * 100).toFixed(0)}%`;
        addLog("QUALITY", breakdown, "info");
        toast({ 
          title: `Quality: ${(s.overall * 100).toFixed(0)}%`, 
          description: `S:${(s.skin_realism * 100).toFixed(0)} F:${(s.face_consistency * 100).toFixed(0)} L:${(s.lighting_quality * 100).toFixed(0)} C:${(s.composition * 100).toFixed(0)}`
        });
      }
    } catch (error: any) {
      toast({ title: "Analysis failed", description: error.message, variant: "destructive" });
    } finally {
      setAnalyzingImage(null);
    }
  };

  const handleFaceSwap = async (path: string) => {
    setSwappingImage(path);
    try {
      const influencerName = selectedInfluencer === "luna_vale" ? "Luna Vale" : "Starbright Monroe";
      addLog("FACE_SWAP", `Starting face swap for ${path.split('/').pop()}...`, "info");
      
      const response = await fetch(
        `${apiBase}/face_swap?image_path=${encodeURIComponent(path)}&influencer=${encodeURIComponent(influencerName)}`
      );
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Server error: ${response.status}`);
      }
      
      const data = await response.json();
      
      if (data.status === "success") {
        addLog("FACE_SWAP", `Face swap complete: ${data.swapped_image_path?.split('/').pop()}`, "success");
        toast({ 
          title: "Face swap complete", 
          description: "New image added to gallery"
        });
        await loadImages();
      } else {
        throw new Error(data.error || "Face swap failed");
      }
    } catch (error: any) {
      addLog("FACE_SWAP", `Face swap failed: ${error.message}`, "error");
      toast({ title: "Face swap failed", description: error.message, variant: "destructive" });
    } finally {
      setSwappingImage(null);
    }
  };

  const handleDelete = async (path: string, isFinal: boolean = false) => {
    if (!confirm(`Are you sure you want to delete this image? It will be moved to archives and can be recovered.`)) {
      return;
    }

    try {
      const contentType = isFinal ? "final" : "raw";
      const response = await fetch(
        `${apiBase}/content/delete?file_path=${encodeURIComponent(path)}&content_type=${contentType}&influencer=${selectedInfluencer}`,
        { method: "DELETE" }
      );

      const data = await response.json();

      if (data.status === "deleted") {
        addLog("GALLERY", `Deleted: ${path.split('/').pop()}`, "success");
        toast({
          title: "Deleted successfully",
          description: "Image moved to archives (recoverable)"
        });
        await loadImages();
      } else {
        throw new Error(data.detail || "Delete failed");
      }
    } catch (error: any) {
      addLog("GALLERY", `Delete failed: ${error.message}`, "error");
      toast({
        title: "Delete failed",
        description: error.message,
        variant: "destructive"
      });
    }
  };

  const handleCreateLoop = async (path: string) => {
    setGeneratingLoop(path);
    try {
      addLog("LOOPS", `Starting microloop generation for ${path.split('/').pop()}...`, "info");
      
      const response = await fetch(
        `${apiBase}/micro_loop/generate?hero_image_path=${encodeURIComponent(path)}&influencer=${selectedInfluencer}`,
        { method: "POST" }
      );
      
      const data = await response.json();
      
      if (data.status === "success") {
        addLog("LOOPS", `Microloop generated: ${data.output_path?.split('/').pop() || 'video'}`, "success");
        toast({ 
          title: "Microloop generated!", 
          description: `Movement: ${data.movement_type || 'micro_sway'}. Check the Loops tab.`
        });
      } else {
        throw new Error(data.error || "Generation failed");
      }
    } catch (error: any) {
      addLog("LOOPS", `Microloop generation failed: ${error.message}`, "error");
      toast({ title: "Generation failed", description: error.message, variant: "destructive" });
    } finally {
      setGeneratingLoop(null);
    }
  };

  const handlePostToX = async (path: string) => {
    setPostingToX(path);
    try {
      addLog("TWITTER", `Posting to X: ${path.split('/').pop()}...`, "info");
      
      const response = await fetch(
        `${apiBase}/workflow/auto-post?image_path=${encodeURIComponent(path)}&influencer=${selectedInfluencer}`,
        { method: "POST" }
      );
      
      const data = await response.json();
      
      if (data.status === "success") {
        addLog("TWITTER", `Posted to X: ${data.tweet_url}`, "success");
        toast({ 
          title: "Posted to X!", 
          description: data.tweet_url
        });
      } else {
        throw new Error(data.error || "Post failed");
      }
    } catch (error: any) {
      addLog("TWITTER", `Post to X failed: ${error.message}`, "error");
      toast({ title: "Post failed", description: error.message, variant: "destructive" });
    } finally {
      setPostingToX(null);
    }
  };

  const getImageStatus = (path: string) => approvalStatus[path] || "pending";

  const handleDownloadSingle = (path: string) => {
    const downloadUrl = `${apiBase}/gallery/download/${path}`;
    window.open(downloadUrl, '_blank');
  };

  const handleDownloadAll = () => {
    const downloadUrl = `${apiBase}/gallery/download-all/${selectedInfluencer}?source=${sourceFilter}`;
    window.open(downloadUrl, '_blank');
    toast({
      title: "Download Started",
      description: "Preparing ZIP file with all content..."
    });
  };

  const filteredImages = images.filter(img => {
    if (filter === "all") return true;
    const status = getImageStatus(img.path);
    if (filter === "pending") return status === "pending";
    if (filter === "approved") return status === "approved" || status === "final";
    if (filter === "rejected") return status === "rejected";
    return true;
  });

  const stats = {
    total: images.length,
    pending: images.filter(img => getImageStatus(img.path) === "pending").length,
    approved: images.filter(img => ["approved", "final"].includes(getImageStatus(img.path))).length,
    rejected: images.filter(img => getImageStatus(img.path) === "rejected").length
  };

  const openModal = (index: number) => {
    setSelectedImageIndex(index);
    setModalOpen(true);
  };

  const navigateModal = (direction: number) => {
    const newIndex = selectedImageIndex + direction;
    if (newIndex >= 0 && newIndex < filteredImages.length) {
      setSelectedImageIndex(newIndex);
    }
  };

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
            onClick={loadImages}
            disabled={isLoading}
            className="border-white/10"
          >
            <RefreshCw className={`w-4 h-4 mr-1 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
        
        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={handleDownloadAll}
            disabled={filteredImages.length === 0}
            className="border-white/10 text-green-400 hover:text-green-300"
          >
            <Download className="w-4 h-4 mr-1" />
            Download All ({filteredImages.length})
          </Button>
          <div className="flex items-center gap-2 text-xs">
            <span className="text-muted-foreground">{stats.total} total</span>
            <span className="text-yellow-400">{stats.pending} pending</span>
            <span className="text-green-400">{stats.approved} approved</span>
          </div>
        </div>
      </div>
      
      <div className="flex gap-2 mb-4 items-center">
        <Select value={sourceFilter} onValueChange={setSourceFilter}>
          <SelectTrigger className="w-32 bg-black/20 border-white/10 h-8 text-xs">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Sources</SelectItem>
            <SelectItem value="research">Research</SelectItem>
            <SelectItem value="generated">Generated</SelectItem>
            <SelectItem value="raw">Raw</SelectItem>
            <SelectItem value="final">Final</SelectItem>
          </SelectContent>
        </Select>
        
        <div className="h-4 w-px bg-white/20" />
        
        {["all", "pending", "approved", "rejected"].map(f => (
          <Button
            key={f}
            variant={filter === f ? "default" : "ghost"}
            size="sm"
            onClick={() => setFilter(f)}
            className={filter === f ? "" : "text-muted-foreground hover:text-white"}
          >
            {f.charAt(0).toUpperCase() + f.slice(1)}
          </Button>
        ))}
      </div>
      
      <ScrollArea className="flex-1">
        {isLoading ? (
          <div className="flex items-center justify-center h-40">
            <Loader2 className="w-8 h-8 animate-spin text-primary" />
          </div>
        ) : filteredImages.length === 0 ? (
          <div className="text-center py-12 text-muted-foreground">
            <ImageIcon className="w-10 h-10 mx-auto mb-3 opacity-30" />
            <p>{filter === "all" ? "No images generated yet" : `No ${filter} images`}</p>
          </div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {filteredImages.map((img, idx) => {
              const status = getImageStatus(img.path);
              const score = scores[img.path];
              const imageUrl = `${apiBase}/gallery/image/${img.path}`;
              
              return (
                <div 
                  key={img.path}
                  className={`relative group rounded-lg overflow-hidden border transition-all hover:scale-[1.02] cursor-pointer ${
                    status === "approved" || status === "final" ? "border-green-500/50" :
                    status === "rejected" ? "border-red-500/50 opacity-60" :
                    "border-white/10"
                  }`}
                  onClick={() => openModal(idx)}
                >
                  <img 
                    src={imageUrl} 
                    alt={img.filename}
                    className="w-full aspect-square object-cover"
                    loading="lazy"
                  />
                  
                  {status !== "pending" && (
                    <div className={`absolute top-2 right-2 px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                      status === "final" ? "bg-purple-500/90" :
                      status === "approved" ? "bg-green-500/90" :
                      "bg-red-500/90"
                    }`}>
                      {status}
                    </div>
                  )}
                  
                  <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity">
                    <div className="absolute bottom-0 left-0 right-0 p-2">
                      <p className="text-[10px] text-white/80 truncate mb-2">{img.filename}</p>
                      
                      {status === "pending" && (
                        <div className="flex gap-1" onClick={e => e.stopPropagation()}>
                          <Button 
                            size="sm" 
                            className="flex-1 h-7 text-xs bg-green-600/80 hover:bg-green-600"
                            onClick={() => handleApprove(img.path)}
                          >
                            <Check className="w-3 h-3" />
                          </Button>
                          <Button 
                            size="sm" 
                            className="flex-1 h-7 text-xs bg-red-600/80 hover:bg-red-600"
                            onClick={() => handleReject(img.path)}
                          >
                            <X className="w-3 h-3" />
                          </Button>
                          <Button 
                            size="sm" 
                            className="h-7 text-xs bg-purple-600/80 hover:bg-purple-600"
                            onClick={() => handleFaceSwap(img.path)}
                            disabled={swappingImage === img.path}
                            title="Face Swap"
                          >
                            {swappingImage === img.path ? (
                              <Loader2 className="w-3 h-3 animate-spin" />
                            ) : (
                              <Wand2 className="w-3 h-3" />
                            )}
                          </Button>
                          <Button 
                            size="sm" 
                            className="h-7 text-xs bg-blue-600/80 hover:bg-blue-600"
                            onClick={() => handleAnalyze(img.path)}
                            disabled={analyzingImage === img.path}
                          >
                            {analyzingImage === img.path ? (
                              <Loader2 className="w-3 h-3 animate-spin" />
                            ) : (
                              <Sparkles className="w-3 h-3" />
                            )}
                          </Button>
                          <Button 
                            size="sm" 
                            className="h-7 w-7 p-0 bg-cyan-600/80 hover:bg-cyan-600"
                            onClick={() => handleCreateLoop(img.path)}
                            disabled={generatingLoop === img.path}
                            title="Create Microloop"
                          >
                            {generatingLoop === img.path ? (
                              <Loader2 className="w-3 h-3 animate-spin" />
                            ) : (
                              <Video className="w-3 h-3" />
                            )}
                          </Button>
                          <Button 
                            size="sm" 
                            variant="destructive"
                            className="h-7 w-7 p-0"
                            onClick={() => handleDelete(img.path, false)}
                            title="Delete"
                          >
                            <Trash2 className="w-3 h-3" />
                          </Button>
                          <Button 
                            size="sm" 
                            className="h-7 w-7 p-0 bg-emerald-600/80 hover:bg-emerald-600"
                            onClick={() => handleDownloadSingle(img.path)}
                            title="Download"
                          >
                            <Download className="w-3 h-3" />
                          </Button>
                        </div>
                      )}
                      
                      {(status === "approved" || status === "final") && (
                        <div className="flex flex-col gap-1" onClick={e => e.stopPropagation()}>
                          <div className="flex gap-1">
                            <Button 
                              size="sm" 
                              className="h-7 text-xs bg-blue-600/80 hover:bg-blue-600"
                              onClick={() => handlePostToX(img.path)}
                              disabled={postingToX === img.path}
                              title="Post to X"
                            >
                              {postingToX === img.path ? (
                                <Loader2 className="w-3 h-3 animate-spin mr-1" />
                              ) : (
                                <Send className="w-3 h-3 mr-1" />
                              )}
                              Post
                            </Button>
                            <Button 
                              size="sm" 
                              className="h-7 text-xs bg-cyan-600/80 hover:bg-cyan-600"
                              onClick={() => handleCreateLoop(img.path)}
                              disabled={generatingLoop === img.path}
                              title="Create Microloop"
                            >
                              {generatingLoop === img.path ? (
                                <Loader2 className="w-3 h-3 animate-spin mr-1" />
                              ) : (
                                <Video className="w-3 h-3 mr-1" />
                              )}
                              Loop
                            </Button>
                          </div>
                          <div className="flex gap-1">
                            <Button 
                              size="sm" 
                              className="h-7 text-xs bg-emerald-600/80 hover:bg-emerald-600"
                              onClick={() => handleDownloadSingle(img.path)}
                            >
                              <Download className="w-3 h-3 mr-1" />
                              Download
                            </Button>
                            <Button 
                              size="sm" 
                              variant="destructive"
                              className="h-7 text-xs"
                              onClick={() => handleDelete(img.path, status === "final")}
                            >
                              <Trash2 className="w-3 h-3 mr-1" />
                              Delete
                            </Button>
                          </div>
                        </div>
                      )}
                      
                      {score && (
                        <div className="mt-1 text-[10px]">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="font-medium">Overall</span>
                            <div className="flex-1 h-1.5 bg-white/20 rounded overflow-hidden">
                              <div 
                                className={`h-full ${score.overall >= 0.7 ? "bg-green-400" : score.overall >= 0.5 ? "bg-yellow-400" : "bg-red-400"}`}
                                style={{ width: `${score.overall * 100}%` }}
                              />
                            </div>
                            <span className={`font-bold ${score.overall >= 0.7 ? "text-green-400" : score.overall >= 0.5 ? "text-yellow-400" : "text-red-400"}`}>
                              {(score.overall * 100).toFixed(0)}%
                            </span>
                          </div>
                          <div className="flex gap-2 text-[8px]">
                            <span className={score.skin_realism >= 0.7 ? "text-green-400" : score.skin_realism >= 0.5 ? "text-yellow-400" : "text-red-400"}>
                              S:{(score.skin_realism * 100).toFixed(0)}
                            </span>
                            <span className={score.face_consistency >= 0.7 ? "text-green-400" : score.face_consistency >= 0.5 ? "text-yellow-400" : "text-red-400"}>
                              F:{(score.face_consistency * 100).toFixed(0)}
                            </span>
                            <span className={score.lighting_quality >= 0.7 ? "text-green-400" : score.lighting_quality >= 0.5 ? "text-yellow-400" : "text-red-400"}>
                              L:{(score.lighting_quality * 100).toFixed(0)}
                            </span>
                            <span className={score.composition >= 0.7 ? "text-green-400" : score.composition >= 0.5 ? "text-yellow-400" : "text-red-400"}>
                              C:{(score.composition * 100).toFixed(0)}
                            </span>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </ScrollArea>
      
      <ImageModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        image={filteredImages[selectedImageIndex] || null}
        images={filteredImages}
        currentIndex={selectedImageIndex}
        onNavigate={navigateModal}
        onApprove={handleApprove}
        onReject={handleReject}
        onPostToX={handlePostToX}
        approvalStatus={approvalStatus}
        backendUrl={backendUrl}
        selectedInfluencer={selectedInfluencer}
      />
    </div>
  );
}
