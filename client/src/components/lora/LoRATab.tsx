import { useState, useEffect } from "react";
import {
  Sparkles,
  Play,
  RefreshCw,
  Image as ImageIcon,
  Check,
  Loader2,
  AlertCircle,
  Database,
  Zap,
  Download
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useToast } from "@/hooks/use-toast";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { LogEntryType } from "@/components/gallery/types";

interface LoRATabProps {
  backendUrl: string;
  addLog: (agent: string, message: string, type?: LogEntryType) => void;
}

interface Dataset {
  persona: string;
  path: string;
  image_count: number;
  images: string[];
}

interface TrainedModel {
  training_id: string;
  trigger_word: string;
  status: string;
  started_at: string;
  completed_at?: string;
  model_url?: string;
  steps?: number;
  lora_rank?: number;
}

interface GeneratedImage {
  filename: string;
  path: string;
  size_kb: number;
  created: string;
}

export function LoRATab({ backendUrl, addLog }: LoRATabProps) {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [models, setModels] = useState<Record<string, TrainedModel>>({});
  const [generatedImages, setGeneratedImages] = useState<GeneratedImage[]>([]);
  const [loading, setLoading] = useState(false);
  const [training, setTraining] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [checkingStatus, setCheckingStatus] = useState(false);
  
  const [selectedPersona, setSelectedPersona] = useState("starbright");
  const [triggerWord, setTriggerWord] = useState("STARBRIGHT");
  const [prompt, setPrompt] = useState("");
  const [aspectRatio, setAspectRatio] = useState("9:16");
  const [numOutputs, setNumOutputs] = useState(1);
  
  const { toast } = useToast();

  const fetchData = async () => {
    setLoading(true);
    try {
      const [datasetsRes, modelsRes] = await Promise.all([
        fetch(`${backendUrl}/api/lora/datasets`),
        fetch(`${backendUrl}/api/lora/models`)
      ]);
      
      if (datasetsRes.ok) {
        const data = await datasetsRes.json();
        setDatasets(data.datasets || []);
      }
      
      if (modelsRes.ok) {
        const data = await modelsRes.json();
        setModels(data.models || {});
      }
      
      addLog("LORA", "Loaded training data", "info");
    } catch (error) {
      addLog("LORA", `Error loading data: ${error}`, "error");
    } finally {
      setLoading(false);
    }
  };

  const fetchGeneratedImages = async () => {
    try {
      const res = await fetch(`${backendUrl}/api/lora/generated?persona=${selectedPersona}`);
      if (res.ok) {
        const data = await res.json();
        setGeneratedImages(data.images || []);
      }
    } catch (error) {
      console.error("Error fetching generated images:", error);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    fetchGeneratedImages();
  }, [selectedPersona]);

  const startTraining = async () => {
    setTraining(true);
    addLog("LORA", `Starting LoRA training for ${selectedPersona}...`, "info");
    
    try {
      const response = await fetch(`${backendUrl}/api/lora/train`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          persona: selectedPersona,
          trigger_word: triggerWord,
          steps: 1000,
          lora_rank: 16,
          learning_rate: 0.0004
        })
      });
      
      const result = await response.json();
      
      if (result.status === "training_started") {
        addLog("LORA", `Training started! ID: ${result.training_id}`, "success");
        toast({
          title: "Training Started",
          description: `LoRA training for ${selectedPersona} has begun. Check status in a few minutes.`
        });
        fetchData();
      } else {
        throw new Error(result.error || "Training failed to start");
      }
    } catch (error) {
      addLog("LORA", `Training error: ${error}`, "error");
      toast({
        title: "Training Error",
        description: String(error),
        variant: "destructive"
      });
    } finally {
      setTraining(false);
    }
  };

  const checkStatus = async () => {
    setCheckingStatus(true);
    addLog("LORA", `Checking training status for ${selectedPersona}...`, "info");
    
    try {
      const response = await fetch(`${backendUrl}/api/lora/train/status?persona=${selectedPersona}`);
      const result = await response.json();
      
      addLog("LORA", `Status: ${result.status}`, result.status === "completed" ? "success" : "info");
      
      toast({
        title: `Training Status: ${result.status}`,
        description: result.message || result.error || "Check logs for details"
      });
      
      fetchData();
    } catch (error) {
      addLog("LORA", `Status check error: ${error}`, "error");
    } finally {
      setCheckingStatus(false);
    }
  };

  const generateImage = async () => {
    if (!prompt.trim()) {
      toast({
        title: "Prompt Required",
        description: "Please enter a prompt for image generation",
        variant: "destructive"
      });
      return;
    }
    
    setGenerating(true);
    addLog("LORA", `Generating image with prompt: ${prompt.slice(0, 50)}...`, "info");
    
    try {
      const response = await fetch(`${backendUrl}/api/lora/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          persona: selectedPersona,
          prompt: prompt,
          num_outputs: numOutputs,
          aspect_ratio: aspectRatio,
          guidance_scale: 3.5,
          num_inference_steps: 28
        })
      });
      
      const result = await response.json();
      
      if (result.status === "success") {
        addLog("LORA", `Generated ${result.count} image(s)!`, "success");
        toast({
          title: "Images Generated",
          description: `Successfully generated ${result.count} image(s)`
        });
        fetchGeneratedImages();
      } else {
        throw new Error(result.error || "Generation failed");
      }
    } catch (error) {
      addLog("LORA", `Generation error: ${error}`, "error");
      toast({
        title: "Generation Error",
        description: String(error),
        variant: "destructive"
      });
    } finally {
      setGenerating(false);
    }
  };

  const selectedDataset = datasets.find(d => d.persona === selectedPersona);
  const selectedModel = models[selectedPersona];

  return (
    <div className="h-full flex flex-col gap-4 overflow-auto p-2">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-purple-400" />
            LoRA Training & Generation
          </h2>
          <p className="text-sm text-muted-foreground">
            Train FLUX LoRA models for consistent character generation
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={fetchData} disabled={loading}>
          <RefreshCw className={`w-4 h-4 mr-2 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </Button>
      </div>

      <Tabs defaultValue="train" className="flex-1">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="train">Training</TabsTrigger>
          <TabsTrigger value="generate">Generate</TabsTrigger>
        </TabsList>

        <TabsContent value="train" className="space-y-4 mt-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Database className="w-4 h-4" />
                  Training Datasets
                </CardTitle>
                <CardDescription>
                  Available image datasets for LoRA training
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>Select Persona</Label>
                  <Select value={selectedPersona} onValueChange={setSelectedPersona}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {datasets.map(d => (
                        <SelectItem key={d.persona} value={d.persona}>
                          {d.persona} ({d.image_count} images)
                        </SelectItem>
                      ))}
                      {datasets.length === 0 && (
                        <SelectItem value="starbright">starbright</SelectItem>
                      )}
                    </SelectContent>
                  </Select>
                </div>

                {selectedDataset && (
                  <div className="bg-muted/50 rounded-lg p-3 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">Images:</span>
                      <Badge variant="secondary">{selectedDataset.image_count}</Badge>
                    </div>
                    <div className="text-xs text-muted-foreground max-h-24 overflow-auto">
                      {selectedDataset.images.slice(0, 5).map((img, i) => (
                        <div key={i}>{img}</div>
                      ))}
                      {selectedDataset.images.length > 5 && (
                        <div>...and {selectedDataset.images.length - 5} more</div>
                      )}
                    </div>
                  </div>
                )}

                <div className="space-y-2">
                  <Label>Trigger Word</Label>
                  <Input
                    value={triggerWord}
                    onChange={e => setTriggerWord(e.target.value.toUpperCase())}
                    placeholder="STARBRIGHT"
                  />
                  <p className="text-xs text-muted-foreground">
                    Use this word in prompts to activate the LoRA
                  </p>
                </div>

                <Button
                  className="w-full"
                  onClick={startTraining}
                  disabled={training || !selectedDataset}
                >
                  {training ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Training...
                    </>
                  ) : (
                    <>
                      <Play className="w-4 h-4 mr-2" />
                      Start Training (~$1.50)
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Zap className="w-4 h-4" />
                  Trained Models
                </CardTitle>
                <CardDescription>
                  LoRA models ready for generation
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {selectedModel ? (
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">Status:</span>
                      <Badge
                        variant={selectedModel.status === "completed" ? "default" : "secondary"}
                        className={
                          selectedModel.status === "completed"
                            ? "bg-green-500/20 text-green-400"
                            : selectedModel.status === "training"
                            ? "bg-yellow-500/20 text-yellow-400"
                            : "bg-red-500/20 text-red-400"
                        }
                      >
                        {selectedModel.status === "completed" ? (
                          <Check className="w-3 h-3 mr-1" />
                        ) : selectedModel.status === "training" ? (
                          <Loader2 className="w-3 h-3 mr-1 animate-spin" />
                        ) : (
                          <AlertCircle className="w-3 h-3 mr-1" />
                        )}
                        {selectedModel.status}
                      </Badge>
                    </div>

                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">Trigger:</span>
                      <code className="text-sm bg-muted px-2 py-0.5 rounded">
                        {selectedModel.trigger_word}
                      </code>
                    </div>

                    {selectedModel.steps && (
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">Steps:</span>
                        <span className="text-sm">{selectedModel.steps}</span>
                      </div>
                    )}

                    {selectedModel.started_at && (
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">Started:</span>
                        <span className="text-xs text-muted-foreground">
                          {new Date(selectedModel.started_at).toLocaleString()}
                        </span>
                      </div>
                    )}

                    <Button
                      variant="outline"
                      className="w-full"
                      onClick={checkStatus}
                      disabled={checkingStatus}
                    >
                      {checkingStatus ? (
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      ) : (
                        <RefreshCw className="w-4 h-4 mr-2" />
                      )}
                      Check Status
                    </Button>
                  </div>
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    <Sparkles className="w-8 h-8 mx-auto mb-2 opacity-50" />
                    <p className="text-sm">No trained model for {selectedPersona}</p>
                    <p className="text-xs mt-1">Start training to create one</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="generate" className="space-y-4 mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <ImageIcon className="w-4 h-4" />
                Generate Images
              </CardTitle>
              <CardDescription>
                Use your trained LoRA to generate consistent images
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {selectedModel?.status !== "completed" ? (
                <div className="text-center py-8 text-muted-foreground">
                  <AlertCircle className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">No completed LoRA model available</p>
                  <p className="text-xs mt-1">Train a model first in the Training tab</p>
                </div>
              ) : (
                <>
                  <div className="space-y-2">
                    <Label>Prompt</Label>
                    <Textarea
                      value={prompt}
                      onChange={e => setPrompt(e.target.value)}
                      placeholder={`${selectedModel.trigger_word}, young woman with brown hair and hazel eyes, wearing a red crop top, standing in a modern living room, soft natural lighting, photorealistic`}
                      className="min-h-24"
                    />
                    <p className="text-xs text-muted-foreground">
                      Trigger word "{selectedModel.trigger_word}" will be added automatically if not present
                    </p>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Aspect Ratio</Label>
                      <Select value={aspectRatio} onValueChange={setAspectRatio}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="9:16">9:16 (Portrait)</SelectItem>
                          <SelectItem value="1:1">1:1 (Square)</SelectItem>
                          <SelectItem value="16:9">16:9 (Landscape)</SelectItem>
                          <SelectItem value="4:5">4:5 (Instagram)</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="space-y-2">
                      <Label>Number of Images</Label>
                      <Select value={String(numOutputs)} onValueChange={v => setNumOutputs(Number(v))}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="1">1 image</SelectItem>
                          <SelectItem value="2">2 images</SelectItem>
                          <SelectItem value="4">4 images</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  <Button
                    className="w-full"
                    onClick={generateImage}
                    disabled={generating || !prompt.trim()}
                  >
                    {generating ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Generating...
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-4 h-4 mr-2" />
                        Generate (~$0.01/image)
                      </>
                    )}
                  </Button>
                </>
              )}
            </CardContent>
          </Card>

          {generatedImages.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Download className="w-4 h-4" />
                  Generated Images ({generatedImages.length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {generatedImages.slice(0, 8).map((img, i) => (
                    <div key={i} className="relative group">
                      <img
                        src={`${backendUrl}/content/${img.path.replace("content/", "")}`}
                        alt={img.filename}
                        className="w-full aspect-[9/16] object-cover rounded-lg border border-white/10"
                        onError={(e) => {
                          (e.target as HTMLImageElement).src = "/placeholder.png";
                        }}
                      />
                      <div className="absolute bottom-0 left-0 right-0 bg-black/60 text-xs p-1 rounded-b-lg opacity-0 group-hover:opacity-100 transition-opacity">
                        <div className="truncate">{img.filename}</div>
                        <div className="text-muted-foreground">{img.size_kb} KB</div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
