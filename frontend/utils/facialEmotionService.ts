import Constants from 'expo-constants';

export interface EmotionScores {
  angry: number;
  disgust: number;
  fear: number;
  happy: number;
  neutral: number;
  sad: number;
  surprise: number;
}

export interface EmotionAnalysisResponse {
  success: boolean;
  face_detected: boolean;
  faces_detected: number;
  provider: string | null;
  emotion: string;
  confidence: number;
  scores: EmotionScores;
  message?: string;
}

export interface FusionResponse {
  sign: string;
  emotion: string;
  confidence?: number;
  status: 'aligned' | 'mismatch' | 'low_confidence';
  message: string;
  expected_emotions: string[];
}

function resolveBackendBaseUrl(): string {
  const envUrl = process.env.EXPO_PUBLIC_BACKEND_URL;
  if (envUrl && envUrl.trim().length > 0) {
    return envUrl.trim().replace(/\/$/, '');
  }

  const hostUri = Constants.expoConfig?.hostUri;
  const host = hostUri?.split(':')[0];

  if (host) {
    return `http://${host}:8000`;
  }

  return 'http://localhost:8000';
}

export function getBackendBaseUrl(): string {
  return resolveBackendBaseUrl();
}

export async function checkFacialApiHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${resolveBackendBaseUrl()}/api/facial-emotion/health`);
    return response.ok;
  } catch {
    return false;
  }
}

export async function analyzeEmotionFromBase64(imageBase64: string): Promise<EmotionAnalysisResponse> {
  return analyzeEmotionFromSnapshot(imageBase64);
}

export async function analyzeEmotionFromSnapshot(imageBase64: string): Promise<EmotionAnalysisResponse> {
  const baseUrl = resolveBackendBaseUrl();
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 10000);

  try {
    const response = await fetch(`${baseUrl}/api/facial-emotion/emotion`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ image: imageBase64 }),
      signal: controller.signal,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(errorText || `Emotion API request failed (${response.status})`);
    }

    return (await response.json()) as EmotionAnalysisResponse;
  } finally {
    clearTimeout(timeout);
  }
}

export async function interpretFusion(sign: string, emotion: string, confidence?: number): Promise<FusionResponse> {
  const response = await fetch(`${resolveBackendBaseUrl()}/api/fusion/interpret`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ sign, emotion, confidence }),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `Fusion API request failed (${response.status})`);
  }

  return (await response.json()) as FusionResponse;
}
