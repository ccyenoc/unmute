import { Colors } from '@/constants/theme';
import { useColorScheme } from '@/hooks/use-color-scheme';
import { resolveBackendBaseUrl } from '@/utils/facialEmotionService';
import { useEffect, useState } from 'react';
import {
    Alert,
    ScrollView,
    StyleSheet,
    Switch,
    Text,
    TouchableOpacity,
    View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

export default function SettingsScreen() {
  const colorScheme = useColorScheme() ?? 'light';
  const [enableSound, setEnableSound] = useState(true);
  const [enableVibration, setEnableVibration] = useState(true);
  const [enableAutoCapture, setEnableAutoCapture] = useState(false);
  const [backendStatus, setBackendStatus] = useState('Loading...');

  const checkBackendConnection = async (url: string) => {
    const normalizedUrl = url.trim().replace(/\/$/, '');
    if (!normalizedUrl) {
      setBackendStatus('Disconnected');
      return;
    }

    setBackendStatus('Checking...');
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 5000);

    try {
      const endpoints = ['/api/facial-emotion/health', '/health'];
      for (const endpoint of endpoints) {
        const response = await fetch(`${normalizedUrl}${endpoint}`, {
          signal: controller.signal,
        });
        if (response.ok) {
          setBackendStatus('Connected');
          return;
        }
      }
      setBackendStatus('Disconnected');
    } catch {
      setBackendStatus('Disconnected');
    } finally {
      clearTimeout(timeout);
    }
  };

  useEffect(() => {
    let mounted = true;

    resolveBackendBaseUrl()
      .then((url) => {
        if (!mounted) {
          return;
        }
        void checkBackendConnection(url);
      })
      .catch(() => {
        if (mounted) {
          setBackendStatus('Unavailable');
        }
      });

    return () => {
      mounted = false;
    };
  }, []);

  const handleAbout = () => {
    Alert.alert(
      'About',
      'Sign Language Translator v1.0.0\n\nTranslate sign language in real-time using AI-powered recognition.',
      [{ text: 'OK' }]
    );
  };

  const handlePrivacy = () => {
    Alert.alert(
      'Privacy Policy',
      'Your camera feed is processed locally and never stored or transmitted.',
      [{ text: 'OK' }]
    );
  };

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: Colors[colorScheme].background }]}>
      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: Colors[colorScheme].text }]}>Audio & Feedback</Text>

          <View style={[styles.settingItem, { borderColor: Colors[colorScheme].tabIconDefault }]}>
            <Text style={[styles.settingLabel, { color: Colors[colorScheme].text }]}>Text-to-Speech</Text>
            <Switch
              value={enableSound}
              onValueChange={setEnableSound}
              trackColor={{
                false: Colors[colorScheme].tabIconDefault,
                true: Colors[colorScheme].tint,
              }}
              thumbColor={enableSound ? Colors[colorScheme].tint : '#f4f3f4'}
            />
          </View>

          <View style={[styles.settingItem, { borderColor: Colors[colorScheme].tabIconDefault }]}>
            <Text style={[styles.settingLabel, { color: Colors[colorScheme].text }]}>Vibration Feedback</Text>
            <Switch
              value={enableVibration}
              onValueChange={setEnableVibration}
              trackColor={{
                false: Colors[colorScheme].tabIconDefault,
                true: Colors[colorScheme].tint,
              }}
              thumbColor={enableVibration ? Colors[colorScheme].tint : '#f4f3f4'}
            />
          </View>
        </View>

        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: Colors[colorScheme].text }]}>Recognition</Text>

          <View style={[styles.settingItem, { borderColor: Colors[colorScheme].tabIconDefault }]}>
            <Text style={[styles.settingLabel, { color: Colors[colorScheme].text }]}>Auto-Capture</Text>
            <Switch
              value={enableAutoCapture}
              onValueChange={setEnableAutoCapture}
              trackColor={{
                false: Colors[colorScheme].tabIconDefault,
                true: Colors[colorScheme].tint,
              }}
              thumbColor={enableAutoCapture ? Colors[colorScheme].tint : '#f4f3f4'}
            />
          </View>

          <View style={styles.settingDescription}>
            <Text style={[styles.descriptionText, { color: Colors[colorScheme].tabIconDefault }]}>
              Automatically detect and translate sign language without pressing a button
            </Text>
          </View>
        </View>

        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: Colors[colorScheme].text }]}>Backend Connection</Text>
          <View style={[styles.backendBox, { borderColor: Colors[colorScheme].tabIconDefault }]}>
            <Text style={[styles.backendHint, { color: Colors[colorScheme].tabIconDefault }]}>
              Backend URL is configured in the app build. This screen only shows connection status.
            </Text>
            <Text style={[styles.backendStatus, { color: Colors[colorScheme].text }]}>Status: {backendStatus}</Text>
          </View>
        </View>

        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: Colors[colorScheme].text }]}>Language</Text>

          <TouchableOpacity style={[styles.settingButton, { borderColor: Colors[colorScheme].tabIconDefault }]}>
            <View>
              <Text style={[styles.settingLabel, { color: Colors[colorScheme].text }]}>Input Language</Text>
              <Text style={[styles.settingValue, { color: Colors[colorScheme].tabIconDefault }]}>American Sign Language (ASL)</Text>
            </View>
            <Text style={[styles.buttonArrow, { color: Colors[colorScheme].tint }]}>›</Text>
          </TouchableOpacity>

          <TouchableOpacity style={[styles.settingButton, { borderColor: Colors[colorScheme].tabIconDefault }]}>
            <View>
              <Text style={[styles.settingLabel, { color: Colors[colorScheme].text }]}>Output Language</Text>
              <Text style={[styles.settingValue, { color: Colors[colorScheme].tabIconDefault }]}>English</Text>
            </View>
            <Text style={[styles.buttonArrow, { color: Colors[colorScheme].tint }]}>›</Text>
          </TouchableOpacity>
        </View>

        <View style={styles.section}>
          <TouchableOpacity
            style={[styles.settingButton, { borderColor: Colors[colorScheme].tabIconDefault }]}
            onPress={handlePrivacy}
          >
            <Text style={[styles.settingLabel, { color: Colors[colorScheme].text }]}>Privacy Policy</Text>
            <Text style={[styles.buttonArrow, { color: Colors[colorScheme].tint }]}>›</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.settingButton, { borderColor: Colors[colorScheme].tabIconDefault }]}
            onPress={handleAbout}
          >
            <Text style={[styles.settingLabel, { color: Colors[colorScheme].text }]}>About</Text>
            <Text style={[styles.buttonArrow, { color: Colors[colorScheme].tint }]}>›</Text>
          </TouchableOpacity>
        </View>

        <Text style={[styles.versionText, { color: Colors[colorScheme].tabIconDefault }]}>Version 1.0.0</Text>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  content: {
    flex: 1,
    paddingVertical: 8,
  },
  section: {
    paddingVertical: 8,
    paddingHorizontal: 16,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 12,
    marginTop: 8,
    textTransform: 'uppercase',
  },
  settingItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 12,
    borderBottomWidth: 1,
  },
  settingButton: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 12,
    borderBottomWidth: 1,
  },
  settingLabel: {
    fontSize: 16,
    fontWeight: '500',
  },
  settingValue: {
    fontSize: 12,
    marginTop: 4,
  },
  buttonArrow: {
    fontSize: 20,
    marginLeft: 8,
  },
  settingDescription: {
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  backendBox: {
    borderWidth: 1,
    borderRadius: 12,
    padding: 12,
  },
  backendHint: {
    fontSize: 12,
    lineHeight: 18,
    marginTop: 8,
  },
  backendStatus: {
    marginTop: 10,
    fontSize: 13,
    fontWeight: '600',
  },
  descriptionText: {
    fontSize: 13,
    lineHeight: 18,
  },
  versionText: {
    textAlign: 'center',
    fontSize: 12,
    marginVertical: 24,
  },
});
