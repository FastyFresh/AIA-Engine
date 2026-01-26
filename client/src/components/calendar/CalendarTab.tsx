import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Calendar, Clock, Image, Sparkles, RefreshCw, ChevronRight, Zap } from "lucide-react";

interface Post {
  post_number: number;
  scheduled_time: string;
  content_type: string;
  suggested_outfit: string;
  suggested_setting: string;
  hero_image: string | null;
  status: string;
  caption_prompt: string | null;
  cta_category: string;
}

interface DaySchedule {
  date: string;
  day_name: string;
  theme: string;
  vibe: string;
  posts: Post[];
}

interface WeekCalendar {
  influencer: string;
  week_start: string;
  generated_at: string;
  posts_per_day: number;
  total_posts: number;
  days: DaySchedule[];
}

interface ThemeConfig {
  theme: string;
  vibe: string;
  suggested_outfits: string[];
  suggested_settings: string[];
  content_type: string;
  best_times: string[];
}

const themeColors: Record<string, string> = {
  "Motivation Monday": "bg-green-500/20 text-green-400 border-green-500/30",
  "Tease Tuesday": "bg-pink-500/20 text-pink-400 border-pink-500/30",
  "Wellness Wednesday": "bg-cyan-500/20 text-cyan-400 border-cyan-500/30",
  "Thirsty Thursday": "bg-orange-500/20 text-orange-400 border-orange-500/30",
  "Fanvue Friday": "bg-purple-500/20 text-purple-400 border-purple-500/30",
  "Selfie Saturday": "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
  "Soft Sunday": "bg-blue-500/20 text-blue-400 border-blue-500/30",
};

