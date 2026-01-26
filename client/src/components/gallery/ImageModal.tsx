import { useState } from "react";
import { Check, X, ChevronLeft, ChevronRight, Send, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import { VisuallyHidden } from "@radix-ui/react-visually-hidden";
import { GalleryImage, getApiBase } from "./types";

interface ImageModalProps {
  isOpen: boolean;
  onClose: () => void;
  image: GalleryImage | null;
  images: GalleryImage[];
  currentIndex: number;
  onNavigate: (direction: number) => void;
  onApprove: (path: string) => void;
  onReject: (path: string) => void;
  onPostToX?: (path: string) => Promise<void>;
  approvalStatus: Record<string, string>;
  backendUrl: string;
  selectedInfluencer?: string;
}

export function ImageModal({ 
  isOpen, 
  onClose, 
  image, 
  images,
  currentIndex,
  onNavigate,
  onApprove, 
  onReject,
  onPostToX,
  approvalStatus,
  backendUrl,
  selectedInfluencer = "starbright_monroe"
}: ImageModalProps) {
  const [isPosting, setIsPosting] = useState(false);
  
  if (!isOpen || !image) return null;

  const status = approvalStatus[image.path] || "pending";
  const apiBase = getApiBase(backendUrl);
  const imageUrl = `${apiBase}/gallery/image/${image.path}`;
  
  const handlePostToX = async () => {
    if (!onPostToX) return;
    setIsPosting(true);
    try {
      await onPostToX(image.path);
    } finally {
      setIsPosting(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-4xl bg-black/95 border-white/10">
        <VisuallyHidden>
          <DialogTitle>Image Preview</DialogTitle>
        </VisuallyHidden>
        <div className="relative">
          <Button 
            variant="ghost" 
            size="icon" 
            className="absolute left-2 top-1/2 -translate-y-1/2 z-10 bg-black/50 hover:bg-black/70"
            onClick={() => onNavigate(-1)}
            disabled={currentIndex === 0}
          >
            <ChevronLeft className="w-6 h-6" />
          </Button>
          
          <img 
            src={imageUrl} 
            alt={image.filename}
            className="w-full max-h-[70vh] object-contain rounded-lg"
          />
          
          <Button 
            variant="ghost" 
            size="icon" 
            className="absolute right-2 top-1/2 -translate-y-1/2 z-10 bg-black/50 hover:bg-black/70"
            onClick={() => onNavigate(1)}
            disabled={currentIndex === images.length - 1}
          >
            <ChevronRight className="w-6 h-6" />
          </Button>
        </div>
        
        <div className="flex items-center justify-between mt-4">
          <div>
            <p className="text-sm font-mono text-muted-foreground">{image.filename}</p>
            <p className="text-xs text-muted-foreground/60">{image.date} · {image.size_kb} KB</p>
          </div>
          
          {status === "pending" && (
            <div className="flex gap-2">
              <Button 
                size="sm" 
                variant="outline" 
                className="bg-green-500/10 border-green-500/30 text-green-400 hover:bg-green-500/20"
                onClick={() => onApprove(image.path)}
              >
                <Check className="w-4 h-4 mr-1" /> Approve
              </Button>
              <Button 
                size="sm" 
                variant="outline" 
                className="bg-red-500/10 border-red-500/30 text-red-400 hover:bg-red-500/20"
                onClick={() => onReject(image.path)}
              >
                <X className="w-4 h-4 mr-1" /> Reject
              </Button>
            </div>
          )}
          
          {status !== "pending" && (
            <div className="flex items-center gap-2">
              {(status === "approved" || status === "final") && onPostToX && (
                <Button
                  size="sm"
                  variant="outline"
                  className="bg-blue-500/10 border-blue-500/30 text-blue-400 hover:bg-blue-500/20"
                  onClick={handlePostToX}
                  disabled={isPosting}
                >
                  {isPosting ? (
                    <Loader2 className="w-4 h-4 mr-1 animate-spin" />
                  ) : (
                    <Send className="w-4 h-4 mr-1" />
                  )}
                  Post to X
                </Button>
              )}
              <Badge className={
                status === "approved" || status === "final" 
                  ? "bg-green-500/20 text-green-400" 
                  : "bg-red-500/20 text-red-400"
              }>
                {status.toUpperCase()}
              </Badge>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
