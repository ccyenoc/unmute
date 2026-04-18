import React, { useState } from 'react';
import {
  StyleSheet,
  View,
  SafeAreaView,
  ScrollView,
  Switch,
  Text,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { Colors } from '@/frontend/constants/theme';
import { useColorScheme } from '@/hooks/use-color-scheme';

export default function SettingsScreen() {
  const colorScheme = useColorScheme();
  const [enableSound, setEnableSound] = useState(true);
  const [enableVibration, setEnableVibration] = useState(true);
  const [enableAutoCapture, setEnableAutoCapture] = useState(false);

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
          <Text style={[styles.sectionTitle, { color: Colors[colorScheme].text }]}>
            Audio & Feedback
          </Text>

          <View
            style={[
              styles.settingItem,
              { borderColor: Colors[colorScheme].tabIconDefault },
            ]}
          >
            <Text style={[styles.settingLabel, { color: Colors[colorScheme].text }]}>
              Text-to-Speech
            </Text>
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

          <View
            style={[
              styles.settingItem,
              { borderColor: Colors[colorScheme].tabIconDefault },
            ]}
          >
            <Text style={[styles.settingLabel, { color: Colors[colorScheme].text }]}>
              Vibration Feedback
            </Text>
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
          <Text style={[styles.sectionTitle, { color: Colors[colorScheme].text }]}>
            Recognition
          </Text>

          <View
            style={[
              styles.settingItem,
              { borderColor: Colors[colorScheme].tabIconDefault },
            ]}
          >
            <Text style={[styles.settingLabel, { color: Colors[colorScheme].text }]}>
              Auto-Capture
            </Text>
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
          <Text style={[styles.sectionTitle, { color: Colors[colorScheme].text }]}>
            Language
          </Text>

          <TouchableOpacity
            style={[
              styles.settingButton,
              { borderColor: Colors[colorScheme].tabIconDefault },
            ]}
          >
            <View>
              <Text style={[styles.settingLabel, { color: Colors[colorScheme].text }]}>
                Input Language
              </Text>
              <Text style={[styles.settingValue, { color: Colors[colorScheme].tabIconDefault }]}>
                American Sign Language (ASL)
              </Text>
            </View>
            <Text style={[styles.buttonArrow, { color: Colors[colorScheme].tint }]}>›</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[
              styles.settingButton,
              { borderColor: Colors[colorScheme].tabIconDefault },
            ]}
          >
            <View>
              <Text style={[styles.settingLabel, { color: Colors[colorScheme].text }]}>
                Output Language
              </Text>
              <Text style={[styles.settingValue, { color: Colors[colorScheme].tabIconDefault }]}>
                English
              </Text>
            </View>
            <Text style={[styles.buttonArrow, { color: Colors[colorScheme].tint }]}>›</Text>
          </TouchableOpacity>
        </View>

        <View style={styles.section}>
          <TouchableOpacity
            style={[
              styles.settingButton,
              { borderColor: Colors[colorScheme].tabIconDefault },
            ]}
            onPress={handlePrivacy}
          >
            <Text style={[styles.settingLabel, { color: Colors[colorScheme].text }]}>
              Privacy Policy
            </Text>
            <Text style={[styles.buttonArrow, { color: Colors[colorScheme].tint }]}>›</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[
              styles.settingButton,
              { borderColor: Colors[colorScheme].tabIconDefault },
            ]}
            onPress={handleAbout}
          >
            <Text style={[styles.settingLabel, { color: Colors[colorScheme].text }]}>
              About
            </Text>
            <Text style={[styles.buttonArrow, { color: Colors[colorScheme].tint }]}>›</Text>
          </TouchableOpacity>
        </View>

        <Text style={[styles.versionText, { color: Colors[colorScheme].tabIconDefault }]}>
          Version 1.0.0
        </Text>
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