export function CalendarTab() {
  const [postsPerDay, setPostsPerDay] = useState("2");
  const [useAI, setUseAI] = useState(true);
  const [selectedDay, setSelectedDay] = useState<DaySchedule | null>(null);

  const { data: themes } = useQuery<{ themes: Record<string, ThemeConfig> }>({
    queryKey: ["/api/calendar/themes"],
  });

  const [generatedCalendar, setGeneratedCalendar] = useState<WeekCalendar | null>(null);

  const generateMutation = useMutation({
    mutationFn: async () => {
      const res = await fetch(
        `/api/calendar/generate/week?posts_per_day=${postsPerDay}&use_ai=${useAI}`
      );
      if (!res.ok) throw new Error("Failed to generate calendar");
      return res.json();
    },
    onSuccess: (data) => {
      setGeneratedCalendar(data);
    },
  });

  const displayCalendar = generatedCalendar;

  return (
    <div className="space-y-6">
      <Card className="bg-gray-900/50 border-gray-800">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2 text-xl">
                <Calendar className="h-5 w-5 text-purple-400" />
                Content Calendar
              </CardTitle>
              <CardDescription>
                AI-powered themed content scheduling like OmniMe
              </CardDescription>
            </div>
            <div className="flex items-center gap-3">
              <Select value={postsPerDay} onValueChange={setPostsPerDay}>
                <SelectTrigger className="w-32 bg-gray-800 border-gray-700">
                  <SelectValue placeholder="Posts/day" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1">1 post/day</SelectItem>
                  <SelectItem value="2">2 posts/day</SelectItem>
                  <SelectItem value="3">3 posts/day</SelectItem>
                  <SelectItem value="4">4 posts/day</SelectItem>
                </SelectContent>
              </Select>
              <Button
                onClick={() => setUseAI(!useAI)}
                variant={useAI ? "default" : "outline"}
                size="sm"
                className={useAI ? "bg-purple-600 hover:bg-purple-700" : ""}
              >
                <Sparkles className="h-4 w-4 mr-1" />
                AI Captions
              </Button>
              <Button
                onClick={() => generateMutation.mutate()}
                disabled={generateMutation.isPending}
                className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700"
              >
                {generateMutation.isPending ? (
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <Zap className="h-4 w-4 mr-2" />
                )}
                Generate Week
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>

      <Tabs defaultValue="calendar" className="space-y-4">
        <TabsList className="bg-gray-900/50 border border-gray-800">
          <TabsTrigger value="calendar">Week View</TabsTrigger>
          <TabsTrigger value="themes">Theme Guide</TabsTrigger>
        </TabsList>

        <TabsContent value="calendar">
          {displayCalendar ? (
            <div className="grid grid-cols-7 gap-3">
              {displayCalendar.days.map((day) => (
                <Card
                  key={day.date}
                  className={`bg-gray-900/50 border-gray-800 cursor-pointer transition-all hover:border-purple-500/50 ${
                    selectedDay?.date === day.date ? "ring-2 ring-purple-500" : ""
                  }`}
                  onClick={() => setSelectedDay(day)}
                >
                  <CardHeader className="pb-2">
                    <div className="text-xs text-gray-500">{day.date}</div>
                    <CardTitle className="text-sm">{day.day_name}</CardTitle>
                    <Badge
                      className={`text-xs ${themeColors[day.theme] || "bg-gray-700"}`}
                    >
                      {day.theme.split(" ")[0]}
                    </Badge>
                  </CardHeader>
                  <CardContent className="pt-0">
                    <div className="text-xs text-gray-400 mb-2">{day.vibe}</div>
                    <div className="space-y-1">
                      {day.posts.map((post, idx) => (
                        <div
                          key={idx}
                          className="flex items-center gap-1 text-xs bg-gray-800/50 rounded px-2 py-1"
                        >
                          <Clock className="h-3 w-3 text-gray-500" />
                          <span>{post.scheduled_time}</span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <Card className="bg-gray-900/50 border-gray-800 border-dashed">
              <CardContent className="py-12 text-center">
                <Calendar className="h-12 w-12 mx-auto text-gray-600 mb-4" />
                <p className="text-gray-400 mb-4">No calendar generated yet</p>
                <Button
                  onClick={() => generateMutation.mutate()}
                  disabled={generateMutation.isPending}
                  className="bg-purple-600 hover:bg-purple-700"
                >
                  Generate Your First Week
                </Button>
              </CardContent>
            </Card>
          )}

          {selectedDay && (
            <Card className="mt-4 bg-gray-900/50 border-gray-800">
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span>
                    {selectedDay.day_name} - {selectedDay.theme}
                  </span>
                  <Badge className={themeColors[selectedDay.theme]}>
                    {selectedDay.posts.length} posts
                  </Badge>
                </CardTitle>
                <CardDescription>{selectedDay.vibe}</CardDescription>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-64">
                  <div className="space-y-3">
                    {selectedDay.posts.map((post, idx) => (
                      <div
                        key={idx}
                        className="bg-gray-800/50 rounded-lg p-4 border border-gray-700"
                      >
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <Clock className="h-4 w-4 text-purple-400" />
                            <span className="font-medium">{post.scheduled_time}</span>
                            <Badge variant="outline" className="text-xs">
                              {post.content_type}
                            </Badge>
                          </div>
                          <Badge className="bg-gray-700 text-gray-300">
                            {post.status}
                          </Badge>
                        </div>
                        <div className="grid grid-cols-2 gap-2 text-sm text-gray-400">
                          <div>
                            <span className="text-gray-500">Outfit:</span>{" "}
                            {post.suggested_outfit}
                          </div>
                          <div>
                            <span className="text-gray-500">Setting:</span>{" "}
                            {post.suggested_setting}
                          </div>
                          <div>
                            <span className="text-gray-500">CTA:</span>{" "}
                            {post.cta_category}
                          </div>
                          {post.hero_image && (
                            <div className="flex items-center gap-1">
                              <Image className="h-3 w-3" />
                              <span className="truncate">{post.hero_image}</span>
                            </div>
                          )}
                        </div>
                        {post.caption_prompt && (
                          <div className="mt-2 p-2 bg-purple-500/10 rounded border border-purple-500/20">
                            <div className="text-xs text-purple-400 mb-1">
                              AI Caption:
                            </div>
                            <div className="text-sm">{post.caption_prompt}</div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="themes">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {themes?.themes &&
              Object.entries(themes.themes).map(([day, config]) => (
                <Card
                  key={day}
                  className="bg-gray-900/50 border-gray-800"
                >
                  <CardHeader className="pb-2">
                    <CardTitle className="text-lg capitalize">{day}</CardTitle>
                    <Badge className={themeColors[config.theme] || "bg-gray-700"}>
                      {config.theme}
                    </Badge>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div>
                      <div className="text-xs text-gray-500 mb-1">Vibe</div>
                      <div className="text-sm text-gray-300">{config.vibe}</div>
                    </div>
                    <div>
                      <div className="text-xs text-gray-500 mb-1">Content Type</div>
                      <Badge variant="outline">{config.content_type}</Badge>
                    </div>
                    <div>
                      <div className="text-xs text-gray-500 mb-1">Best Times</div>
                      <div className="flex flex-wrap gap-1">
                        {config.best_times.map((time, idx) => (
                          <Badge
                            key={idx}
                            variant="secondary"
                            className="text-xs bg-gray-800"
                          >
                            {time}
                          </Badge>
                        ))}
                      </div>
                    </div>
                    <div>
                      <div className="text-xs text-gray-500 mb-1">Outfits</div>
                      <div className="flex flex-wrap gap-1">
                        {config.suggested_outfits.map((outfit, idx) => (
                          <Badge
                            key={idx}
                            variant="outline"
                            className="text-xs"
                          >
                            {outfit}
                          </Badge>
                        ))}
                      </div>
                    </div>
                    <div>
                      <div className="text-xs text-gray-500 mb-1">Settings</div>
                      <div className="flex flex-wrap gap-1">
                        {config.suggested_settings.map((setting, idx) => (
                          <Badge
                            key={idx}
                            variant="outline"
                            className="text-xs"
                          >
                            {setting}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
