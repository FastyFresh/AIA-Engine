import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Loader2, Send, Image, Video, Star, Crown, CheckCircle, AlertCircle, ArrowLeft, Sparkles } from "lucide-react";
import { Link } from "wouter";

interface ContentFile {
  name: string;
  size: number;
  type: "image" | "video";
  path: string;
}

export default function ContentDrops() {
  const [persona, setPersona] = useState("starbright");
  const [sourceTier, setSourceTier] = useState("vip");
  const [targetTier, setTargetTier] = useState("companion");
  const [files, setFiles] = useState<ContentFile[]>([]);
  const [selectedFile, setSelectedFile] = useState<ContentFile | null>(null);
  const [caption, setCaption] = useState("");
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [result, setResult] = useState<{ success: boolean; message: string } | null>(null);
  const [generatingCaption, setGeneratingCaption] = useState(false);
  const [captionSuggestions, setCaptionSuggestions] = useState<string[]>([]);

  const apiKey = localStorage.getItem("adminApiKey") || "";

  const fetchFiles = async () => {
    if (!apiKey) return;
    setLoading(true);
    try {
      const res = await fetch(`/api/content/list/${persona}/${sourceTier}`, {
        headers: { "x-api-key": apiKey },
      });
      const data = await res.json();
      setFiles(data.files || []);
      setSelectedFile(null);
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchFiles();
  }, [persona, sourceTier, apiKey]);

  const generateCaption = async () => {
    if (!selectedFile) return;
    
    setGeneratingCaption(true);
    setCaptionSuggestions([]);
    
    try {
      const res = await fetch("/api/telegram/generate-caption", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "x-api-key": apiKey,
        },
        body: JSON.stringify({
          persona_id: persona === "starbright" ? "starbright_monroe" : "luna_vale",
          content_path: `content/telegram/${persona}/${sourceTier}/${selectedFile.name}`,
          tier: targetTier,
        }),
      });
      
      const data = await res.json();
      
      if (res.ok && data.captions) {
        setCaptionSuggestions(data.captions);
      } else {
        console.error("Caption generation failed:", data);
      }
    } catch (e) {
      console.error("Caption generation error:", e);
    }
    
    setGeneratingCaption(false);
  };

  const sendContentDrop = async () => {
    if (!selectedFile || !caption.trim()) return;
    
    setSending(true);
    setResult(null);
    
    try {
      const res = await fetch("/api/telegram/send-content-drop", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "x-api-key": apiKey,
        },
        body: JSON.stringify({
          persona_id: persona === "starbright" ? "starbright_monroe" : "luna_vale",
          content_path: `content/telegram/${persona}/${sourceTier}/${selectedFile.name}`,
          caption: caption,
          tier: targetTier,
          content_type: selectedFile.type === "video" ? "video" : "photo",
        }),
      });
      
      const data = await res.json();
      
      if (res.ok) {
        setResult({ 
          success: true, 
          message: `Sent to ${data.recipients} subscribers!` 
        });
        setCaption("");
        setSelectedFile(null);
      } else {
        setResult({ 
          success: false, 
          message: data.detail || "Failed to send content drop" 
        });
      }
    } catch (e) {
      setResult({ success: false, message: "Network error" });
    }
    
    setSending(false);
  };

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
    <div className="p-4 max-w-6xl mx-auto">
      <div className="flex items-center gap-4 mb-6">
        <Link href="/content">
          <Button variant="ghost" size="sm">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Content
          </Button>
        </Link>
        <h1 className="text-2xl font-bold">Content Drops</h1>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Select Content</CardTitle>
            <CardDescription>Choose content to send to subscribers</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-4">
              <div className="flex-1">
                <label className="text-sm font-medium mb-2 block">Persona</label>
                <Select value={persona} onValueChange={setPersona}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="starbright">Starbright Monroe</SelectItem>
                    <SelectItem value="luna">Luna Vale</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="flex-1">
                <label className="text-sm font-medium mb-2 block">Browse From</label>
                <Select value={sourceTier} onValueChange={setSourceTier}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="teaser">Teaser</SelectItem>
                    <SelectItem value="companion">Companion</SelectItem>
                    <SelectItem value="vip">VIP</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="border rounded-lg p-4 h-80 overflow-y-auto bg-gray-50">
              {loading ? (
                <div className="flex items-center justify-center h-full">
                  <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
                </div>
              ) : files.length === 0 ? (
                <div className="flex items-center justify-center h-full text-gray-500">
                  No content in this tier
                </div>
              ) : (
                <div className="grid grid-cols-3 gap-2">
                  {files.map((file) => (
                    <div
                      key={file.name}
                      onClick={() => setSelectedFile(file)}
                      className={`relative cursor-pointer rounded-lg overflow-hidden border-2 transition-all ${
                        selectedFile?.name === file.name
                          ? "border-purple-500 ring-2 ring-purple-200"
                          : "border-transparent hover:border-gray-300"
                      }`}
                    >
                      {file.type === "video" ? (
                        <div className="aspect-square bg-gray-800 relative">
                          <video
                            src={`/api/content/file/${persona}/${sourceTier}/${file.name}?key=${apiKey}`}
                            className="w-full h-full object-cover"
                            muted
                            preload="metadata"
                          />
                          <div className="absolute top-1 right-1 bg-black/70 px-1.5 py-0.5 rounded text-xs text-white flex items-center gap-1">
                            <Video className="w-3 h-3" />
                            VIDEO
                          </div>
                        </div>
                      ) : (
                        <img
                          src={`/api/content/file/${persona}/${sourceTier}/${file.name}?key=${apiKey}`}
                          alt={file.name}
                          className="aspect-square object-cover"
                        />
                      )}
                      {selectedFile?.name === file.name && (
                        <div className="absolute inset-0 bg-purple-500/20 flex items-center justify-center">
                          <CheckCircle className="w-8 h-8 text-purple-600" />
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Compose Message</CardTitle>
            <CardDescription>Write the caption and select recipients</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {selectedFile && (
              <div className="space-y-3">
                <div className="rounded-lg overflow-hidden bg-gray-900 max-h-64">
                  {selectedFile.type === "video" ? (
                    <video
                      src={`/api/content/file/${persona}/${sourceTier}/${selectedFile.name}?key=${apiKey}`}
                      controls
                      className="w-full max-h-64 object-contain"
                    />
                  ) : (
                    <img
                      src={`/api/content/file/${persona}/${sourceTier}/${selectedFile.name}?key=${apiKey}`}
                      alt={selectedFile.name}
                      className="w-full max-h-64 object-contain"
                    />
                  )}
                </div>
                <div className="p-2 bg-purple-50 dark:bg-purple-900/20 rounded-lg flex items-center gap-3">
                  {selectedFile.type === "video" ? (
                    <Video className="w-6 h-6 text-purple-500" />
                  ) : (
                    <Image className="w-6 h-6 text-purple-500" />
                  )}
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-sm truncate">{selectedFile.name}</p>
                    <p className="text-xs text-gray-500">
                      {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                </div>
              </div>
            )}

            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm font-medium">Caption</label>
                {selectedFile && selectedFile.type === "image" && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={generateCaption}
                    disabled={generatingCaption}
                    className="text-purple-600 border-purple-200 hover:bg-purple-50"
                  >
                    {generatingCaption ? (
                      <>
                        <Loader2 className="w-3 h-3 mr-1 animate-spin" />
                        Generating...
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-3 h-3 mr-1" />
                        AI Suggest
                      </>
                    )}
                  </Button>
                )}
              </div>
              
              {captionSuggestions.length > 0 && (
                <div className="mb-3 space-y-2">
                  <p className="text-xs text-gray-500 font-medium">Click to use:</p>
                  {captionSuggestions.map((suggestion, idx) => (
                    <button
                      key={idx}
                      onClick={() => {
                        setCaption(suggestion);
                        setCaptionSuggestions([]);
                      }}
                      className="w-full text-left p-2 text-sm bg-black text-white border border-purple-500 rounded-lg hover:border-purple-300 transition-colors"
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              )}
              
              <Textarea
                value={caption}
                onChange={(e) => setCaption(e.target.value)}
                placeholder="Write a caption for this content drop..."
                rows={4}
                className="resize-none"
              />
              <p className="text-xs text-gray-500 mt-1">
                This will be sent as a message with the content
              </p>
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block">Send To</label>
              <div className="flex gap-2">
                <Button
                  variant={targetTier === "companion" ? "default" : "outline"}
                  onClick={() => setTargetTier("companion")}
                  className="flex-1"
                >
                  <Star className="w-4 h-4 mr-2" />
                  Companion + VIP
                </Button>
                <Button
                  variant={targetTier === "vip" ? "default" : "outline"}
                  onClick={() => setTargetTier("vip")}
                  className="flex-1"
                >
                  <Crown className="w-4 h-4 mr-2" />
                  VIP Only
                </Button>
              </div>
              <p className="text-xs text-gray-500 mt-1">
                {targetTier === "companion" 
                  ? "Sends to all Companion and VIP subscribers"
                  : "Sends only to VIP subscribers (exclusive)"}
              </p>
            </div>

            {result && (
              <div className={`p-3 rounded-lg flex items-center gap-2 ${
                result.success ? "bg-green-50 text-green-700" : "bg-red-50 text-red-700"
              }`}>
                {result.success ? (
                  <CheckCircle className="w-5 h-5" />
                ) : (
                  <AlertCircle className="w-5 h-5" />
                )}
                <span>{result.message}</span>
              </div>
            )}

            <Button
              onClick={sendContentDrop}
              disabled={!selectedFile || !caption.trim() || sending}
              className="w-full"
              size="lg"
            >
              {sending ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Sending...
                </>
              ) : (
                <>
                  <Send className="w-4 h-4 mr-2" />
                  Send Content Drop
                </>
              )}
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
