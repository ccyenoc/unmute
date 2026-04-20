import { Colors } from '@/constants/theme';
import { useColorScheme } from '@/hooks/use-color-scheme';
import {
    analyzeEmotionFromBase64,
    checkFacialApiHealth,
    EmotionAnalysisResponse,
    FusionResponse,
    interpretFusion,
} from '@/utils/facialEmotionService';
import { simulateSignTranslation, storeTranslation } from '@/utils/translationService';
import { useFocusEffect } from '@react-navigation/native';
import { CameraView, useCameraPermissions } from 'expo-camera';
import React, { useCallback, useRef, useState } from 'react';
import {
    ActivityIndicator,
    Alert,
    SafeAreaView,
    StyleSheet,
    Text,
    TouchableOpacity,
    View,
} from 'react-native';

export default function TranslatorScreen() {
  const colorScheme = useColorScheme() ?? 'light';
  const actionButtonTextColor = colorScheme === 'light' ? '#11181C' : '#FFFFFF';
  const [permission, requestPermission] = useCameraPermissions();
  const [isRecording, setIsRecording] = useState(false);
  const [translation, setTranslation] = useState<string | null>(null);
  const [emotionResult, setEmotionResult] = useState<EmotionAnalysisResponse | null>(null);
  const [fusionResult, setFusionResult] = useState<FusionResponse | null>(null);
  const [apiConnected, setApiConnected] = useState<boolean | null>(null);
  const [backendStatusLabel, setBackendStatusLabel] = useState('Checking...');
  const [isProcessing, setIsProcessing] = useState(false);
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

      checkFacialApiHealth()
        .then((ok) => {
          if (mounted) {
            setApiConnected(ok);
            setBackendStatusLabel(ok ? 'Connected' : 'Disconnected');
          }
        })
        .catch(() => {
          if (mounted) {
            setApiConnected(false);
            setBackendStatusLabel('Disconnected');
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
    setEmotionResult(null);
    setFusionResult(null);
    setIsProcessing(true);

    try {
      // Keep a short delay for recording UX before capturing a frame.
      await new Promise((resolve) => setTimeout(resolve, 1200));
      const snapshot = await cameraRef.current.takePictureAsync({
        base64: true,
        quality: 0.5,
        skipProcessing: true,
      });

      const result = await simulateSignTranslation();
      setTranslation(result);

      if (snapshot.base64) {
        try {
          const emotion = await analyzeEmotionFromBase64(snapshot.base64);
          setEmotionResult(emotion);

          if (emotion.face_detected) {
            try {
              const fusion = await interpretFusion(result, emotion.emotion, emotion.confidence);
              setFusionResult(fusion);
            } catch {
              setFusionResult(null);
            }
          }
        } catch {
          setEmotionResult(null);
          setFusionResult(null);
        }
      }

      await storeTranslation(result);
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
    if (!emotionResult) {
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
      <View style={styles.emotionOverlayCard}>
        <Text style={styles.emotionOverlayTitle}>Facial Expression API</Text>
        <Text style={styles.emotionOverlayPayload}>{JSON.stringify(payload, null, 2)}</Text>
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
          <Text
            style={[
              styles.backendStatusValue,
              { color: apiConnected ? '#22A06B' : apiConnected === false ? '#D92D20' : Colors[colorScheme].text },
            ]}
          >
            {backendStatusLabel}
          </Text>
        </View>

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
            {
              backgroundColor: Colors[colorScheme].tint,
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
    right: 12,
    top: 60,
    width: 220,
    backgroundColor: 'rgba(0, 0, 0, 0.75)',
    borderRadius: 10,
    padding: 10,
  },
  emotionOverlayTitle: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '700',
    marginBottom: 6,
  },
  emotionOverlayPayload: {
    color: '#FFFFFF',
    fontSize: 11,
    lineHeight: 16,
    fontFamily: 'monospace',
  },
  emotionOverlayCloseButton: {
    alignSelf: 'flex-end',
    marginTop: 8,
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 6,
    backgroundColor: 'rgba(255,255,255,0.2)',
  },
  emotionOverlayCloseText: {
    color: '#FFFFFF',
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
  buttonText: {
    fontSize: 16,
    fontWeight: '600',
  },
});
