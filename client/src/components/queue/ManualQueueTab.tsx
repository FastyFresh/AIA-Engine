import { useState, useEffect, useCallback } from "react";
import {
  Instagram,
  Music2,
  Clock,
  CheckCircle2,
  Copy,
  ExternalLink,
  Loader2,
  RefreshCw,
  Image as ImageIcon
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useToast } from "@/hooks/use-toast";

interface QueueItem {
  item_id: string;
  platform: string;
  influencer_name: string;
  influencer_handle: string;
  image_path: string;
  caption: string;
  suggested_time: string;
  created_at: string;
  status: string;
  posted_at?: string;
  notes?: string;
}

interface QueueStats {
  total: number;
  pending: {
    instagram: number;
    tiktok: number;
    total: number;
  };
  posted: {
    instagram: number;
    tiktok: number;
    total: number;
  };
}

interface ManualQueueTabProps {
  backendUrl: string;
  useLiveMode: boolean;
  addLog: (agent: string, message: string, type: "info" | "success" | "error" | "warning") => void;
}

export function ManualQueueTab({ backendUrl, useLiveMode, addLog }: ManualQueueTabProps) {
  const { toast } = useToast();
  const [items, setItems] = useState<QueueItem[]>([]);
  const [stats, setStats] = useState<QueueStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [platform, setPlatform] = useState<string>("all");
  const [markingPosted, setMarkingPosted] = useState<string | null>(null);

  const getApiBase = useCallback(() => {
    if (backendUrl) return backendUrl.replace(/\/$/, "");
    return window.location.origin;
  }, [backendUrl]);

  const fetchQueue = useCallback(async () => {
    setLoading(true);
    try {
      const platformParam = platform !== "all" ? `&platform=${platform}_manual` : "";
      const response = await fetch(
        `${getApiBase()}/manual_queue?status=pending${platformParam}`
      );
      if (response.ok) {
        const data = await response.json();
        setItems(data.items || []);
      }
    } catch (error) {
      console.error("Failed to fetch queue:", error);
    } finally {
      setLoading(false);
    }
  }, [getApiBase, platform]);

  const fetchStats = useCallback(async () => {
    try {
      const response = await fetch(`${getApiBase()}/manual_queue/stats`);
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (error) {
      console.error("Failed to fetch stats:", error);
    }
  }, [getApiBase]);

  useEffect(() => {
    fetchQueue();
    fetchStats();
  }, [fetchQueue, fetchStats]);

  const markAsPosted = async (itemId: string) => {
    setMarkingPosted(itemId);
    try {
      const response = await fetch(
        `${getApiBase()}/manual_queue/mark_posted?item_id=${encodeURIComponent(itemId)}`,
        { method: "POST" }
      );
      if (response.ok) {
        addLog("QUEUE", `Marked ${itemId} as posted`, "success");
        toast({
          title: "Marked as Posted",
          description: "Item removed from pending queue",
        });
        fetchQueue();
        fetchStats();
      } else {
        throw new Error("Failed to mark as posted");
      }
    } catch (error) {
      addLog("QUEUE", `Failed to mark posted: ${error}`, "error");
      toast({
        title: "Error",
        description: "Failed to mark item as posted",
        variant: "destructive",
      });
    } finally {
      setMarkingPosted(null);
    }
  };

  const copyCaption = (caption: string) => {
    navigator.clipboard.writeText(caption);
    toast({
      title: "Copied!",
      description: "Caption copied to clipboard",
    });
  };

  const formatTime = (isoString: string) => {
    try {
      const date = new Date(isoString);
      return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    } catch {
      return isoString;
    }
  };

  const formatDate = (isoString: string) => {
    try {
      const date = new Date(isoString);
      return date.toLocaleDateString();
    } catch {
      return isoString;
    }
  };

  return (
    <div className="h-full flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h3 className="font-bold text-lg">Manual Posting Queue</h3>
          {stats && (
            <div className="flex gap-2">
              <Badge variant="outline" className="bg-pink-500/10 text-pink-400 border-pink-500/20">
                <Instagram className="w-3 h-3 mr-1" />
                {stats.pending.instagram} pending
              </Badge>
              <Badge variant="outline" className="bg-cyan-500/10 text-cyan-400 border-cyan-500/20">
                <Music2 className="w-3 h-3 mr-1" />
                {stats.pending.tiktok} pending
              </Badge>
            </div>
          )}
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => {
            fetchQueue();
            fetchStats();
          }}
          disabled={loading}
        >
          <RefreshCw className={`w-4 h-4 mr-2 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </Button>
      </div>

      <Tabs value={platform} onValueChange={setPlatform} className="flex-1 flex flex-col">
        <TabsList className="bg-black/40 border border-white/5 w-fit">
          <TabsTrigger value="all" className="text-xs font-mono">
            ALL
          </TabsTrigger>
          <TabsTrigger value="instagram" className="text-xs font-mono">
            <Instagram className="w-3 h-3 mr-1" />
            INSTAGRAM
          </TabsTrigger>
          <TabsTrigger value="tiktok" className="text-xs font-mono">
            <Music2 className="w-3 h-3 mr-1" />
            TIKTOK
          </TabsTrigger>
        </TabsList>

        <div className="flex-1 overflow-y-auto mt-4">
          {loading ? (
            <div className="flex items-center justify-center h-32">
              <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
            </div>
          ) : items.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-32 text-muted-foreground">
              <CheckCircle2 className="w-8 h-8 mb-2 text-green-500" />
              <p>No pending posts</p>
              <p className="text-xs">All caught up!</p>
            </div>
          ) : (
            <div className="grid gap-4">
              {items.map((item) => (
                <Card key={item.item_id} className="glass-panel border-white/10">
                  <CardContent className="p-4">
                    <div className="flex gap-4">
                      <div className="w-24 h-24 rounded-lg bg-black/40 overflow-hidden shrink-0">
                        <img
                          src={`${getApiBase()}/gallery/image/${encodeURIComponent(item.image_path)}`}
                          alt="Queue item"
                          className="w-full h-full object-cover"
                          onError={(e) => {
                            (e.target as HTMLImageElement).src = "";
                            (e.target as HTMLImageElement).style.display = "none";
                          }}
                        />
                      </div>

                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-2">
                          <Badge
                            variant="outline"
                            className={
                              item.platform === "instagram_manual"
                                ? "bg-pink-500/10 text-pink-400 border-pink-500/20"
                                : "bg-cyan-500/10 text-cyan-400 border-cyan-500/20"
                            }
                          >
                            {item.platform === "instagram_manual" ? (
                              <Instagram className="w-3 h-3 mr-1" />
                            ) : (
                              <Music2 className="w-3 h-3 mr-1" />
                            )}
                            {item.platform === "instagram_manual" ? "Instagram" : "TikTok"}
                          </Badge>
                          <span className="text-xs text-muted-foreground">
                            {item.influencer_name}
                          </span>
                        </div>

                        <div className="flex items-center gap-2 text-xs text-muted-foreground mb-2">
                          <Clock className="w-3 h-3" />
                          <span>Suggested: {formatTime(item.suggested_time)}</span>
                          <span>•</span>
                          <span>{formatDate(item.suggested_time)}</span>
                        </div>

                        <p className="text-sm text-foreground/80 line-clamp-2 mb-3">
                          {item.caption}
                        </p>

                        <div className="flex gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => copyCaption(item.caption)}
                          >
                            <Copy className="w-3 h-3 mr-1" />
                            Copy Caption
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() =>
                              window.open(
                                `${getApiBase()}/gallery/image/${encodeURIComponent(item.image_path)}`,
                                "_blank"
                              )
                            }
                          >
                            <ExternalLink className="w-3 h-3 mr-1" />
                            Open Image
                          </Button>
                          <Button
                            variant="default"
                            size="sm"
                            onClick={() => markAsPosted(item.item_id)}
                            disabled={markingPosted === item.item_id}
                          >
                            {markingPosted === item.item_id ? (
                              <Loader2 className="w-3 h-3 mr-1 animate-spin" />
                            ) : (
                              <CheckCircle2 className="w-3 h-3 mr-1" />
                            )}
                            Mark Posted
                          </Button>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      </Tabs>

      <div className="text-xs text-muted-foreground text-center py-2 border-t border-white/5">
        These posts require manual posting from your mobile device due to platform TOS restrictions.
      </div>
    </div>
  );
}

export default ManualQueueTab;
