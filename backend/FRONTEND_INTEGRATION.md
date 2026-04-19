"""
Frontend Integration Example
How to use the backend API from React Native
"""

# ============================================
# TypeScript/JavaScript Integration Examples
# ============================================

# 1. BASIC DETECTION SERVICE
# ============================================

"""
// frontend/services/translationService.ts

import axios from 'axios';

const API_BASE = 'http://localhost:8000/api';

interface DetectionResult {
  success: boolean;
  prediction: string;
  confidence: number;
  handedness: string;
}

class TranslationService {
  /**
   * Detect sign from image URI
   */
  async detectFromImage(imageUri: string): Promise<DetectionResult> {
    try {
      const formData = new FormData();
      
      // Convert URI to blob (React Native)
      const response = await fetch(imageUri);
      const blob = await response.blob();
      
      formData.append('file', blob, 'image.jpg');
      
      const result = await axios.post(
        `${API_BASE}/detection/detect-image`,
        formData,
        {
          headers: { 'Content-Type': 'multipart/form-data' },
        }
      );
      
      return {
        success: result.data.success,
        prediction: result.data.predictions[0]?.prediction || 'UNCERTAIN',
        confidence: result.data.predictions[0]?.confidence || 0,
        handedness: result.data.handedness[0] || 'Unknown',
      };
    } catch (error) {
      console.error('Detection error:', error);
      return {
        success: false,
        prediction: 'ERROR',
        confidence: 0,
        handedness: 'Unknown',
      };
    }
  }

  /**
   * Detect from camera frame (real-time)
   */
  async detectFrame(frameUri: string): Promise<DetectionResult> {
    try {
      const formData = new FormData();
      const response = await fetch(frameUri);
      const blob = await response.blob();
      
      formData.append('file', blob, 'frame.jpg');
      
      const result = await axios.post(
        `${API_BASE}/detection/detect-frame`,
        formData
      );
      
      return result.data;
    } catch (error) {
      console.error('Frame detection error:', error);
      return { success: false };
    }
  }

  /**
   * Get translation history
   */
  async getHistory(limit: number = 50) {
    try {
      const result = await axios.get(
        `${API_BASE}/history/?limit=${limit}`
      );
      return result.data.entries;
    } catch (error) {
      console.error('History error:', error);
      return [];
    }
  }

  /**
   * Get statistics
   */
  async getStats() {
    try {
      const result = await axios.get(`${API_BASE}/history/stats`);
      return result.data;
    } catch (error) {
      console.error('Stats error:', error);
      return null;
    }
  }

  /**
   * Add to history
   */
  async addToHistory(prediction: string, confidence: number) {
    try {
      await axios.post(`${API_BASE}/history/add`, {
        prediction,
        confidence,
      });
    } catch (error) {
      console.error('Add to history error:', error);
    }
  }
}

export default new TranslationService();
"""

# 2. REACT COMPONENT EXAMPLE
# ============================================

"""
// frontend/app/(tabs)/index.tsx

import React, { useRef, useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  Image,
  ActivityIndicator,
} from 'react-native';
import { CameraView, useCameraPermissions } from 'expo-camera';
import * as ImagePicker from 'expo-image-picker';
import TranslationService from '@/services/translationService';

export default function HomeScreen() {
  const cameraRef = useRef(null);
  const [permission, requestPermission] = useCameraPermissions();
  const [prediction, setPrediction] = useState<string>('');
  const [confidence, setConfidence] = useState<number>(0);
  const [loading, setLoading] = useState(false);
  const [handedness, setHandedness] = useState('');

  // Handle camera permission
  if (!permission?.granted) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
        <TouchableOpacity onPress={requestPermission}>
          <Text>Grant Camera Permission</Text>
        </TouchableOpacity>
      </View>
    );
  }

  // Capture and detect
  const handleCapture = async () => {
    setLoading(true);
    try {
      const photo = await cameraRef.current?.takePictureAsync();
      if (photo) {
        const result = await TranslationService.detectFromImage(photo.uri);
        
        if (result.success) {
          setPrediction(result.prediction);
          setConfidence(result.confidence);
          setHandedness(result.handedness);
          
          // Add to history
          await TranslationService.addToHistory(
            result.prediction,
            result.confidence
          );
        }
      }
    } catch (error) {
      console.error('Capture error:', error);
    } finally {
      setLoading(false);
    }
  };

  // Pick image from gallery
  const handlePickImage = async () => {
    setLoading(true);
    try {
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        allowsEditing: true,
      });

      if (!result.canceled) {
        const detection = await TranslationService.detectFromImage(
          result.assets[0].uri
        );
        
        if (detection.success) {
          setPrediction(detection.prediction);
          setConfidence(detection.confidence);
          setHandedness(detection.handedness);
        }
      }
    } catch (error) {
      console.error('Pick image error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={{ flex: 1 }}>
      <CameraView ref={cameraRef} style={{ flex: 1 }} facing="front">
        <View
          style={{
            flex: 1,
            justifyContent: 'flex-end',
            alignItems: 'center',
            paddingBottom: 20,
          }}
        >
          {/* Result Display */}
          {prediction && (
            <View
              style={{
                backgroundColor: 'rgba(0,0,0,0.7)',
                padding: 20,
                borderRadius: 10,
                marginBottom: 20,
              }}
            >
              <Text style={{ fontSize: 48, color: 'white', fontWeight: 'bold' }}>
                {prediction}
              </Text>
              <Text style={{ color: 'white', marginTop: 10 }}>
                Confidence: {(confidence * 100).toFixed(1)}%
              </Text>
              <Text style={{ color: 'white' }}>
                Hand: {handedness}
              </Text>
            </View>
          )}

          {/* Loading Indicator */}
          {loading && <ActivityIndicator size="large" color="white" />}

          {/* Buttons */}
          <View style={{ flexDirection: 'row', gap: 10 }}>
            <TouchableOpacity
              onPress={handleCapture}
              disabled={loading}
              style={{
                backgroundColor: '#007AFF',
                padding: 15,
                borderRadius: 8,
              }}
            >
              <Text style={{ color: 'white', fontWeight: 'bold' }}>
                Capture & Detect
              </Text>
            </TouchableOpacity>

            <TouchableOpacity
              onPress={handlePickImage}
              disabled={loading}
              style={{
                backgroundColor: '#34C759',
                padding: 15,
                borderRadius: 8,
              }}
            >
              <Text style={{ color: 'white', fontWeight: 'bold' }}>
                Pick Image
              </Text>
            </TouchableOpacity>
          </View>
        </View>
      </CameraView>
    </View>
  );
}
"""

