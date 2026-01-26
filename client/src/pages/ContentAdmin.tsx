import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { Loader2, Image, Video, Archive, Star, Crown, Eye, ChevronLeft, ChevronRight, Send } from "lucide-react";
import { Link } from "wouter";

interface ContentFile {
  name: string;
  size: number;
  type: "image" | "video";
  path: string;
}

const TIERS = [
  { id: "unsorted", label: "Unsorted", icon: Eye, color: "bg-gray-500" },
  { id: "teaser", label: "Teaser (Free)", icon: Eye, color: "bg-blue-500" },
  { id: "companion", label: "Companion ($9.99)", icon: Star, color: "bg-purple-500" },
  { id: "vip", label: "VIP ($24.99)", icon: Crown, color: "bg-yellow-500" },
  { id: "archive", label: "Archive", icon: Archive, color: "bg-red-500" },
];

export default function ContentAdmin() {
  const [persona, setPersona] = useState("starbright");
  const [currentTier, setCurrentTier] = useState("unsorted");
  const [files, setFiles] = useState<ContentFile[]>([]);
  const [selectedFiles, setSelectedFiles] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState<Record<string, number>>({});
  const [currentIndex, setCurrentIndex] = useState(0);
  const [viewMode, setViewMode] = useState<"grid" | "single">("single");

  const apiKey = localStorage.getItem("adminApiKey") || "";

  const fetchFiles = async () => {
    if (!apiKey) return;
    setLoading(true);
    try {
      const res = await fetch(`/api/content/list/${persona}/${currentTier}`, {
        headers: { "x-api-key": apiKey },
      });
      const data = await res.json();
      setFiles(data.files || []);
      setCurrentIndex(0);
      setSelectedFiles(new Set());
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  const fetchStats = async () => {
    if (!apiKey) return;
    try {
      const res = await fetch(`/api/content/stats/${persona}`, {
        headers: { "x-api-key": apiKey },
      });
      const data = await res.json();
      setStats(data);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchFiles();
    fetchStats();
  }, [persona, currentTier, apiKey]);

  const moveFiles = async (toTier: string) => {
    if (selectedFiles.size === 0) return;
    
    try {
      await fetch("/api/content/bulk-move", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "x-api-key": apiKey,
        },
        body: JSON.stringify({
          files: Array.from(selectedFiles),
          from_tier: currentTier,
          to_tier: toTier,
          persona,
        }),
      });
      fetchFiles();
      fetchStats();
    } catch (e) {
      console.error(e);
    }
  };

  const moveCurrent = async (toTier: string) => {
    if (files.length === 0) return;
    const file = files[currentIndex];
    
    try {
      await fetch("/api/content/move", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "x-api-key": apiKey,
        },
        body: JSON.stringify({
          filename: file.name,
          from_tier: currentTier,
          to_tier: toTier,
          persona,
        }),
      });
      
      const newFiles = files.filter((_, i) => i !== currentIndex);
      setFiles(newFiles);
      if (currentIndex >= newFiles.length && newFiles.length > 0) {
        setCurrentIndex(newFiles.length - 1);
      }
      fetchStats();
    } catch (e) {
      console.error(e);
    }
  };

  const toggleSelect = (name: string) => {
    const newSelected = new Set(selectedFiles);
    if (newSelected.has(name)) {
      newSelected.delete(name);
    } else {
      newSelected.add(name);
    }
    setSelectedFiles(newSelected);
  };

  const currentFile = files[currentIndex];

  if (!apiKey) {
    return (
      <div className="p-8 max-w-md mx-auto">
        <Card>
          <CardHeader>
            <CardTitle>Admin Access Required</CardTitle>
          </CardHeader>
          <CardContent>
            <input
              type="password"
              placeholder="Enter Admin API Key"
              className="w-full p-3 border rounded mb-4"
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  localStorage.setItem("adminApiKey", (e.target as HTMLInputElement).value);
                  window.location.reload();
                }
              }}
            />
            <p className="text-sm text-gray-500">Press Enter to save</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="p-4 max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Content Manager</h1>
        <div className="flex gap-2">
          <Link href="/drops">
            <Button variant="outline" className="gap-2">
              <Send className="w-4 h-4" />
              Content Drops
            </Button>
          </Link>
          <Select value={persona} onValueChange={setPersona}>
            <SelectTrigger className="w-40">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="starbright">Starbright</SelectItem>
              <SelectItem value="luna">Luna</SelectItem>
            </SelectContent>
          </Select>
          <Button
            variant={viewMode === "single" ? "default" : "outline"}
            onClick={() => setViewMode("single")}
          >
            Single
          </Button>
          <Button
            variant={viewMode === "grid" ? "default" : "outline"}
            onClick={() => setViewMode("grid")}
          >
            Grid
          </Button>
        </div>
      </div>

      <div className="flex gap-2 mb-6 flex-wrap">
        {TIERS.map((tier) => (
          <Button
            key={tier.id}
            variant={currentTier === tier.id ? "default" : "outline"}
            onClick={() => setCurrentTier(tier.id)}
            className="flex items-center gap-2"
          >
            <tier.icon className="w-4 h-4" />
            {tier.label}
            <Badge variant="secondary" className="ml-1">
              {stats[tier.id] || 0}
            </Badge>
          </Button>
        ))}
      </div>

      {loading ? (
        <div className="flex justify-center py-20">
          <Loader2 className="w-8 h-8 animate-spin" />
        </div>
      ) : files.length === 0 ? (
        <Card>
          <CardContent className="py-20 text-center text-gray-500">
            No content in this tier
          </CardContent>
        </Card>
      ) : viewMode === "single" ? (
        <div className="space-y-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-4">
                <Button
                  variant="outline"
                  disabled={currentIndex === 0}
                  onClick={() => setCurrentIndex(currentIndex - 1)}
                >
                  <ChevronLeft className="w-4 h-4" />
                </Button>
                <span className="text-sm text-gray-500">
                  {currentIndex + 1} of {files.length}
                </span>
                <Button
                  variant="outline"
                  disabled={currentIndex >= files.length - 1}
                  onClick={() => setCurrentIndex(currentIndex + 1)}
                >
                  <ChevronRight className="w-4 h-4" />
                </Button>
              </div>

              {currentFile && (
                <div className="space-y-4">
                  <div className="aspect-[9/16] max-h-[600px] bg-black rounded-lg overflow-hidden flex items-center justify-center">
                    {currentFile.type === "video" ? (
                      <video
                        key={currentFile.path}
                        src={`${currentFile.path}?key=${apiKey}`}
                        controls
                        className="max-w-full max-h-full"
                      />
                    ) : (
                      <img
                        src={`${currentFile.path}?key=${apiKey}`}
                        alt={currentFile.name}
                        className="max-w-full max-h-full object-contain"
                      />
                    )}
                  </div>

                  <div className="text-center text-sm text-gray-500 truncate">
                    {currentFile.name}
                  </div>

                  <div className="flex flex-wrap gap-2 justify-center">
                    {TIERS.filter((t) => t.id !== currentTier).map((tier) => (
                      <Button
                        key={tier.id}
                        variant="outline"
                        onClick={() => moveCurrent(tier.id)}
                        className={`${tier.id === "archive" ? "text-red-500" : ""}`}
                      >
                        <tier.icon className="w-4 h-4 mr-2" />
                        {tier.id === "archive" ? "Delete" : `→ ${tier.label}`}
                      </Button>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      ) : (
        <div className="space-y-4">
          {selectedFiles.size > 0 && (
            <div className="flex gap-2 items-center p-3 bg-gray-100 rounded-lg">
              <span className="text-sm font-medium">{selectedFiles.size} selected</span>
              {TIERS.filter((t) => t.id !== currentTier).map((tier) => (
                <Button
                  key={tier.id}
                  size="sm"
                  variant="outline"
                  onClick={() => moveFiles(tier.id)}
                >
                  → {tier.label}
                </Button>
              ))}
            </div>
          )}

          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
            {files.map((file) => (
              <div
                key={file.name}
                className={`relative aspect-square bg-gray-100 rounded-lg overflow-hidden cursor-pointer border-2 ${
                  selectedFiles.has(file.name) ? "border-blue-500" : "border-transparent"
                }`}
                onClick={() => toggleSelect(file.name)}
              >
                <div className="absolute top-2 left-2 z-10">
                  <Checkbox checked={selectedFiles.has(file.name)} />
                </div>
                <div className="absolute top-2 right-2 z-10">
                  {file.type === "video" ? (
                    <Video className="w-5 h-5 text-white drop-shadow" />
                  ) : (
                    <Image className="w-5 h-5 text-white drop-shadow" />
                  )}
                </div>
                {file.type === "video" ? (
                  <video
                    src={`${file.path}?key=${apiKey}`}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <img
                    src={`${file.path}?key=${apiKey}`}
                    alt={file.name}
                    className="w-full h-full object-cover"
                  />
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
