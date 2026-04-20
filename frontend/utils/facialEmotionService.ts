import AsyncStorage from '@react-native-async-storage/async-storage';
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

export interface EmotionDatasetInfoResponse {
  dataset_dir: string;
  total_images: number;
  per_emotion: Record<string, number>;
  classes_with_data: string[];
}

export interface EmotionTrainingJobResponse {
  success: boolean;
  message: string;
  job: {
    job_id: string;
    status: string;
    epochs: number;
    batch_size: number;
    started_at: string;
  };
}

export interface EmotionTrainingStatusResponse {
  running?: boolean;
  last_job?: {
    job_id: string;
    status: string;
    epochs: number;
    batch_size: number;
    started_at: string;
    finished_at?: string | null;
    summary?: Record<string, unknown>;
  };
  jobs_count?: number;
  job_id?: string;
  status?: string;
  summary?: Record<string, unknown>;
}

export interface EmotionModelInfoResponse {
  task: string;
  available_emotions: string[];
  use_fen: boolean;
  providers: {
    deepface: boolean;
    fer: boolean;
  };
  fen_model: {
    ready: boolean;
    model_path: string;
    message?: string;
  };
}

const BACKEND_URL_KEY = 'signlanguage_backend_url';
const DEFAULT_BACKEND_URL = 'https://improved-space-chainsaw-97rxv5p9r4w2q76-8000.app.github.dev';
const EMOTION_REQUEST_TIMEOUT_MS = 20000;

function normalizeBackendUrl(value: string): string {
  return value.trim().replace(/\/+$/, '');
}

function isUsableHost(host: string): boolean {
  if (!host) {
    return false;
  }

  const lowerHost = host.toLowerCase();
  if (lowerHost.includes('exp.direct') || lowerHost.includes('expo.dev')) {
    return false;
  }

  return true;
}

function isLocalBackendUrl(url: string): boolean {
  const normalized = url.trim().toLowerCase();
  return normalized.includes('localhost') || normalized.includes('127.0.0.1');
}

function deriveBackendFromWebHost(): string | null {
  if (typeof window === 'undefined' || !window.location?.host) {
    return null;
  }

  const host = window.location.host;
  if (!host.includes('.app.github.dev')) {
    return null;
  }

  const backendHost = host.replace(/-\d+\.app\.github\.dev$/, '-8000.app.github.dev');
  return `https://${backendHost}`;
}

async function getStoredBackendBaseUrl(): Promise<string | null> {
  try {
    const value = await AsyncStorage.getItem(BACKEND_URL_KEY);
    if (!value || value.trim().length === 0) {
      return null;
    }

    const normalized = normalizeBackendUrl(value);
    if (isLocalBackendUrl(normalized)) {
      // Remove stale localhost values so subsequent runs don't reuse them.
      await AsyncStorage.removeItem(BACKEND_URL_KEY);
      return null;
    }

    return normalized;
  } catch {
    return null;
  }
}

function resolveDefaultBackendBaseUrl(): string {
  const webDerivedUrl = deriveBackendFromWebHost();
  if (webDerivedUrl) {
    return normalizeBackendUrl(webDerivedUrl);
  }

  const envUrl = process.env.EXPO_PUBLIC_BACKEND_URL;
  if (envUrl && envUrl.trim().length > 0) {
    return normalizeBackendUrl(envUrl);
  }

  const hostUri = Constants.expoConfig?.hostUri;
  const host = hostUri?.split(':')[0];

  if (host && isUsableHost(host)) {
    return `http://${host}:8000`;
  }

  const extraUrl = Constants.expoConfig?.extra?.backendUrl;
  if (typeof extraUrl === 'string' && extraUrl.trim().length > 0) {
    return normalizeBackendUrl(extraUrl);
  }

  return DEFAULT_BACKEND_URL;
}