# 3. HISTORY SCREEN COMPONENT
# ============================================

"""
// frontend/app/(tabs)/history.tsx

import React, { useEffect, useState } from 'react';
import { View, Text, FlatList, TouchableOpacity } from 'react-native';
import TranslationService from '@/services/translationService';

export default function HistoryScreen() {
  const [history, setHistory] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [historyData, statsData] = await Promise.all([
        TranslationService.getHistory(100),
        TranslationService.getStats(),
      ]);
      
      setHistory(historyData);
      setStats(statsData);
    } catch (error) {
      console.error('Load error:', error);
    } finally {
      setLoading(false);
    }
  };

  const renderItem = ({ item }) => (
    <View
      style={{
        padding: 10,
        borderBottomWidth: 1,
        borderBottomColor: '#ccc',
      }}
    >
      <Text style={{ fontSize: 18, fontWeight: 'bold' }}>
        {item.prediction}
      </Text>
      <Text style={{ color: '#666' }}>
        Confidence: {(item.confidence * 100).toFixed(1)}%
      </Text>
      <Text style={{ color: '#999', fontSize: 12 }}>
        {new Date(item.timestamp).toLocaleString()}
      </Text>
    </View>
  );

  return (
    <View style={{ flex: 1, padding: 10 }}>
      {stats && (
        <View
          style={{
            backgroundColor: '#f0f0f0',
            padding: 15,
            borderRadius: 8,
            marginBottom: 15,
          }}
        >
          <Text style={{ fontSize: 16, fontWeight: 'bold' }}>Statistics</Text>
          <Text>Total Predictions: {stats.total_predictions}</Text>
          <Text>Unique Signs: {stats.unique_signs}</Text>
          <Text>
            Average Confidence:{' '}
            {(stats.average_confidence * 100).toFixed(1)}%
          </Text>
          <Text>Most Common: {stats.most_common}</Text>
        </View>
      )}

      <TouchableOpacity
        onPress={loadData}
        style={{
          backgroundColor: '#007AFF',
          padding: 10,
          borderRadius: 8,
          marginBottom: 10,
        }}
      >
        <Text style={{ color: 'white', textAlign: 'center' }}>
          Refresh
        </Text>
      </TouchableOpacity>

      <FlatList
        data={history}
        renderItem={renderItem}
        keyExtractor={(item) => item.id.toString()}
        refreshing={loading}
        onRefresh={loadData}
      />
    </View>
  );
}
"""

# 4. AXIOS CONFIGURATION
# ============================================

"""
// frontend/services/axiosConfig.ts

import axios from 'axios';

// For development (local backend)
const API_URL = 'http://localhost:8000';

// For production
// const API_URL = 'https://your-production-api.com';

const apiClient = axios.create({
  baseURL: API_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    // Add auth token if needed
    // const token = AsyncStorage.getItem('authToken');
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`;
    // }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle errors globally
    console.error('API Error:', error.response?.status, error.message);
    return Promise.reject(error);
  }
);

export default apiClient;
"""

# 5. ENVIRONMENT CONFIGURATION
# ============================================

"""
// frontend/.env

EXPO_PUBLIC_API_URL=http://localhost:8000
EXPO_PUBLIC_API_TIMEOUT=10000
"""

# 6. TESTING THE INTEGRATION
# ============================================

"""
Steps to test integration:

1. Backend running:
   $ cd backend
   $ python app.py
   
2. Frontend running:
   $ cd frontend
   $ npx expo start

3. Test detection:
   - Open Expo app on phone
   - Allow camera permission
   - Point camera at your hand showing a sign
   - Press "Capture & Detect"
   - Should see prediction with confidence

4. View history:
   - Switch to History tab
   - See all predictions
   - Check statistics

5. Test with gallery image:
   - Press "Pick Image"
   - Select image with hand sign
   - Verify detection works
"""

# 7. TROUBLESHOOTING
# ============================================

"""
Common Issues:

1. Connection refused:
   - Check backend is running: http://localhost:8000/health
   - Check frontend has correct API_URL

2. CORS errors:
   - Backend should handle CORS automatically
   - If not, update app.py CORS settings

3. Camera permission denied:
   - Allow in app settings
   - Restart app

4. No hands detected:
   - Ensure good lighting
   - Show hand fully in frame
   - Verify backend hand detection is working

5. Slow responses:
   - Train model first
   - Reduce image size
   - Use detect-frame instead of detect-image
"""
