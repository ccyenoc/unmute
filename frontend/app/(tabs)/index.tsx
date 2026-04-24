import { Colors } from '@/constants/theme';
import { useColorScheme } from '@/hooks/use-color-scheme';
import { CameraView, useCameraPermissions } from 'expo-camera';
import { useEffect, useRef, useState } from 'react';
import {
  ActivityIndicator,
  SafeAreaView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import Svg, { Circle, G, Line } from 'react-native-svg';

interface Landmark {
  x: number;
  y: number;
  z: number;
}

interface LandmarkResponse {
  landmarks: Landmark[][];
}

export default function TranslatorScreen() {
  const colorScheme = useColorScheme() ?? 'light';
  const actionButtonTextColor = '#11181C';
  const [permission, requestPermission] = useCameraPermissions();
  const cameraRef = useRef<CameraView>(null);

  // 🔥 UI STATE
  const [currentWord, setCurrentWord] = useState("");
  const [sentence, setSentence] = useState("Detecting...");
  const [landmarks, setLandmarks] = useState<Landmark[][]>([]);
  const [cameraSize, setCameraSize] = useState({ width: 0, height: 0 });

  // 🔥 MEMORY (same as Python)
  const history = useRef<string[]>([]);
  const wordBuffer = useRef<string[]>([]);
  const phrases = useRef<{ text: string; timer: number }[]>([]);
  const cooldown = useRef(0);
  const isSending = useRef(false);
  const lastWord = useRef("");

  // ===== PERMISSION =====
  useEffect(() => {
    if (!permission?.granted) {
      requestPermission();
    }
  }, [permission]);

  // ===== MAIN LOOP (capture frames) =====
  useEffect(() => {
    const interval = setInterval(() => {
      sendFrame();
    }, 150); // faster

    return () => clearInterval(interval);
  }, []);

  // ===== TIMER LOOP (sentence decay like Python) =====
  useEffect(() => {
    const timer = setInterval(() => {
      updateDisplay();
    }, 200);

    return () => clearInterval(timer);
  }, []);

  // ===== SEND FRAME =====
  const sendFrame = async () => {
    if (!cameraRef.current || isSending.current) return;

    isSending.current = true;

    try {
      const photo = await cameraRef.current.takePictureAsync({
        quality: 0.8,  // Higher quality for better hand detection
        base64: false,
      });

      const formData = new FormData();
      formData.append('file', {
        uri: photo.uri,
        type: 'image/jpeg',
        name: 'frame.jpg',
      } as any);

      const res = await fetch('http://192.168.1.101:8000/api/detection/predict', {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        console.log("ERROR: Backend returned status", res.status);
        return;
      }

      const data = await res.json();

      // 🔥 ALWAYS display landmarks (like predict_webcam.py shows all frames)
      if (data.landmarks && Array.isArray(data.landmarks)) {
        setLandmarks(data.landmarks);
        console.log("Landmarks:", data.landmarks.length, "hands detected");
      } else {
        setLandmarks([]);
      }

      // Then process prediction (which may be filtered)
      if (data.prediction) {
        processPrediction(data.prediction, data.confidence || 0);
      }

    } catch (err) {
      console.log("ERROR:", err);
    } finally {
      isSending.current = false;
    }
  };

  // ===== PROCESS PREDICTION =====
  const processPrediction = (pred: any, confidence: number = 0) => {
  // 🔥 SAFETY CHECK
  if (!pred || typeof pred !== "string") {
    return;
  }

  // 🔥 Don't add "No hand" to history, but still process uncertain
  if (pred === "No hand") return;

    // 🔥 HISTORY - add ALL predictions (including "Uncertain")
    history.current.push(pred);
    if (history.current.length > 12) history.current.shift();

    // Filter out uncertain for voting
    const validPredictions = history.current.filter(p => p !== "Uncertain");
    if (validPredictions.length === 0) return;

    // majority vote (only on valid predictions)
    const counts: Record<string, number> = {};
    validPredictions.forEach(p => {
      counts[p] = (counts[p] || 0) + 1;
    });

    const finalPred = Object.keys(counts).reduce((a, b) =>
      counts[a] > counts[b] ? a : b
    );

    // 🔥 ANTI-FLICKER WORD UPDATE
    if (finalPred !== lastWord.current) {
      setCurrentWord(finalPred);
      lastWord.current = finalPred;
    }

    // cooldown
    if (cooldown.current > 0) {
      cooldown.current--;
      return;
    }

    if (!cameraRef.current) {
      Alert.alert('Camera Error', 'Camera is not ready yet. Please try again.');
      return;
    }

    const freq = counts[finalPred] / validPredictions.length;
    if (freq < 0.4) return; // relaxed threshold

    const DIRECT_PHRASES: Record<string, string> = {
      hi: "Hi",
      iloveyou: "I love you",
      thankyou: "Thank you",
      goodbye: "Goodbye",
    };

    if (DIRECT_PHRASES[finalPred]) {
      phrases.current.push({
        text: DIRECT_PHRASES[finalPred],
        timer: 30,
      });

      history.current = [];
      wordBuffer.current = [];
      cooldown.current = 30;

      return;
    }

    // 🔥 WORD BUFFER LOGIC
    if (wordBuffer.current.length === 0) {
      wordBuffer.current.push(finalPred);
    } else {
      const prev = wordBuffer.current[wordBuffer.current.length - 1];

      if (prev === "me" && finalPred === "hungry") {
        phrases.current.push({ text: "I am hungry", timer: 30 });
        wordBuffer.current = [];
      } else if (prev === "me" && finalPred === "tired") {
        phrases.current.push({ text: "I am tired", timer: 30 });
        wordBuffer.current = [];
      } else if (prev === "name") {
        phrases.current.push({
          text: `My name is ${finalPred.toUpperCase()}`,
          timer: 30,
        });
        wordBuffer.current = [];
      } else {
        wordBuffer.current.push(finalPred);
      }
    }

    cooldown.current = 15;
  };

  // ===== UPDATE SENTENCE (AUTO DECAY) =====
  const updateDisplay = () => {
    phrases.current.forEach(p => {
      p.timer -= 1;
    });

    phrases.current = phrases.current.filter(p => p.timer > 0);

    const text = phrases.current.map(p => p.text).join(" ");
    setSentence(text || "Detecting...");
  };

  // ===== UI =====
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
        <Text>Camera permission required</Text>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: Colors[colorScheme].background }]}>
      <View 
        style={styles.cameraContainer}
        onLayout={(event) => {
          const { width, height } = event.nativeEvent.layout;
          setCameraSize({ width, height });
        }}
      >
        <CameraView 
          ref={cameraRef} 
          style={styles.camera} 
          facing="back"
        />
        
        {/* Landmarks Overlay */}
        {cameraSize.width > 0 && landmarks.length > 0 && (
          <Svg
            style={styles.landmarksOverlay}
            width={cameraSize.width}
            height={cameraSize.height}
          >
            {landmarks.map((hand, handIdx) => {
              // Define hand connections (from MediaPipe HAND_CONNECTIONS)
              const connections = [
                [0, 1], [1, 2], [2, 3], [3, 4],
                [0, 5], [5, 6], [6, 7], [7, 8],
                [5, 9], [9, 10], [10, 11], [11, 12],
                [9, 13], [13, 14], [14, 15], [15, 16],
                [13, 17], [17, 18], [18, 19], [19, 20],
                [0, 17]
              ];

              return (
                <G key={`hand-${handIdx}`}>
  {connections.map((conn, idx) => {
    const start = hand[conn[0]];
    const end = hand[conn[1]];
    if (!start || !end) return null;

    const x1 = (1 - start.x) * cameraSize.width;
    const y1 = start.y * cameraSize.height;
    const x2 = (1 - end.x) * cameraSize.width;
    const y2 = end.y * cameraSize.height;

    return (
      <Line
        key={`line-${handIdx}-${idx}`}
        x1={x1}
        y1={y1}
        x2={x2}
        y2={y2}
        stroke="#00FF00"
        strokeWidth={3}
      />
    );
  })}

  {hand.map((lm, idx) => {
    const cx = (1 - lm.x) * cameraSize.width;
    const cy = lm.y * cameraSize.height;

    return (
      <Circle
        key={`dot-${handIdx}-${idx}`}
        cx={cx}
        cy={cy}
        r={5}
        fill="#FF0000"
      />
    );
  })}
</G>
              );
            })}
          </Svg>
        )}
      </View>

      <View style={styles.controlsContainer}>
        <Text style={styles.label}>Word</Text>
        <Text style={styles.word}>{currentWord || "..."}</Text>

        <Text style={styles.label}>Sentence</Text>
        <Text style={styles.sentence}>{sentence}</Text>
        
        <Text style={styles.debug}>Landmarks: {landmarks.length} hands</Text>
      </View>
    </SafeAreaView>
  );

}

const styles = StyleSheet.create({
  container: { flex: 1 },

  cameraContainer: {
    flex: 1,
    margin: 12,
    borderRadius: 12,
    overflow: 'hidden',
    backgroundColor: '#000',
  },

  camera: { 
    ...StyleSheet.absoluteFillObject,
  },

  landmarksOverlay: {
    ...StyleSheet.absoluteFillObject,
  },

  controlsContainer: {
    padding: 20,
    alignItems: 'center',
  },

  label: {
    fontSize: 14,
    color: 'gray',
    marginTop: 10,
  },

  word: {
    fontSize: 24,
    fontWeight: 'bold',
  },

  sentence: {
    fontSize: 22,
    fontWeight: '600',
    marginTop: 10,
    textAlign: 'center',
  },

  debug: {
    fontSize: 12,
    color: '#999',
    marginTop: 10,
  },
});