function collectBackendBaseUrlCandidates(): string[] {
  const candidates: string[] = [];

  const webDerivedUrl = deriveBackendFromWebHost();
  if (webDerivedUrl) {
    candidates.push(normalizeBackendUrl(webDerivedUrl));
  }

  const envUrl = process.env.EXPO_PUBLIC_BACKEND_URL;
  if (envUrl && envUrl.trim().length > 0) {
    candidates.push(normalizeBackendUrl(envUrl));
  }

  const hostUri = Constants.expoConfig?.hostUri;
  const host = hostUri?.split(':')[0];
  if (host && isUsableHost(host)) {
    candidates.push(`http://${host}:8000`);
  }

  const extraUrl = Constants.expoConfig?.extra?.backendUrl;
  if (typeof extraUrl === 'string' && extraUrl.trim().length > 0) {
    candidates.push(normalizeBackendUrl(extraUrl));
  }

  candidates.push(DEFAULT_BACKEND_URL);

  return Array.from(new Set(candidates));
}

async function getBackendBaseUrlCandidates(): Promise<string[]> {
  const candidates: string[] = [];
  const storedUrl = await getStoredBackendBaseUrl();
  if (storedUrl) {
    candidates.push(storedUrl);
  }

  candidates.push(...collectBackendBaseUrlCandidates());
  return Array.from(new Set(candidates));
}

async function fetchWithTimeout(
  url: string,
  init: RequestInit,
  timeoutMs: number,
): Promise<Response> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(url, { ...init, signal: controller.signal });
  } finally {
    clearTimeout(timeout);
  }
}

function toNumber(value: unknown, fallback = 0): number {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function normalizeScores(rawScores: unknown, emotion: string, confidence: number): EmotionScores {
  const base: EmotionScores = {
    angry: 0,
    disgust: 0,
    fear: 0,
    happy: 0,
    neutral: 0,
    sad: 0,
    surprise: 0,
  };

  if (!rawScores || typeof rawScores !== 'object') {
    if (emotion in base) {
      base[emotion as keyof EmotionScores] = confidence;
    }
    return base;
  }

  const scoreMap = rawScores as Record<string, unknown>;
  return {
    angry: toNumber(scoreMap.angry, 0),
    disgust: toNumber(scoreMap.disgust, 0),
    fear: toNumber(scoreMap.fear, 0),
    happy: toNumber(scoreMap.happy, 0),
    neutral: toNumber(scoreMap.neutral, 0),
    sad: toNumber(scoreMap.sad, 0),
    surprise: toNumber(scoreMap.surprise, 0),
  };
}

function normalizeEmotionResponse(payload: unknown): EmotionAnalysisResponse {
  const record = (payload && typeof payload === 'object') ? (payload as Record<string, unknown>) : {};
  const emotion = String(record.emotion ?? 'neutral');
  const confidence = toNumber(record.confidence, 0);
  const hasFaceDetectedFlag = typeof record.face_detected !== 'undefined';
  const faceDetected = hasFaceDetectedFlag ? Boolean(record.face_detected) : true;
  const facesDetected = toNumber(record.faces_detected, faceDetected ? 1 : 0);

  return {
    success: typeof record.success === 'boolean' ? record.success : true,
    face_detected: faceDetected,
    faces_detected: facesDetected,
    provider: record.provider == null ? 'unknown' : String(record.provider),
    emotion,
    confidence,
    scores: normalizeScores(record.scores, emotion, confidence),
    message: typeof record.message === 'string' ? record.message : undefined,
  };
}

export async function resolveBackendBaseUrl(): Promise<string> {
  const storedUrl = await getStoredBackendBaseUrl();
  return storedUrl ?? resolveDefaultBackendBaseUrl();
}

export function getBackendBaseUrl(): string {
  return resolveDefaultBackendBaseUrl();
}

export async function saveBackendBaseUrl(url: string): Promise<void> {
  await AsyncStorage.setItem(BACKEND_URL_KEY, normalizeBackendUrl(url));
}

export async function clearBackendBaseUrl(): Promise<void> {
  await AsyncStorage.removeItem(BACKEND_URL_KEY);
}

export async function checkFacialApiHealth(): Promise<boolean> {
  const candidates = await getBackendBaseUrlCandidates();

  for (const baseUrl of candidates) {
    try {
      const response = await fetchWithTimeout(`${baseUrl}/api/facial-emotion/health`, {}, 4000);
      if (response.ok) {
        await saveBackendBaseUrl(baseUrl);
        return true;
      }
    } catch {
      // Try next candidate URL.
    }
  }

  return false;
}

export async function analyzeEmotionFromBase64(imageBase64: string): Promise<EmotionAnalysisResponse> {
  return analyzeEmotionFromSnapshot(imageBase64);
}

export async function analyzeEmotionFromSnapshot(imageBase64: string): Promise<EmotionAnalysisResponse> {
  const candidates = await getBackendBaseUrlCandidates();
  let lastError: Error | null = null;

  for (const baseUrl of candidates) {
    try {
      const attempts: { endpoint: string; body: Record<string, string> }[] = [
        { endpoint: '/api/facial-emotion/emotion', body: { image: imageBase64 } },
        { endpoint: '/api/facial-emotion/analyze-frame', body: { image_base64: imageBase64 } },
        { endpoint: '/api/emotion/predict', body: { image: imageBase64 } },
      ];

      for (const attempt of attempts) {
        const response = await fetchWithTimeout(
          `${baseUrl}${attempt.endpoint}`,
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(attempt.body),
          },
          EMOTION_REQUEST_TIMEOUT_MS,
        );

        if (!response.ok) {
          const errorText = await response.text();
          lastError = new Error(errorText || `Emotion endpoint failed (${response.status})`);
          continue;
        }

        const payload = await response.json();
        await saveBackendBaseUrl(baseUrl);
        return normalizeEmotionResponse(payload);
      }
    } catch (error) {
      lastError = error instanceof Error ? error : new Error('Emotion API request failed');
    }
  }

  throw lastError ?? new Error('Emotion API request failed');
}

