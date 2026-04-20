import { Colors } from '@/constants/theme';
import { useColorScheme } from '@/hooks/use-color-scheme';
import {
    analyzeEmotionFromBase64,
    checkFacialApiHealth,
    collectEmotionSampleFromBase64,
    EmotionAnalysisResponse,
    EmotionDatasetInfoResponse,
    FusionResponse,
    getEmotionDatasetInfo,
    getEmotionModelInfo,
    getEmotionTrainingStatus,
    interpretFusion,
    startEmotionTraining,
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
  const [selectedEmotionLabel, setSelectedEmotionLabel] = useState<'happy' | 'angry' | 'neutral'>('neutral');
  const [datasetInfo, setDatasetInfo] = useState<EmotionDatasetInfoResponse | null>(null);
  const [fenReady, setFenReady] = useState(false);
  const [trainingStatusText, setTrainingStatusText] = useState<string>('Idle');
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

      getEmotionDatasetInfo()
        .then((dataset) => {
          if (mounted) {
            setDatasetInfo(dataset);
          }
        })
        .catch(() => {
          if (mounted) {
            setDatasetInfo(null);
          }
        });

      getEmotionModelInfo()
        .then((modelInfo) => {
          if (mounted) {
            setFenReady(Boolean(modelInfo.fen_model?.ready));
          }
        })
        .catch(() => {
          if (mounted) {
            setFenReady(false);
          }
        });

      getEmotionTrainingStatus()
        .then((status) => {
          if (!mounted) {
            return;
          }
          if (status.running) {
            setTrainingStatusText('Running');
            return;
          }
          const lastStatus = status.last_job?.status;
          if (lastStatus) {
            setTrainingStatusText(lastStatus);
            return;
          }
          setTrainingStatusText('Idle');
        })
        .catch(() => {
          if (mounted) {
            setTrainingStatusText('Unavailable');
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

  const handleCollectSample = async () => {
    if (!permission?.granted) {
      Alert.alert('Camera Permission', 'Camera permission is required to collect emotion samples.');
      return;
    }

    if (!cameraRef.current) {
      Alert.alert('Camera Error', 'Camera is not ready yet. Please try again.');
      return;
    }

    setIsProcessing(true);
    try {
      const snapshot = await cameraRef.current.takePictureAsync({
        base64: true,
        quality: 0.6,
        skipProcessing: true,
      });

      if (!snapshot.base64) {
        throw new Error('No frame data captured');
      }

      const result = await collectEmotionSampleFromBase64(snapshot.base64, selectedEmotionLabel);
      setDatasetInfo(result.dataset);
      Alert.alert('Sample Collected', `Saved ${selectedEmotionLabel} sample successfully.`);
    } catch {
      Alert.alert('Collect Sample Failed', 'Could not collect sample. Make sure a face is visible.');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleTrainFen = async () => {
    setIsProcessing(true);
    try {
      const started = await startEmotionTraining(30, 32);
      setTrainingStatusText(started.job?.status || 'running');
      Alert.alert('Training Started', 'FEN training job started in backend.');
    } catch {
      Alert.alert('Training Failed', 'Could not start training. Ensure dataset has at least 2 emotion classes.');
    } finally {
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

  const renderEmotionOutput = () => {
    if (!emotionResult) {
      return null;
    }

    return (
      <View style={styles.emotionApiCard}>
        <Text style={[styles.emotionApiTitle, { color: Colors[colorScheme].text }]}>Facial Expression API</Text>
        <Text style={[styles.emotionApiText, { color: Colors[colorScheme].tabIconDefault }]}> 
          {emotionResult.face_detected
            ? `${emotionResult.emotion} (${emotionResult.confidence.toFixed(1)}%)`
            : 'No face detected'}
        </Text>
        <Text style={[styles.emotionApiMeta, { color: Colors[colorScheme].tabIconDefault }]}> 
          Provider: {emotionResult.provider ?? 'none'}
        </Text>
        <Text style={[styles.emotionApiMeta, { color: Colors[colorScheme].tabIconDefault }]}> 
          Faces detected: {emotionResult.faces_detected}
        </Text>
        <Text style={[styles.emotionApiMeta, { color: Colors[colorScheme].tabIconDefault }]}> 
          Scores: {JSON.stringify(emotionResult.scores)}
        </Text>
        {emotionResult.message ? (
          <Text style={[styles.emotionApiMeta, { color: Colors[colorScheme].tabIconDefault }]}> 
            Message: {emotionResult.message}
          </Text>
        ) : null}
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

        <View style={[styles.fenPanel, { borderColor: Colors[colorScheme].tabIconDefault }]}> 
          <Text style={[styles.fenTitle, { color: Colors[colorScheme].text }]}>FEN Training Panel</Text>
          <Text style={[styles.fenMeta, { color: Colors[colorScheme].tabIconDefault }]}> 
            FEN Ready: {fenReady ? 'Yes' : 'No'}
          </Text>
          <Text style={[styles.fenMeta, { color: Colors[colorScheme].tabIconDefault }]}> 
            Training Status: {trainingStatusText}
          </Text>
          <Text style={[styles.fenMeta, { color: Colors[colorScheme].tabIconDefault }]}> 
            Total Samples: {datasetInfo?.total_images ?? 0}
          </Text>

          <View style={styles.labelRow}>
            {(['happy', 'angry', 'neutral'] as const).map((label) => (
              <TouchableOpacity
                key={label}
                style={[
                  styles.labelChip,
                  {
                    borderColor: Colors[colorScheme].tabIconDefault,
                    backgroundColor: selectedEmotionLabel === label ? Colors[colorScheme].tint : 'transparent',
                  },
                ]}
                onPress={() => setSelectedEmotionLabel(label)}
              >
                <Text
                  style={{
                    color: selectedEmotionLabel === label ? actionButtonTextColor : Colors[colorScheme].text,
                    fontWeight: '600',
                    textTransform: 'capitalize',
                  }}
                >
                  {label}
                </Text>
              </TouchableOpacity>
            ))}
          </View>

          <View style={styles.fenActionRow}>
            <TouchableOpacity
              style={[styles.secondaryButton, { borderColor: Colors[colorScheme].tabIconDefault }]}
              onPress={handleCollectSample}
              disabled={isProcessing}
            >
              <Text style={[styles.secondaryButtonText, { color: Colors[colorScheme].text }]}>Collect Sample</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.secondaryButton, { borderColor: Colors[colorScheme].tabIconDefault }]}
              onPress={handleTrainFen}
              disabled={isProcessing}
            >
              <Text style={[styles.secondaryButtonText, { color: Colors[colorScheme].text }]}>Train FEN</Text>
            </TouchableOpacity>
          </View>
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
            {emotionResult?.face_detected && (
              <View style={styles.emotionContainer}>
                <Text style={[styles.emotionLabel, { color: Colors[colorScheme].tabIconDefault }]}>
                  Emotion
                </Text>
                <Text style={[styles.emotionText, { color: Colors[colorScheme].text }]}>
                  {emotionResult.emotion} ({emotionResult.confidence.toFixed(1)}%)
                </Text>
                {fusionResult && (
                  <Text style={[styles.fusionText, { color: Colors[colorScheme].tabIconDefault }]}> 
                    Fusion: {fusionResult.status}
                  </Text>
                )}
              </View>
            )}
            {renderEmotionOutput()}
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
  fenPanel: {
    borderWidth: 1,
    borderRadius: 10,
    padding: 12,
    marginBottom: 12,
  },
  fenTitle: {
    fontSize: 12,
    fontWeight: '700',
    textTransform: 'uppercase',
    marginBottom: 6,
  },
  fenMeta: {
    fontSize: 12,
    marginTop: 2,
  },
  labelRow: {
    flexDirection: 'row',
    marginTop: 10,
    gap: 8,
  },
  labelChip: {
    borderWidth: 1,
    borderRadius: 8,
    paddingHorizontal: 10,
    paddingVertical: 6,
  },
  fenActionRow: {
    flexDirection: 'row',
    marginTop: 10,
    gap: 8,
  },
  secondaryButton: {
    flex: 1,
    borderWidth: 1,
    borderRadius: 10,
    alignItems: 'center',
    paddingVertical: 10,
  },
  secondaryButtonText: {
    fontSize: 13,
    fontWeight: '600',
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
  emotionContainer: {
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: 'rgba(0, 122, 255, 0.2)',
  },
  emotionApiCard: {
    marginTop: 12,
    padding: 12,
    borderRadius: 10,
    backgroundColor: 'rgba(0, 0, 0, 0.04)',
  },
  emotionApiTitle: {
    fontSize: 12,
    fontWeight: '700',
    marginBottom: 6,
    textTransform: 'uppercase',
  },
  emotionApiText: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 6,
  },
  emotionApiMeta: {
    fontSize: 12,
    lineHeight: 18,
    marginTop: 2,
  },
  emotionLabel: {
    fontSize: 12,
    fontWeight: '600',
    marginBottom: 4,
    textTransform: 'uppercase',
  },
  emotionText: {
    fontSize: 16,
    fontWeight: '600',
  },
  fusionText: {
    marginTop: 6,
    fontSize: 13,
    fontWeight: '600',
    textTransform: 'capitalize',
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
