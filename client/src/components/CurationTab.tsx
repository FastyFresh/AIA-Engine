import { useState, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Loader2, Check, X, RefreshCw, Sparkles, AlertCircle, RotateCcw } from "lucide-react";
import { LogEntryType } from "@/components/gallery/types";

interface CurationImage {
  path: string;
  filename: string;
  url: string;
  status: string;
  score: number | null;
  recommendation: string | null;
  face_match: number | null;
  hair_match: number | null;
  body_match: number | null;
  issues: string[];
  notes?: string;
}

interface CurationStats {
  total: number;
  pending: number;
  approved: number;
  rejected: number;
  review: number;
  target: number;
}

interface CurationTabProps {
  backendUrl: string;
  addLog: (agent: string, message: string, type?: LogEntryType) => void;
}

export function CurationTab({ backendUrl, addLog }: CurationTabProps) {
  const [images, setImages] = useState<CurationImage[]>([]);
  const [stats, setStats] = useState<CurationStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [scoring, setScoring] = useState(false);
  const [scoringProgress, setScoringProgress] = useState({ current: 0, total: 0 });
  const [filter, setFilter] = useState<string>("all");
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      const [imagesRes, statsRes] = await Promise.all([
        fetch(`${backendUrl}/api/curation/images?persona=starbright&filter_status=${filter}`),
        fetch(`${backendUrl}/api/curation/stats?persona=starbright`)
      ]);
      
      if (imagesRes.ok) {
        const data = await imagesRes.json();
        setImages(data.images || []);
      }
      
      if (statsRes.ok) {
        const data = await statsRes.json();
        setStats(data);
      }
    } catch (error) {
      addLog("CURATION", `Error fetching curation data: ${error}`, "error");
    } finally {
      setLoading(false);
    }
  }, [backendUrl, filter, addLog]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const [resetting, setResetting] = useState(false);

  const resetAndRescore = async () => {
    setResetting(true);
    addLog("CURATION", "Resetting all scores for re-analysis...", "info");
    
    try {
      const res = await fetch(`${backendUrl}/api/curation/reset-scores?persona=starbright`, {
        method: "POST"
      });
      
      if (res.ok) {
        const result = await res.json();
        addLog("CURATION", `Reset ${result.reset} score files. Starting fresh analysis...`, "success");
        await fetchData();
        setResetting(false);
        scoreAllPending();
      }
    } catch (error) {
      addLog("CURATION", `Error resetting scores: ${error}`, "error");
      setResetting(false);
    }
  };

  const scoreAllPending = async () => {
    setScoring(true);
    await fetchData();
    const pendingImages = images.filter(img => !img.score);
    setScoringProgress({ current: 0, total: pendingImages.length });
    
    addLog("CURATION", `Starting quality scoring for ${pendingImages.length} images...`, "info");
    
    for (let i = 0; i < pendingImages.length; i++) {
      const img = pendingImages[i];
      try {
        const res = await fetch(`${backendUrl}/api/curation/score`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ image_path: img.path })
        });
        
        if (res.ok) {
          const result = await res.json();
          addLog("CURATION", `Scored ${img.filename}: ${result.score} (${result.recommendation})`, "info");
        }
      } catch (error) {
        addLog("CURATION", `Error scoring ${img.filename}: ${error}`, "error");
      }
      
      setScoringProgress({ current: i + 1, total: pendingImages.length });
    }
    
    setScoring(false);
    fetchData();
    addLog("CURATION", "Quality scoring complete!", "success");
  };

  const handleApprove = async (imagePath: string) => {
    setActionLoading(imagePath);
    try {
      const res = await fetch(`${backendUrl}/api/curation/approve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ image_path: imagePath })
      });
      
      if (res.ok) {
        addLog("CURATION", `Approved: ${imagePath.split("/").pop()}`, "success");
        fetchData();
      }
    } catch (error) {
      addLog("CURATION", `Error approving: ${error}`, "error");
    } finally {
      setActionLoading(null);
    }
  };

  const handleReject = async (imagePath: string, shouldDelete: boolean = false) => {
    setActionLoading(imagePath);
    try {
      const res = await fetch(`${backendUrl}/api/curation/reject`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ image_path: imagePath, delete: shouldDelete })
      });
      
      if (res.ok) {
        addLog("CURATION", `Rejected: ${imagePath.split("/").pop()}`, "success");
        fetchData();
      }
    } catch (error) {
      addLog("CURATION", `Error rejecting: ${error}`, "error");
    } finally {
      setActionLoading(null);
    }
  };

  const getScoreColor = (score: number | null) => {
    if (score === null) return "bg-gray-500";
    if (score >= 85) return "bg-green-500";
    if (score >= 60) return "bg-yellow-500";
    return "bg-red-500";
  };

  const getRecommendationBadge = (rec: string | null) => {
    if (!rec) return <Badge variant="outline">Not scored</Badge>;
    switch (rec) {
      case "APPROVE":
        return <Badge className="bg-green-600">APPROVE</Badge>;
      case "REVIEW":
        return <Badge className="bg-yellow-600">REVIEW</Badge>;
      case "REJECT":
        return <Badge className="bg-red-600">REJECT</Badge>;
      default:
        return <Badge variant="outline">{rec}</Badge>;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-bold flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-purple-400" />
            Dataset Curation
          </h3>
          <p className="text-sm text-muted-foreground">
            AI-powered quality scoring and manual curation for training dataset
          </p>
        </div>
        
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={fetchData}
            disabled={scoring || resetting}
          >
            <RefreshCw className="w-4 h-4 mr-1" />
            Refresh
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={resetAndRescore}
            disabled={scoring || resetting || images.length === 0}
            className="border-orange-500/50 text-orange-400 hover:bg-orange-500/10"
          >
            {resetting ? (
              <>
                <Loader2 className="w-4 h-4 mr-1 animate-spin" />
                Resetting...
              </>
            ) : (
              <>
                <RotateCcw className="w-4 h-4 mr-1" />
                Reset & Re-score All
              </>
            )}
          </Button>
          <Button
            size="sm"
            onClick={scoreAllPending}
            disabled={scoring || resetting || images.filter(img => !img.score).length === 0}
          >
            {scoring ? (
              <>
                <Loader2 className="w-4 h-4 mr-1 animate-spin" />
                Scoring {scoringProgress.current}/{scoringProgress.total}
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4 mr-1" />
                Score Pending Only
              </>
            )}
          </Button>
        </div>
      </div>

      {stats && (
        <div className="grid grid-cols-5 gap-3">
          <Card className="bg-black/30">
            <CardContent className="p-3 text-center">
              <div className="text-2xl font-bold">{stats.total}</div>
              <div className="text-xs text-muted-foreground">Total</div>
            </CardContent>
          </Card>
          <Card className="bg-black/30">
            <CardContent className="p-3 text-center">
              <div className="text-2xl font-bold text-gray-400">{stats.pending}</div>
              <div className="text-xs text-muted-foreground">Pending</div>
            </CardContent>
          </Card>
          <Card className="bg-black/30 border-green-500/30">
            <CardContent className="p-3 text-center">
              <div className="text-2xl font-bold text-green-400">{stats.approved}</div>
              <div className="text-xs text-muted-foreground">Approved</div>
            </CardContent>
          </Card>
          <Card className="bg-black/30 border-yellow-500/30">
            <CardContent className="p-3 text-center">
              <div className="text-2xl font-bold text-yellow-400">{stats.review}</div>
              <div className="text-xs text-muted-foreground">Review</div>
            </CardContent>
          </Card>
          <Card className="bg-black/30">
            <CardContent className="p-3 text-center">
              <div className="text-2xl font-bold text-green-400">{stats.approved}/{stats.target}</div>
              <div className="text-xs text-muted-foreground">Target</div>
              <Progress value={(stats.approved / stats.target) * 100} className="h-1 mt-1" />
            </CardContent>
          </Card>
        </div>
      )}

      {scoring && (
        <Card className="bg-purple-900/20 border-purple-500/30">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <Loader2 className="w-5 h-5 animate-spin text-purple-400" />
              <div className="flex-1">
                <div className="text-sm font-medium">
                  Scoring images with Grok Vision...
                </div>
                <Progress 
                  value={(scoringProgress.current / scoringProgress.total) * 100} 
                  className="h-2 mt-2" 
                />
              </div>
              <div className="text-sm text-muted-foreground">
                {scoringProgress.current} / {scoringProgress.total}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="flex gap-2 mb-4">
        {["all", "pending", "approved", "review"].map(f => (
          <Button
            key={f}
            variant={filter === f ? "default" : "outline"}
            size="sm"
            onClick={() => setFilter(f)}
          >
            {f.charAt(0).toUpperCase() + f.slice(1)}
          </Button>
        ))}
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 max-h-[500px] overflow-y-auto">
        {images.map((img) => (
          <Card key={img.path} className="bg-black/30 overflow-hidden">
            <div className="relative aspect-square">
              <img
                src={img.url}
                alt={img.filename}
                className="w-full h-full object-cover"
                onError={(e) => {
                  (e.target as HTMLImageElement).src = "/placeholder.png";
                }}
              />
              
              {img.score !== null && (
                <div className={`absolute top-2 left-2 px-2 py-1 rounded text-xs font-bold text-white ${getScoreColor(img.score)}`}>
                  {img.score}
                </div>
              )}
              
              <div className="absolute top-2 right-2">
                {getRecommendationBadge(img.recommendation)}
              </div>
              
              {img.status === "approved" && (
                <div className="absolute bottom-2 left-2 bg-green-600 rounded-full p-1">
                  <Check className="w-4 h-4" />
                </div>
              )}
            </div>
            
            <CardContent className="p-3">
              <div className="text-xs font-mono truncate mb-2" title={img.filename}>
                {img.filename}
              </div>
              
              {img.score !== null && (
                <div className="grid grid-cols-3 gap-1 text-xs mb-2">
                  <div title="Face Match">
                    <span className="text-muted-foreground">Face:</span> {img.face_match}
                  </div>
                  <div title="Hair Match">
                    <span className="text-muted-foreground">Hair:</span> {img.hair_match}
                  </div>
                  <div title="Body Match">
                    <span className="text-muted-foreground">Body:</span> {img.body_match}
                  </div>
                </div>
              )}
              
              {img.issues && img.issues.length > 0 && (
                <div className="text-xs text-red-400 mb-2 flex items-start gap-1">
                  <AlertCircle className="w-3 h-3 mt-0.5 flex-shrink-0" />
                  <span className="truncate" title={img.issues.join(", ")}>
                    {img.issues[0]}
                  </span>
                </div>
              )}
              
              {img.status !== "approved" && (
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    className="flex-1 h-7 text-xs border-green-600 text-green-400 hover:bg-green-600/20"
                    onClick={() => handleApprove(img.path)}
                    disabled={actionLoading === img.path}
                  >
                    {actionLoading === img.path ? (
                      <Loader2 className="w-3 h-3 animate-spin" />
                    ) : (
                      <Check className="w-3 h-3" />
                    )}
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    className="flex-1 h-7 text-xs border-red-600 text-red-400 hover:bg-red-600/20"
                    onClick={() => handleReject(img.path, true)}
                    disabled={actionLoading === img.path}
                  >
                    {actionLoading === img.path ? (
                      <Loader2 className="w-3 h-3 animate-spin" />
                    ) : (
                      <X className="w-3 h-3" />
                    )}
                  </Button>
                </div>
              )}
              
              {img.status === "approved" && (
                <div className="text-xs text-center text-green-400 font-medium">
                  Approved for Training
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
      
      {images.length === 0 && (
        <div className="text-center py-12 text-muted-foreground">
          No images found. Generate some variations first using the LoRA tab.
        </div>
      )}
    </div>
  );
}
