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
    Dimensions,
    PanResponder,
    ScrollView,
    StyleSheet,
    Text,
    TouchableOpacity,
    View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

export default function TranslatorScreen() {
  const colorScheme = useColorScheme() ?? 'light';
  const actionButtonTextColor = '#11181C';
  const [overlayScale, setOverlayScale] = useState(1);
  const [overlayPosition, setOverlayPosition] = useState({ x: 12, y: 60 });
  const dragStartRef = useRef({ x: 12, y: 60 });
  const touchStartRef = useRef({ x: 0, y: 0 });
  const pinchStartDistanceRef = useRef<number | null>(null);
  const pinchStartScaleRef = useRef(1);
  const isPinchingRef = useRef(false);
  const [permission, requestPermission] = useCameraPermissions();
  const [isRecording, setIsRecording] = useState(false);
  const [translation, setTranslation] = useState<string | null>(null);
  const [emotionResult, setEmotionResult] = useState<EmotionAnalysisResponse | null>(null);
  const [fusionResult, setFusionResult] = useState<FusionResponse | null>(null);
  const [apiConnected, setApiConnected] = useState<boolean | null>(null);
  const [fenReady, setFenReady] = useState<boolean | null>(null);
  const [fenModelMessage, setFenModelMessage] = useState<string | null>(null);
  const [backendStatusLabel, setBackendStatusLabel] = useState('Checking...');
  const [isProcessing, setIsProcessing] = useState(false);
  const cameraRef = useRef<CameraView>(null);

  const createFallbackEmotionResult = (message: string): EmotionAnalysisResponse => ({
    success: false,
    face_detected: false,
    faces_detected: 0,
    provider: 'fen',
    emotion: 'neutral',
    confidence: 0,
    scores: {
      angry: 0,
      disgust: 0,
      fear: 0,
      happy: 0,
      neutral: 0,
      sad: 0,
      surprise: 0,
    },
    message,
  });

  const clamp = (value: number, min: number, max: number) => Math.min(Math.max(value, min), max);

  const getOverlayBounds = (scale: number) => {
    const { width: screenWidth, height: screenHeight } = Dimensions.get('window');
    const scaledWidth = 240 * scale;
    const scaledHeight = 320 * scale;
    return {
      minX: -scaledWidth * 0.75,
      maxX: Math.max(8, screenWidth - scaledWidth * 0.25),
      minY: -scaledHeight * 0.45,
      maxY: Math.max(52, screenHeight - scaledHeight * 0.15),
    };
  };

  const getTouchDistance = (touches: readonly { pageX: number; pageY: number }[]) => {
    if (touches.length < 2) {
      return 0;
    }
    const dx = touches[0].pageX - touches[1].pageX;
    const dy = touches[0].pageY - touches[1].pageY;
    return Math.hypot(dx, dy);
  };

  const panResponder = useRef(
    PanResponder.create({
      onMoveShouldSetPanResponder: (evt, gestureState) => {
        const touchCount = evt.nativeEvent.touches.length;
        return touchCount > 1 || Math.abs(gestureState.dx) > 2 || Math.abs(gestureState.dy) > 2;
      },
      onPanResponderGrant: (evt, gestureState) => {
        dragStartRef.current = overlayPosition;
        touchStartRef.current = { x: gestureState.x0, y: gestureState.y0 };
        if (evt.nativeEvent.touches.length > 1) {
          pinchStartDistanceRef.current = getTouchDistance(evt.nativeEvent.touches);
          pinchStartScaleRef.current = overlayScale;
          isPinchingRef.current = true;
        } else {
          pinchStartDistanceRef.current = null;
          isPinchingRef.current = false;
        }
      },
      onPanResponderMove: (evt, gestureState) => {
        if (evt.nativeEvent.touches.length > 1) {
          const currentDistance = getTouchDistance(evt.nativeEvent.touches);
          if (!pinchStartDistanceRef.current || pinchStartDistanceRef.current <= 0) {
            pinchStartDistanceRef.current = currentDistance;
            pinchStartScaleRef.current = overlayScale;
            isPinchingRef.current = true;
            return;
          }

          const ratio = currentDistance / pinchStartDistanceRef.current;
          const nextScale = clamp(pinchStartScaleRef.current * ratio, 0.6, 2.3);
          const bounds = getOverlayBounds(nextScale);

          setOverlayScale(nextScale);
          setOverlayPosition((currentPosition) => ({
            x: clamp(currentPosition.x, bounds.minX, bounds.maxX),
            y: clamp(currentPosition.y, bounds.minY, bounds.maxY),
          }));
          return;
        }

        if (isPinchingRef.current) {
          return;
        }

        const bounds = getOverlayBounds(overlayScale);
        const nextX = dragStartRef.current.x + (gestureState.moveX - touchStartRef.current.x);
        const nextY = dragStartRef.current.y + (gestureState.moveY - touchStartRef.current.y);
        setOverlayPosition({
          x: clamp(nextX, bounds.minX, bounds.maxX),
          y: clamp(nextY, bounds.minY, bounds.maxY),
        });
      },
      onPanResponderRelease: () => {
        pinchStartDistanceRef.current = null;
        isPinchingRef.current = false;
      },
      onPanResponderTerminate: () => {
        pinchStartDistanceRef.current = null;
        isPinchingRef.current = false;
      },
    })
  ).current;

  const zoomOverlay = (delta: number) => {
    setOverlayScale((current) => {
      const nextScale = clamp(current + delta, 0.6, 2.3);
      const bounds = getOverlayBounds(nextScale);
      setOverlayPosition((currentPosition) => ({
        x: clamp(currentPosition.x, bounds.minX, bounds.maxX),
        y: clamp(currentPosition.y, bounds.minY, bounds.maxY),
      }));
      return nextScale;
    });
  };

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

      Promise.all([checkFacialApiHealth(), getEmotionModelInfo()])
        .then(([ok, modelInfo]) => {
          if (mounted) {
            setApiConnected(ok);
            setBackendStatusLabel(ok ? 'Connected' : 'Disconnected');
            setFenReady(modelInfo.fen_model.ready);
            setFenModelMessage(modelInfo.fen_model.message ?? null);
          }
        })
        .catch(() => {
          if (mounted) {
            setApiConnected(false);
            setBackendStatusLabel('Disconnected');
            setFenReady(false);
            setFenModelMessage('Unable to read FEN model status');
          }
        });

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
    setEmotionResult(createFallbackEmotionResult('Reading facial expression...'));
    setFusionResult(null);
    setIsProcessing(true);

    try {
      const translationPromise = simulateSignTranslation();
      // Give the camera a tiny moment to settle, but avoid a long blocking delay.
      await new Promise((resolve) => setTimeout(resolve, 120));
      const snapshot = await cameraRef.current.takePictureAsync({
        base64: true,
        quality: 0.85,
        skipProcessing: false,
      });

      const result = await translationPromise;
      setTranslation(result);
      let historyEmotionSnapshot: FacialEmotionSnapshot | null = null;

      if (snapshot.base64) {
        try {
          const emotion = await analyzeEmotionFromBase64(snapshot.base64);
          setEmotionResult(emotion);

          historyEmotionSnapshot = {
            emotion: emotion.emotion,
            confidence: emotion.confidence,
            provider: emotion.provider,
            faces_detected: emotion.faces_detected,
            scores: emotion.scores,
          };

          if (emotion.face_detected) {
            try {
              const fusion = await interpretFusion(result, emotion.emotion, emotion.confidence);
              setFusionResult(fusion);
              historyEmotionSnapshot = {
                ...historyEmotionSnapshot,
                fusion_status: fusion.status,
              };
            } catch {
              setFusionResult(null);
            }
          }
        } catch {
          setEmotionResult(createFallbackEmotionResult('Facial expression API unavailable.'));
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

  const renderEmotionOverlay = () => {
    if (isRecording || !emotionResult) {
      return null;
    }

    const confidenceNormalized = emotionResult.confidence > 1
      ? emotionResult.confidence / 100
      : emotionResult.confidence;

    const payload = {
      emotion: emotionResult.emotion,
      confidence: Number(confidenceNormalized.toFixed(3)),
      provider: emotionResult.provider,
      faces_detected: emotionResult.faces_detected,
      fusion_status: fusionResult?.status ?? 'aligned',
      scores: emotionResult.scores,
    };

    return (
      <View
        style={[
          styles.emotionOverlayCard,
          {
            transform: [{ scale: overlayScale }],
            left: overlayPosition.x,
            top: overlayPosition.y,
          },
        ]}
      >
        <View style={styles.emotionOverlayHeader} {...panResponder.panHandlers}>
          <View>
            <Text style={styles.emotionOverlayTitle}>Facial Expression API</Text>
            <Text style={styles.emotionOverlaySubtitle}>Live Emotion Snapshot</Text>
          </View>
          <View style={styles.emotionOverlayActions}>
            <TouchableOpacity style={styles.zoomControl} onPress={() => zoomOverlay(-0.1)}>
              <Text style={styles.zoomControlText}>-</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.zoomControl} onPress={() => zoomOverlay(0.1)}>
              <Text style={styles.zoomControlText}>+</Text>
            </TouchableOpacity>
          </View>
        </View>

        <View style={styles.overlayMetaRow}>
          <View style={styles.metaPill}>
            <Text style={styles.metaPillLabel}>Emotion</Text>
            <Text style={styles.metaPillValue}>{payload.emotion}</Text>
          </View>
          <View style={styles.metaPill}>
            <Text style={styles.metaPillLabel}>Confidence</Text>
            <Text style={styles.metaPillValue}>{payload.confidence}</Text>
          </View>
        </View>

        {emotionResult.message ? (
          <View style={styles.emotionNoticeBox}>
            <Text style={styles.emotionNoticeText}>{emotionResult.message}</Text>
          </View>
        ) : null}

        <ScrollView
          style={styles.emotionOverlayScroll}
          contentContainerStyle={styles.emotionOverlayScrollContent}
          nestedScrollEnabled
          showsVerticalScrollIndicator
        >
          <Text style={styles.emotionOverlayPayload}>{JSON.stringify(payload, null, 2)}</Text>
        </ScrollView>

        <View style={styles.emotionOverlayFooter}>
          <Text style={styles.dragHint}>Drag to move, pinch or +/- to zoom</Text>
          <TouchableOpacity
            style={styles.emotionOverlayCloseButton}
            onPress={() => {
              setEmotionResult(null);
              setFusionResult(null);
            }}
          >
            <Text style={styles.emotionOverlayCloseText}>Cancel</Text>
          </TouchableOpacity>
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
      <View style={styles.cameraContainer}>
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
        {renderEmotionOverlay()}
      </View>

      <View style={styles.controlsContainer}>
        <View style={[styles.backendStatus, { borderColor: Colors[colorScheme].tabIconDefault }]}> 
          <Text style={[styles.backendStatusLabel, { color: Colors[colorScheme].tabIconDefault }]}>Backend</Text>
          <View style={{ alignItems: 'flex-end' }}>
            <Text
              style={[
                styles.backendStatusValue,
                { color: apiConnected ? '#22A06B' : apiConnected === false ? '#D92D20' : Colors[colorScheme].text },
              ]}
            >
              {backendStatusLabel}
            </Text>
            <Text style={[styles.backendStatusSubValue, { color: fenReady ? '#22A06B' : '#D92D20' }]}> 
              {fenReady ? 'FEN Ready' : 'FEN Not Ready'}
            </Text>
          </View>
        </View>

        {fenModelMessage ? (
          <Text style={[styles.fenStatusMessage, { color: Colors[colorScheme].tabIconDefault }]}> 
            {fenModelMessage}
          </Text>
        ) : null}

        {isProcessing ? (
          <View style={styles.processingContainer}>
            <ActivityIndicator size="large" color={Colors[colorScheme].tint} />
            <Text style={[styles.processingText, { color: Colors[colorScheme].text }]}>
              Processing sign language and emotion...
            </Text>
          </View>
        ) : translation ? (
          <View style={styles.translationResultContainer}>
            <Text style={[styles.translationLabel, { color: Colors[colorScheme].tabIconDefault }]}>
              Translation
            </Text>
            <Text style={[styles.translationText, { color: Colors[colorScheme].text }]}>
              {translation}
            </Text>
          </View>
        ) : (
          <Text style={[styles.instructionText, { color: Colors[colorScheme].tabIconDefault }]}>
            Position yourself in front of the camera and tap the button below to start translating
          </Text>
        )}

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
          <Text style={[styles.buttonText, { color: actionButtonTextColor }] }>
            {isRecording ? 'Recording...' : 'Start Translation'}
          </Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  cameraContainer: {
    flex: 1,
    position: 'relative',
    borderRadius: 12,
    overflow: 'hidden',
    margin: 12,
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
  emotionOverlayCard: {
    position: 'absolute',
    width: 260,
    maxHeight: 360,
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
    padding: 16,
    paddingBottom: 32,
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
    backgroundColor: 'rgba(0, 122, 255, 0.1)',
    borderRadius: 12,
    padding: 16,
    marginBottom: 20,
    borderLeftWidth: 4,
    borderLeftColor: '#007AFF',
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
  },
  button: {
    paddingVertical: 14,
    paddingHorizontal: 24,
    borderRadius: 12,
    alignItems: 'center',
    boxShadow: '0px 2px 4px rgba(0, 0, 0, 0.1)',
  },
  startButton: {
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.08)',
  },
  buttonText: {
    fontSize: 16,
    fontWeight: '600',
  },
});
