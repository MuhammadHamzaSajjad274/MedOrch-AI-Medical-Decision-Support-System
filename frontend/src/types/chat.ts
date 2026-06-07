export type Modality = "brain_mri" | "chest_xray" | "skin_lesion";

export interface Citation {
  source: string;
  snippet: string;
  link?: string;
}

export interface VisionResult {
  modality: Modality;
  label: string;
  confidence: number;
  class_names: string[];
  heatmap_base64?: string | null;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  visionResult?: VisionResult;
  imageBase64?: string | null;
}

export interface ChatRequest {
  message: string;
  modality?: Modality | null;
  image_base64?: string | null;
}

export interface ChatResponse {
  message: string;
  citations: Citation[];
  vision_result: VisionResult | null;
}
