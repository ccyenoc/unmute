import { Colors } from '@/constants/theme';
import { useColorScheme } from '@/hooks/use-color-scheme';
import {
  analyzeEmotionFromBase64,
  checkFacialApiHealth,
  EmotionAnalysisResponse,
  FusionResponse,
  getEmotionModelInfo,
  interpretFusion,
} from '@/utils/facialEmotionService';
import { FacialEmotionSnapshot, simulateSignTranslation, storeTranslation } from '@/utils/translationService';
import { useFocusEffect } from '@react-navigation/native';
import { CameraView, useCameraPermissions } from 'expo-camera';
import React, { useCallback, useRef, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

const toHistoryScores = (scores: EmotionAnalysisResponse['scores']): Record<string, number> => ({
  angry: scores.angry,
  disgust: scores.disgust,
  fear: scores.fear,
  happy: scores.happy,
  neutral: scores.neutral,
  sad: scores.sad,
  surprise: scores.surprise,
});

export default function TranslatorScreen() {
  const colorScheme = useColorScheme() ?? 'light';
  const actionButtonTextColor = '#11181C';
  const [permission, requestPermission] = useCameraPermissions();
  const [isRecording, setIsRecording] = useState(false);
  const [translation, setTranslation] = useState<string | null>(null);
  const [emotionResult, setEmotionResult] = useState<EmotionAnalysisResponse | null>(null);
  const [fusionResult, setFusionResult] = useState<FusionResponse | null>(null);
  const [apiConnected, setApiConnected] = useState<boolean | null>(null);
  const [fenReady, setFenReady] = useState<boolean | null>(null);
  const [fenModelMessage, setFenModelMessage] = useState<string | null>(null);
  const [fenMetadataSource, setFenMetadataSource] = useState<string | null>(null);
  const [backendStatusLabel, setBackendStatusLabel] = useState('Checking...');
  const [isProcessing, setIsProcessing] = useState(false);
  const [emotionErrorMessage, setEmotionErrorMessage] = useState<string | null>(null);
  const cameraRef = useRef<CameraView>(null);



  React.useEffect(() => {
    if (!permission?.granted) {
      requestPermission();
    }
  }, [permission, requestPermission]);

  useFocusEffect(
    useCallback(() => {
      let mounted = true;

      setBackendStatusLabel('Checking...');
      setApiConnected(null);
      setFenReady(null);
      setFenModelMessage(null);
      setFenMetadataSource(null);

      const refreshBackendState = async () => {
        const healthResult = await checkFacialApiHealth().catch(() => false);
        if (!mounted) {
          return;
        }

        setApiConnected(healthResult);
        setBackendStatusLabel('');

        if (!healthResult) {
          setFenReady(false);
          setFenModelMessage('Backend is not reachable');
          setFenMetadataSource(null);
          return;
        }

        try {
          const modelInfo = await getEmotionModelInfo();
          if (!mounted) {
            return;
          }
          setFenReady(modelInfo.fen_model.ready);
          setFenModelMessage(modelInfo.fen_model.message ?? null);
          setFenMetadataSource(modelInfo.fen_model.metadata_source ?? null);
        } catch {
          if (!mounted) {
            return;
          }
          // Keep API as connected and avoid showing a misleading hard error on temporary model-info failures.
          setFenReady(null);
          setFenModelMessage(null);
          setFenMetadataSource(null);
        }
      };

      void refreshBackendState();

      return () => {
        mounted = false;
      };
    }, [])
  );

  const handleStartTranslation = async () => {
    if (!permission?.granted) {
      Alert.alert('Camera Permission', 'Camera permission is required to use the translator.');
      return;
    }

    if (!cameraRef.current) {
      Alert.alert('Camera Error', 'Camera is not ready yet. Please try again.');
      return;
    }

    setIsRecording(true);
    setTranslation(null);
    setEmotionResult(null);
    setEmotionErrorMessage(null);
    setFusionResult(null);
    setIsProcessing(true);

    try {
      const translationPromise = simulateSignTranslation();
      // Give the camera a tiny moment to settle, but avoid a long blocking delay.
      await new Promise((resolve) => setTimeout(resolve, 120));
      const snapshot = await cameraRef.current.takePictureAsync({
        base64: true,
        quality: 0.5,
        skipProcessing: true,
      });

      const result = await translationPromise;
      setTranslation(result);
      let historyEmotionSnapshot: FacialEmotionSnapshot | null = null;

      if (snapshot.base64) {
        try {
          const emotion = await analyzeEmotionFromBase64(snapshot.base64);
          setEmotionResult(emotion);
          setEmotionErrorMessage(null);

          historyEmotionSnapshot = {
            emotion: emotion.emotion,
            confidence: emotion.confidence,
            provider: emotion.provider,
            faces_detected: emotion.faces_detected,
            scores: toHistoryScores(emotion.scores),
          };

          if (emotion.face_detected) {
            try {
              const fusion = await interpretFusion(result, emotion.emotion, emotion.confidence);
              setFusionResult(fusion);
              historyEmotionSnapshot = {
                emotion: emotion.emotion,
                confidence: emotion.confidence,
                provider: emotion.provider,
                faces_detected: emotion.faces_detected,
                scores: toHistoryScores(emotion.scores),
                fusion_status: fusion.status,
              };
            } catch {
              setFusionResult(null);
            }
          }
        } catch (error) {
          const reason = error instanceof Error ? error.message : 'Unknown error';
          const shortReason = reason.length > 120 ? `${reason.slice(0, 120)}...` : reason;
          setEmotionResult(null);
          if (reason.toLowerCase().includes('abort') || reason.toLowerCase().includes('aborted')) {
            setEmotionErrorMessage('Facial expression request timed out. Try again with a clearer face and better connection.');
          } else {
            setEmotionErrorMessage(`Facial expression API unavailable: ${shortReason}`);
          }
          setFusionResult(null);
        }
      }

      await storeTranslation(result, historyEmotionSnapshot);
      await speakTranslation(result);
    } catch {
      Alert.alert('Error', 'Failed to process sign language.');
    } finally {
      setIsRecording(false);
      setIsProcessing(false);
    }
  };

  const speakTranslation = async (text: string) => {
    try {
      // In a real app, you would use a text-to-speech service
      // For now, we'll just log that we would speak
      console.log('Speaking:', text);
      // This would use expo-av or a TTS service
    } catch {
      console.error('Speech error');
    }
  };

  const renderEmotionCard = () => {
    if (isRecording || !emotionResult) {
      return null;
    }

    const confidencePercent = emotionResult.confidence <= 1
      ? emotionResult.confidence * 100
      : emotionResult.confidence;
    const confidencePercentRounded = Number(confidencePercent.toFixed(2));

    const payload = {
      emotion: emotionResult.emotion,
      confidence: confidencePercentRounded,
      provider: emotionResult.provider,
      faces_detected: emotionResult.faces_detected,
      fusion_status: fusionResult?.status ?? 'aligned',
      scores: emotionResult.scores,
    };

    return (
      <View style={[styles.emotionCard, { borderColor: Colors[colorScheme].tabIconDefault }]}>
        <View style={styles.emotionCardHeader}>
          <Text style={[styles.emotionCardTitle, { color: Colors[colorScheme].text }]}>Facial Expression API</Text>
          <TouchableOpacity
            onPress={() => {
              setEmotionResult(null);
              setFusionResult(null);
              setEmotionErrorMessage(null);
            }}
          >
            <Text style={[styles.emotionCardClose, { color: Colors[colorScheme].tabIconDefault }]}>✕</Text>
          </TouchableOpacity>
        </View>

        <View style={styles.emotionCardContent}>
          <View style={styles.emotionMetaRow}>
            <View style={[styles.emotionMetaPill, { backgroundColor: 'rgba(34, 160, 107, 0.1)' }]}>
              <Text style={[styles.emotionMetaLabel, { color: Colors[colorScheme].text }]}>Emotion</Text>
              <Text style={[styles.emotionMetaValue, { color: '#22A06B' }]}>{emotionResult.emotion.toUpperCase()}</Text>
            </View>
            <View style={[styles.emotionMetaPill, { backgroundColor: 'rgba(0, 122, 255, 0.1)' }]}>
              <Text style={[styles.emotionMetaLabel, { color: Colors[colorScheme].text }]}>Confidence</Text>
              <Text style={[styles.emotionMetaValue, { color: '#007AFF' }]}>{confidencePercentRounded.toFixed(1)}%</Text>
            </View>
          </View>

          {emotionResult?.message ? (
            <View style={[styles.emotionNoticeBox, { backgroundColor: 'rgba(255, 149, 0, 0.1)', borderColor: 'rgba(255, 149, 0, 0.3)' }]}>
              <Text style={[styles.emotionNoticeText, { color: '#FF9500' }]}>{emotionResult.message}</Text>
            </View>
          ) : null}

          <ScrollView
            style={styles.emotionPayloadScroll}
            contentContainerStyle={styles.emotionPayloadScrollContent}
            nestedScrollEnabled
            showsVerticalScrollIndicator
          >
            <Text style={styles.emotionPayloadText}>{JSON.stringify(payload, null, 2)}</Text>
          </ScrollView>
        </View>
      </View>
    );
  };


  if (!permission) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: Colors[colorScheme].background }]}>
        <ActivityIndicator size="large" />
      </SafeAreaView>
    );
  }

  if (!permission.granted) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: Colors[colorScheme].background }]}>
        <Text style={{ textAlign: 'center' }}>We need your permission to show the camera</Text>
        <TouchableOpacity style={styles.button} onPress={requestPermission}>
          <Text style={[styles.buttonText, { color: actionButtonTextColor }]}>Grant Permission</Text>
        </TouchableOpacity>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: Colors[colorScheme].background }]}>
      <ScrollView style={styles.scrollContent} contentContainerStyle={styles.scrollContentContainer}>
        {/* Camera Section */}
        <View style={styles.cameraSection}>
          <CameraView
            ref={cameraRef}
            style={styles.camera}
            facing="front"
          />
          {isRecording && (
            <View style={styles.recordingIndicator}>
              <View style={styles.recordingDot} />
              <Text style={styles.recordingText}>Recording...</Text>
            </View>
          )}
        </View>

        {/* Emotion Card Section */}
        {renderEmotionCard()}

        {/* Backend Status Section */}
        <View style={styles.controlsContainer}>
          

          {fenModelMessage ? (
            <Text style={[styles.fenStatusMessage, { color: Colors[colorScheme].tabIconDefault }]}> 
              {fenModelMessage}
            </Text>
          ) : null}

          {fenMetadataSource && fenMetadataSource !== 'training' ? (
            <Text style={[styles.fenStatusMessage, { color: Colors[colorScheme].tabIconDefault }]}> 
              FEN: {fenMetadataSource}
            </Text>
          ) : null}

          {emotionErrorMessage ? (
            <Text style={[styles.fenStatusMessage, { color: '#D92D20' }]}> 
              {emotionErrorMessage}
            </Text>
          ) : null}

          {/* Translator UI Section */}
          {isProcessing ? (
            <View style={styles.processingContainer}>
              <ActivityIndicator size="large" color={Colors[colorScheme].tint} />
              <Text style={[styles.processingText, { color: Colors[colorScheme].text }]}>
                Processing sign language and emotion...
              </Text>
            </View>
          ) : translation ? (
            <View style={[styles.translationResultContainer, { borderLeftColor: Colors[colorScheme].tint }]}>
              <Text style={[styles.translationLabel, { color: Colors[colorScheme].tabIconDefault }]}>
                Translation Result
              </Text>
              <Text style={[styles.translationText, { color: Colors[colorScheme].text }]}>
                {translation}
              </Text>
            </View>
          ) : (
            <Text style={[styles.instructionText, { color: Colors[colorScheme].tabIconDefault }]}>
              Position yourself in front of the camera
            </Text>
          )}

          {/* Start Button */}
          <TouchableOpacity
            style={[
              styles.button,
              styles.startButton,
              {
                opacity: isRecording || isProcessing ? 0.6 : 1,
              },
            ]}
            onPress={handleStartTranslation}
            disabled={isRecording || isProcessing}
          >
            <Text style={[styles.buttonText, { color: actionButtonTextColor }]}>
              {isRecording ? 'Recording...' : 'Start Translation'}
            </Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </SafeAreaView>
  );

}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollContent: {
    flex: 1,
  },
  scrollContentContainer: {
    paddingBottom: 20,
  },
  cameraSection: {
    height: 320,
    borderRadius: 12,
    overflow: 'hidden',
    margin: 8,
    marginBottom: 12,
  },
  camera: {
    flex: 1,
  },
  recordingIndicator: {
    position: 'absolute',
    top: 16,
    right: 16,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 20,
  },
  recordingDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#FF3B30',
    marginRight: 8,
  },
  recordingText: {
    color: '#FFFFFF',
    fontWeight: '600',
  },
  emotionCard: {
    marginHorizontal: 8,
    marginBottom: 12,
    borderWidth: 1,
    borderRadius: 12,
    padding: 12,
    backgroundColor: 'rgba(14, 18, 24, 0.5)',
  },
  emotionCardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  emotionCardTitle: {
    fontSize: 14,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  emotionCardClose: {
    fontSize: 18,
    fontWeight: '600',
  },
  emotionCardContent: {
    gap: 10,
  },
  emotionMetaRow: {
    flexDirection: 'row',
    gap: 10,
  },
  emotionMetaPill: {
    flex: 1,
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 10,
    alignItems: 'center',
  },
  emotionMetaLabel: {
    fontSize: 11,
    fontWeight: '600',
    opacity: 0.7,
  },
  emotionMetaValue: {
    fontSize: 16,
    fontWeight: '700',
    marginTop: 4,
  },
  emotionPayloadScroll: {
    maxHeight: 210,
    borderRadius: 10,
    backgroundColor: 'rgba(2, 6, 12, 0.62)',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.12)',
  },
  emotionPayloadScrollContent: {
    padding: 10,
  },
  emotionPayloadText: {
    color: '#E9F0FF',
    fontSize: 11,
    lineHeight: 16,
    fontFamily: 'monospace',
  },
  emotionOverlayCard: {
    position: 'absolute',
    width: 220,
    maxHeight: 300,
    backgroundColor: 'rgba(14, 18, 24, 0.9)',
    borderRadius: 14,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.15)',
    padding: 12,
    boxShadow: '0px 8px 18px rgba(0, 0, 0, 0.28)',
    zIndex: 30,
    elevation: 30,
  },
  emotionOverlayHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  emotionOverlayTitle: {
    color: '#F5F8FF',
    fontSize: 13,
    fontWeight: '700',
    letterSpacing: 0.3,
  },
  emotionOverlaySubtitle: {
    color: 'rgba(231, 240, 255, 0.75)',
    fontSize: 10,
    marginTop: 2,
  },
  emotionOverlayActions: {
    flexDirection: 'row',
    gap: 6,
  },
  zoomControl: {
    width: 26,
    height: 26,
    borderRadius: 13,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.35)',
    backgroundColor: 'rgba(255,255,255,0.14)',
  },
  zoomControlText: {
    color: '#F5F8FF',
    fontSize: 16,
    fontWeight: '700',
    lineHeight: 18,
  },
  overlayMetaRow: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 8,
  },
  metaPill: {
    flex: 1,
    borderRadius: 10,
    backgroundColor: 'rgba(255,255,255,0.1)',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.16)',
    paddingVertical: 6,
    paddingHorizontal: 8,
  },
  metaPillLabel: {
    color: 'rgba(225, 238, 255, 0.72)',
    fontSize: 9,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  metaPillValue: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '700',
    marginTop: 2,
  },
  emotionOverlayScroll: {
    maxHeight: 220,
    borderRadius: 10,
    backgroundColor: 'rgba(2, 6, 12, 0.62)',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.12)',
  },
  emotionOverlayScrollContent: {
    padding: 10,
  },
  emotionOverlayPayload: {
    color: '#E9F0FF',
    fontSize: 11,
    lineHeight: 16,
    fontFamily: 'monospace',
  },
  emotionOverlayFooter: {
    marginTop: 10,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  emotionNoticeBox: {
    marginTop: 8,
    paddingHorizontal: 10,
    paddingVertical: 8,
    borderRadius: 10,
    backgroundColor: 'rgba(255, 149, 0, 0.12)',
    borderWidth: 1,
    borderColor: 'rgba(255, 149, 0, 0.25)',
  },
  emotionNoticeText: {
    color: '#FFB24D',
    fontSize: 11,
    lineHeight: 15,
    fontWeight: '600',
  },
  dragHint: {
    color: 'rgba(233, 240, 255, 0.8)',
    fontSize: 10,
    fontWeight: '600',
  },
  emotionOverlayCloseButton: {
    paddingHorizontal: 12,
    paddingVertical: 5,
    borderRadius: 7,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.26)',
    backgroundColor: 'rgba(255,255,255,0.16)',
  },
  emotionOverlayCloseText: {
    color: '#F5F8FF',
    fontSize: 11,
    fontWeight: '600',
  },
  controlsContainer: {
    paddingVertical: 8,
  },
  backendStatus: {
    borderWidth: 1,
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 8,
    marginBottom: 12,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  backendStatusLabel: {
    fontSize: 12,
    fontWeight: '600',
    textTransform: 'uppercase',
  },
  backendStatusValue: {
    fontSize: 13,
    fontWeight: '700',
  },
  backendStatusSubValue: {
    fontSize: 11,
    fontWeight: '700',
    marginTop: 2,
  },
  fenStatusMessage: {
    fontSize: 12,
    marginBottom: 12,
    lineHeight: 16,
  },
  processingContainer: {
    alignItems: 'center',
    marginBottom: 20,
  },
  processingText: {
    marginTop: 12,
    fontSize: 16,
    fontWeight: '500',
  },
  translationResultContainer: {
    backgroundColor: 'rgba(0, 122, 255, 0.08)',
    borderRadius: 12,
    padding: 16,
    marginBottom: 20,
    marginHorizontal: 12,
    borderLeftWidth: 4,
  },
  translationLabel: {
    fontSize: 12,
    fontWeight: '600',
    marginBottom: 8,
    textTransform: 'uppercase',
  },
  translationText: {
    fontSize: 18,
    fontWeight: '500',
    lineHeight: 24,
  },
  instructionText: {
    fontSize: 14,
    textAlign: 'center',
    marginBottom: 20,
    marginHorizontal: 12,
  },
  button: {
    paddingVertical: 14,
    paddingHorizontal: 24,
    borderRadius: 12,
    alignItems: 'center',
    marginHorizontal: 12,
    boxShadow: '0px 2px 4px rgba(0, 0, 0, 0.1)',
  },
  startButton: {
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.08)',
    marginTop: 8,
  },
  buttonText: {
    fontSize: 16,
    fontWeight: '600',
  },
});