export async function interpretFusion(sign: string, emotion: string, confidence?: number): Promise<FusionResponse> {
  const baseUrl = await resolveBackendBaseUrl();
  const response = await fetch(`${baseUrl}/api/fusion/interpret`, {
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

export async function collectEmotionSampleFromBase64(
  imageBase64: string,
  label: string,
): Promise<{ success: boolean; sample: Record<string, unknown>; dataset: EmotionDatasetInfoResponse }> {
  const baseUrl = await resolveBackendBaseUrl();
  const response = await fetch(
    `${baseUrl}/api/facial-emotion/collect-sample-frame?label=${encodeURIComponent(label)}`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ image_base64: imageBase64 }),
    }
  );

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `Sample collection failed (${response.status})`);
  }

  return (await response.json()) as {
    success: boolean;
    sample: Record<string, unknown>;
    dataset: EmotionDatasetInfoResponse;
  };
}

export async function getEmotionDatasetInfo(): Promise<EmotionDatasetInfoResponse> {
  const baseUrl = await resolveBackendBaseUrl();
  const response = await fetch(`${baseUrl}/api/facial-emotion/dataset-info`);
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `Dataset info request failed (${response.status})`);
  }

  return (await response.json()) as EmotionDatasetInfoResponse;
}

export async function startEmotionTraining(epochs = 30, batchSize = 32): Promise<EmotionTrainingJobResponse> {
  const baseUrl = await resolveBackendBaseUrl();
  const response = await fetch(
    `${baseUrl}/api/facial-emotion/train?epochs=${epochs}&batch_size=${batchSize}`,
    { method: 'POST' }
  );
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `Training start failed (${response.status})`);
  }

  return (await response.json()) as EmotionTrainingJobResponse;
}

export async function getEmotionTrainingStatus(jobId?: string): Promise<EmotionTrainingStatusResponse> {
  const baseUrl = await resolveBackendBaseUrl();
  const query = jobId ? `?job_id=${encodeURIComponent(jobId)}` : '';
  const response = await fetch(`${baseUrl}/api/facial-emotion/training-status${query}`);
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `Training status request failed (${response.status})`);
  }

  return (await response.json()) as EmotionTrainingStatusResponse;
}

export async function getEmotionModelInfo(): Promise<EmotionModelInfoResponse> {
  const baseUrl = await resolveBackendBaseUrl();
  const response = await fetch(`${baseUrl}/api/facial-emotion/model-info`);
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `Model info request failed (${response.status})`);
  }

  return (await response.json()) as EmotionModelInfoResponse;
}
