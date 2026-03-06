"use client";

import { useEffect, useState } from "react";
import {
  Palette,
  Sparkles,
  Tag,
  Type,
  Save,
  Loader2,
  AlertCircle,
  Trash2,
  Star,
} from "lucide-react";
import {
  listTemplates,
  listCustomTemplates,
  saveCustomTemplate,
  deleteCustomTemplate,
  type Template,
  type CustomTemplate,
} from "@/lib/api";
import { cn } from "@/lib/utils";

export default function TemplatesPage() {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [customTemplates, setCustomTemplates] = useState<CustomTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Template preview/editor state
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(null);
  const [mainText, setMainText] = useState("Ronaldo Aura");
  const [subText, setSubText] = useState("Different breed entirely");
  const [presetName, setPresetName] = useState("");
  const [saving, setSaving] = useState(false);
  const [saveMsg, setSaveMsg] = useState("");

  useEffect(() => {
    Promise.all([listTemplates(), listCustomTemplates()])
      .then(([t, ct]) => {
        setTemplates(t);
        setCustomTemplates(ct);
        if (t.length > 0) setSelectedTemplate(t[0]);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const handleSavePreset = async () => {
    if (!selectedTemplate || !presetName.trim()) return;
    setSaving(true);
    try {
      await saveCustomTemplate({
        name: presetName,
        description: `${selectedTemplate.name} with "${mainText}"`,
        category: selectedTemplate.category,
        base_template_id: selectedTemplate.id,
        variables: { main_text: mainText, sub_text: subText },
      });
      const updated = await listCustomTemplates();
      setCustomTemplates(updated);
      setPresetName("");
      setSaveMsg("Preset saved!");
      setTimeout(() => setSaveMsg(""), 2000);
    } catch (e) {
      setSaveMsg(e instanceof Error ? e.message : "Save failed");
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteCustom = async (id: string) => {
    try {
      await deleteCustomTemplate(id);
      setCustomTemplates((prev) => prev.filter((t) => t.id !== id));
    } catch {
      // ignore
    }
  };

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-red-600 border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Overlay Templates</h1>
        <p className="mt-1 text-sm text-gray-500">
          Choose and customize text overlay styles for your YouTube Shorts.
          Templates are automatically applied based on video content.
        </p>
      </div>

      {error && (
        <div className="mb-6 rounded-lg border border-amber-200 bg-amber-50 p-4">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-4 w-4 text-amber-600" />
            <p className="text-sm text-amber-700">Backend not connected: {error}</p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
        {/* Template Gallery */}
        <div className="lg:col-span-2">
          <h2 className="mb-4 text-lg font-semibold text-gray-900">
            Built-in Templates
          </h2>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            {templates.map((template) => (
              <button
                key={template.id}
                onClick={() => setSelectedTemplate(template)}
                className={cn(
                  "rounded-xl border-2 p-4 text-left transition-all",
                  selectedTemplate?.id === template.id
                    ? "border-red-500 bg-red-50 shadow-md"
                    : "border-gray-200 bg-white hover:border-gray-300 hover:shadow-sm"
                )}
              >
                {/* Template Preview Card */}
                <div
                  className="mb-3 flex aspect-[9/16] max-h-48 items-center justify-center overflow-hidden rounded-lg"
                  style={{ backgroundColor: template.preview_color + "20" }}
                >
                  <TemplatePreview
                    template={template}
                    mainText={selectedTemplate?.id === template.id ? mainText : template.name}
                    subText={selectedTemplate?.id === template.id ? subText : template.description.slice(0, 30)}
                  />
                </div>

                <h3 className="text-sm font-semibold text-gray-900">
                  {template.name}
                </h3>
                <p className="mt-0.5 line-clamp-2 text-xs text-gray-500">
                  {template.description}
                </p>
                <div className="mt-2 flex flex-wrap gap-1">
                  {template.tags.slice(0, 3).map((tag) => (
                    <span
                      key={tag}
                      className="rounded-full bg-gray-100 px-2 py-0.5 text-[10px] text-gray-500"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Editor Panel */}
        <div className="space-y-6">
          {/* Live Editor */}
          {selectedTemplate && (
            <div className="rounded-xl border border-gray-200 bg-white p-6">
              <div className="mb-4 flex items-center gap-2">
                <div
                  className="h-3 w-3 rounded-full"
                  style={{ backgroundColor: selectedTemplate.preview_color }}
                />
                <h2 className="text-lg font-semibold text-gray-900">
                  {selectedTemplate.name}
                </h2>
              </div>

              {/* Preview */}
              <div
                className="mb-4 flex aspect-[9/16] max-h-64 items-center justify-center overflow-hidden rounded-lg"
                style={{ backgroundColor: "#1a1a2e" }}
              >
                <TemplatePreview
                  template={selectedTemplate}
                  mainText={mainText}
                  subText={subText}
                  large
                />
              </div>

              {/* Text Inputs */}
              <div className="space-y-3">
                <div>
                  <label className="mb-1 flex items-center gap-1.5 text-xs font-medium text-gray-700">
                    <Type className="h-3.5 w-3.5" /> Main Text
                  </label>
                  <input
                    type="text"
                    value={mainText}
                    onChange={(e) => setMainText(e.target.value)}
                    placeholder="Ronaldo Aura"
                    maxLength={25}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-red-500 focus:outline-none focus:ring-1 focus:ring-red-500"
                  />
                  <p className="mt-0.5 text-right text-[10px] text-gray-400">
                    {mainText.length}/25
                  </p>
                </div>
                {selectedTemplate.variables.includes("sub_text") && (
                  <div>
                    <label className="mb-1 flex items-center gap-1.5 text-xs font-medium text-gray-700">
                      <Tag className="h-3.5 w-3.5" /> Sub Text
                    </label>
                    <input
                      type="text"
                      value={subText}
                      onChange={(e) => setSubText(e.target.value)}
                      placeholder="Different breed entirely"
                      maxLength={40}
                      className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-red-500 focus:outline-none focus:ring-1 focus:ring-red-500"
                    />
                  </div>
                )}
              </div>

              {/* Quick Presets */}
              <div className="mt-4">
                <p className="mb-2 text-xs font-medium text-gray-500">Quick Fill</p>
                <div className="flex flex-wrap gap-1.5">
                  {QUICK_PRESETS.map((preset) => (
                    <button
                      key={preset.main}
                      onClick={() => {
                        setMainText(preset.main);
                        setSubText(preset.sub);
                      }}
                      className="rounded-full bg-gray-100 px-2.5 py-1 text-[11px] font-medium text-gray-600 hover:bg-gray-200"
                    >
                      {preset.main}
                    </button>
                  ))}
                </div>
              </div>

              {/* Save as Preset */}
              <div className="mt-4 border-t border-gray-100 pt-4">
                <p className="mb-2 text-xs font-medium text-gray-500">
                  Save as Custom Preset
                </p>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={presetName}
                    onChange={(e) => setPresetName(e.target.value)}
                    placeholder="My Ronaldo Template"
                    className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-red-500 focus:outline-none"
                  />
                  <button
                    onClick={handleSavePreset}
                    disabled={!presetName.trim() || saving}
                    className="flex items-center gap-1 rounded-lg bg-red-600 px-3 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-50"
                  >
                    {saving ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Save className="h-4 w-4" />
                    )}
                  </button>
                </div>
                {saveMsg && (
                  <p className="mt-1 text-xs text-green-600">{saveMsg}</p>
                )}
              </div>
            </div>
          )}

          {/* Saved Custom Templates */}
          {customTemplates.length > 0 && (
            <div className="rounded-xl border border-gray-200 bg-white p-6">
              <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold text-gray-900">
                <Star className="h-4 w-4 text-amber-500" />
                My Saved Presets
              </h2>
              <div className="space-y-2">
                {customTemplates.map((ct) => (
                  <div
                    key={ct.id}
                    className="flex items-center justify-between rounded-lg border border-gray-100 p-3"
                  >
                    <button
                      onClick={() => {
                        const base = templates.find((t) => t.id === ct.base_template_id);
                        if (base) setSelectedTemplate(base);
                        setMainText(ct.variables.main_text || "");
                        setSubText(ct.variables.sub_text || "");
                      }}
                      className="text-left"
                    >
                      <p className="text-sm font-medium text-gray-900">
                        {ct.name}
                      </p>
                      <p className="text-[11px] text-gray-500">
                        {ct.variables.main_text} &middot; {ct.base_template_id}
                      </p>
                    </button>
                    <button
                      onClick={() => handleDeleteCustom(ct.id)}
                      className="rounded p-1 text-gray-400 hover:bg-red-50 hover:text-red-600"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* How Templates Work */}
          <div className="rounded-xl border border-blue-100 bg-blue-50 p-4">
            <h3 className="flex items-center gap-1.5 text-sm font-medium text-blue-800">
              <Sparkles className="h-4 w-4" /> How It Works
            </h3>
            <ol className="mt-2 space-y-1 text-xs text-blue-700">
              <li>1. Upload a video and run analysis</li>
              <li>2. AI detects highlights (goals, skills, aura moments)</li>
              <li>3. Templates are auto-selected based on content</li>
              <li>4. Overlay text is generated by the LLM</li>
              <li>5. Shorts are rendered with templates via FFmpeg</li>
              <li>6. You can change templates and re-render anytime</li>
            </ol>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Template Visual Preview Component ───────────────────────────────

function TemplatePreview({
  template,
  mainText,
  subText,
  large,
}: {
  template: Template;
  mainText: string;
  subText: string;
  large?: boolean;
}) {
  const styles = TEMPLATE_PREVIEW_STYLES[template.id] || TEMPLATE_PREVIEW_STYLES.default;
  const scale = large ? 1 : 0.65;

  return (
    <div
      className="relative flex h-full w-full flex-col items-center justify-center overflow-hidden"
      style={{ fontSize: `${scale * 100}%` }}
    >
      {/* Background elements */}
      {styles.bgElements}

      {/* Main text */}
      <p
        className="relative z-10 px-3 text-center font-bold leading-tight"
        style={styles.mainStyle}
      >
        {mainText}
      </p>

      {/* Sub text */}
      {subText && (
        <p
          className="relative z-10 mt-1 px-3 text-center"
          style={styles.subStyle}
        >
          {subText}
        </p>
      )}
    </div>
  );
}

// ── Preview Style Definitions ───────────────────────────────────────

const TEMPLATE_PREVIEW_STYLES: Record<
  string,
  {
    mainStyle: React.CSSProperties;
    subStyle: React.CSSProperties;
    bgElements?: React.ReactNode;
  }
> = {
  aura: {
    mainStyle: {
      fontSize: "1.5em",
      color: "white",
      textShadow: "0 0 20px rgba(139,92,246,0.8), 0 0 40px rgba(139,92,246,0.4), 2px 2px 4px rgba(0,0,0,0.8)",
    },
    subStyle: {
      fontSize: "0.75em",
      color: "rgba(255,255,255,0.8)",
      textShadow: "1px 1px 2px rgba(0,0,0,0.6)",
    },
  },
  hype: {
    mainStyle: {
      fontSize: "1.8em",
      color: "white",
      textShadow: "3px 3px 0 #EF4444, -1px -1px 0 #EF4444",
      letterSpacing: "0.05em",
    },
    subStyle: {
      fontSize: "0.7em",
      color: "white",
      backgroundColor: "rgba(239,68,68,0.85)",
      padding: "2px 8px",
      borderRadius: "4px",
    },
  },
  commentary: {
    mainStyle: {
      fontSize: "1.1em",
      color: "white",
      position: "absolute",
      bottom: "30%",
      left: "8%",
      textAlign: "left",
    },
    subStyle: {
      fontSize: "0.65em",
      color: "rgba(255,255,255,0.7)",
      position: "absolute",
      bottom: "22%",
      left: "8%",
      textAlign: "left",
    },
    bgElements: (
      <>
        <div className="absolute bottom-0 left-0 right-0 h-2/5 bg-gradient-to-t from-black/80 to-transparent" />
        <div className="absolute bottom-[40%] left-0 right-0 h-1 bg-blue-500/90" />
      </>
    ),
  },
  cinematic: {
    mainStyle: {
      fontSize: "1em",
      color: "white",
      position: "absolute",
      bottom: "8%",
      letterSpacing: "0.1em",
    },
    subStyle: {
      fontSize: "0.55em",
      color: "rgba(255,255,255,0.5)",
      position: "absolute",
      top: "5%",
      letterSpacing: "0.15em",
    },
    bgElements: (
      <>
        <div className="absolute top-0 left-0 right-0 h-[15%] bg-black/95" />
        <div className="absolute bottom-0 left-0 right-0 h-[15%] bg-black/95" />
      </>
    ),
  },
  minimal: {
    mainStyle: {
      fontSize: "0.9em",
      color: "white",
      backgroundColor: "rgba(0,0,0,0.4)",
      padding: "4px 12px",
      borderRadius: "6px",
      position: "absolute",
      bottom: "15%",
    },
    subStyle: { display: "none" },
  },
  versus: {
    mainStyle: {
      fontSize: "1.2em",
      color: "white",
      textShadow: "2px 2px 4px rgba(0,0,0,0.8)",
    },
    subStyle: {
      fontSize: "1.2em",
      color: "white",
      textShadow: "2px 2px 4px rgba(0,0,0,0.8)",
      marginTop: "0.5em",
    },
    bgElements: (
      <>
        <div className="absolute inset-x-0 top-1/2 -translate-y-1/2 h-[30%] bg-black/70" />
        <span className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-20 text-lg font-black text-amber-400" style={{textShadow: "2px 2px 4px rgba(0,0,0,0.8)"}}>
          VS
        </span>
      </>
    ),
  },
  countdown: {
    mainStyle: {
      fontSize: "2em",
      color: "white",
      position: "absolute",
      top: "5%",
      left: "5%",
      backgroundColor: "rgba(239,68,68,0.9)",
      width: "1.5em",
      height: "1.5em",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      borderRadius: "4px",
      lineHeight: "1",
    },
    subStyle: {
      fontSize: "0.8em",
      color: "white",
      backgroundColor: "rgba(0,0,0,0.5)",
      padding: "4px 10px",
      borderRadius: "6px",
      position: "absolute",
      bottom: "12%",
    },
  },
  goal_flash: {
    mainStyle: {
      fontSize: "1.8em",
      color: "white",
      textShadow: "3px 3px 0 #DC2626, 0 0 20px rgba(220,38,38,0.5)",
      letterSpacing: "0.05em",
    },
    subStyle: {
      fontSize: "0.7em",
      color: "rgba(255,255,255,0.9)",
      textShadow: "1px 1px 2px rgba(0,0,0,0.6)",
    },
    bgElements: (
      <div className="absolute inset-0 border-4 border-red-600/80 rounded-lg pointer-events-none" />
    ),
  },
  default: {
    mainStyle: { fontSize: "1.2em", color: "white", textShadow: "1px 1px 3px rgba(0,0,0,0.8)" },
    subStyle: { fontSize: "0.7em", color: "rgba(255,255,255,0.7)" },
  },
};

// ── Quick Presets for Football Content ───────────────────────────────

const QUICK_PRESETS = [
  { main: "Ronaldo Aura", sub: "Different breed entirely" },
  { main: "Prime Messi", sub: "The GOAT does it again" },
  { main: "GOAAAL!", sub: "What a strike!" },
  { main: "Neymar Magic", sub: "Skills on another level" },
  { main: "Haaland Mode", sub: "The machine keeps scoring" },
  { main: "Top 5", sub: "Best goals of the week" },
  { main: "NO WAY!", sub: "You won't believe this" },
  { main: "The Beautiful Game", sub: "Football at its finest" },
];
