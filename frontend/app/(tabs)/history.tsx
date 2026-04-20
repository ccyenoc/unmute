import { Colors } from '@/constants/theme';
import { useColorScheme } from '@/hooks/use-color-scheme';
import {
    clearHistory,
    deleteTranslation,
    getTranslationHistory,
    TranslationRecord,
} from '@/utils/translationService';
import { useFocusEffect } from '@react-navigation/native';
import React, { useState } from 'react';
import {
    ActivityIndicator,
    Alert,
    FlatList,
    StyleSheet,
    Text,
    TouchableOpacity,
    View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

export default function HistoryScreen() {
  const colorScheme = useColorScheme() ?? 'light';
  const [history, setHistory] = useState<TranslationRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedRecordId, setSelectedRecordId] = useState<string | null>(null);

  useFocusEffect(
    React.useCallback(() => {
      loadHistory();
    }, [])
  );

  const loadHistory = async () => {
    setIsLoading(true);
    try {
      const data = await getTranslationHistory();
      setHistory(data);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClearHistory = () => {
    Alert.alert('Clear History', 'Are you sure you want to delete all translation history?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Delete',
        style: 'destructive',
        onPress: async () => {
          try {
            await clearHistory();
            setHistory([]);
          } catch {
            Alert.alert('Error', 'Failed to clear history');
          }
        },
      },
    ]);
  };

  const handleDeleteItem = (id: string) => {
    Alert.alert('Delete', 'Delete this translation?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Delete',
        style: 'destructive',
        onPress: async () => {
          try {
            await deleteTranslation(id);
            setHistory((current) => current.filter((item) => item.id !== id));
            setSelectedRecordId((current) => (current === id ? null : current));
          } catch {
            Alert.alert('Error', 'Failed to delete history item');
          }
        },
      },
    ]);
  };

  const selectedRecord = history.find((item) => item.id === selectedRecordId) ?? null;

  const renderHistoryItem = ({ item }: { item: TranslationRecord }) => (
    <TouchableOpacity
      style={[
        styles.historyItem,
        {
          backgroundColor: Colors[colorScheme].background,
          borderColor: Colors[colorScheme].tabIconDefault,
        },
        item.id === selectedRecordId ? styles.historyItemSelected : null,
      ]}
      onPress={() => setSelectedRecordId(item.id)}
      onLongPress={() => handleDeleteItem(item.id)}
    >
      <View style={styles.historyItemContent}>
        <Text style={[styles.historyText, { color: Colors[colorScheme].text }]}>
          {item.text}
        </Text>
        <Text style={[styles.historyDate, { color: Colors[colorScheme].tabIconDefault }]}>
          {item.date}
        </Text>
      </View>
      <Text style={[styles.dragHandle, { color: Colors[colorScheme].tabIconDefault }]}>
        ⋮
      </Text>
    </TouchableOpacity>
  );

  if (isLoading) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: Colors[colorScheme].background }]}>
        <ActivityIndicator size="large" color={Colors[colorScheme].tint} />
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: Colors[colorScheme].background }]}>
      {history.length === 0 ? (
        <View style={styles.emptyContainer}>
          <Text style={[styles.emptyTitle, { color: Colors[colorScheme].text }]}>
            No translations yet
          </Text>
          <Text style={[styles.emptySubtitle, { color: Colors[colorScheme].tabIconDefault }]}>
            Start translating sign language to see your history here
          </Text>
        </View>
      ) : (
        <>
          <FlatList
            data={history}
            renderItem={renderHistoryItem}
            keyExtractor={(item) => item.id}
            contentContainerStyle={styles.listContent}
            scrollEnabled={true}
          />
          {selectedRecord ? (
            <View
              style={[
                styles.detailsPanel,
                {
                  backgroundColor: Colors[colorScheme].background,
                  borderColor: Colors[colorScheme].tabIconDefault,
                },
              ]}
            >
              <View style={styles.panelHeaderRow}>
                <Text style={[styles.detailsTitle, { color: Colors[colorScheme].text }]}>Session Details</Text>
                <Text style={[styles.detailsDateText, { color: Colors[colorScheme].tabIconDefault }]}> 
                  {selectedRecord.date}
                </Text>
              </View>

              <View style={styles.translationCard}>
                <Text style={styles.sectionLabel}>Translation</Text>
                <Text style={[styles.detailsTranslationText, { color: Colors[colorScheme].text }]}> 
                  {selectedRecord.text}
                </Text>
              </View>

              <View style={styles.separator} />
              <Text style={[styles.detailsTitle, { color: Colors[colorScheme].text }]}>Facial Expression API</Text>

              {selectedRecord.emotion ? (
                <View style={styles.emotionCard}>
                  <View style={styles.emotionRow}>
                    <Text style={[styles.fieldLabel, { color: Colors[colorScheme].tabIconDefault }]}>Emotion</Text>
                    <Text style={[styles.fieldValueStrong, { color: Colors[colorScheme].text }]}> 
                      {selectedRecord.emotion.emotion}
                    </Text>
                  </View>
                  <View style={styles.emotionRow}>
                    <Text style={[styles.fieldLabel, { color: Colors[colorScheme].tabIconDefault }]}>Confidence</Text>
                    <Text style={[styles.fieldValue, { color: Colors[colorScheme].text }]}> 
                      {selectedRecord.emotion.confidence}
                    </Text>
                  </View>
                  <View style={styles.emotionRow}>
                    <Text style={[styles.fieldLabel, { color: Colors[colorScheme].tabIconDefault }]}>Faces</Text>
                    <Text style={[styles.fieldValue, { color: Colors[colorScheme].text }]}> 
                      {selectedRecord.emotion.faces_detected}
                    </Text>
                  </View>
                  <View style={styles.emotionRow}>
                    <Text style={[styles.fieldLabel, { color: Colors[colorScheme].tabIconDefault }]}>Provider</Text>
                    <Text style={[styles.fieldValue, { color: Colors[colorScheme].text }]}> 
                      {selectedRecord.emotion.provider ?? 'unknown'}
                    </Text>
                  </View>
                  <View style={styles.emotionRowLast}>
                    <Text style={[styles.fieldLabel, { color: Colors[colorScheme].tabIconDefault }]}>Fusion</Text>
                    <Text style={[styles.fieldValue, { color: Colors[colorScheme].text }]}> 
                      {selectedRecord.emotion.fusion_status ?? 'aligned'}
                    </Text>
                  </View>
                </View>
              ) : (
                <Text style={[styles.detailsEmptyText, { color: Colors[colorScheme].tabIconDefault }]}>
                  No facial expression data stored for this translation.
                </Text>
              )}
            </View>
          ) : null}
          <TouchableOpacity
            style={[styles.clearButton, { backgroundColor: '#FF3B30' }]}
            onPress={handleClearHistory}
          >
            <Text style={styles.clearButtonText}>Clear All History</Text>
          </TouchableOpacity>
        </>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  listContent: {
    padding: 12,
    paddingBottom: 80,
  },
  emptyContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 24,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 8,
  },
  emptySubtitle: {
    fontSize: 14,
    textAlign: 'center',
  },
  historyItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 12,
    paddingHorizontal: 16,
    marginBottom: 8,
    borderRadius: 8,
    borderWidth: 1,
  },
  historyItemSelected: {
    borderColor: '#007AFF',
    borderWidth: 2,
  },
  historyItemContent: {
    flex: 1,
  },
  historyText: {
    fontSize: 14,
    fontWeight: '500',
    marginBottom: 4,
  },
  historyDate: {
    fontSize: 12,
  },
  dragHandle: {
    fontSize: 18,
    marginLeft: 8,
  },
  detailsPanel: {
    marginHorizontal: 12,
    marginBottom: 90,
    borderRadius: 14,
    borderWidth: 1,
    padding: 14,
    boxShadow: '0px 8px 18px rgba(0, 0, 0, 0.1)',
  },
  panelHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  detailsTitle: {
    fontSize: 12,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  translationCard: {
    borderRadius: 10,
    paddingVertical: 10,
    paddingHorizontal: 12,
    backgroundColor: 'rgba(0, 122, 255, 0.08)',
    borderWidth: 1,
    borderColor: 'rgba(0, 122, 255, 0.18)',
  },
  sectionLabel: {
    fontSize: 10,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    color: '#0A84FF',
    fontWeight: '700',
    marginBottom: 6,
  },
  detailsTranslationText: {
    fontSize: 17,
    fontWeight: '600',
    lineHeight: 23,
  },
  detailsDateText: {
    fontSize: 11,
  },
  separator: {
    marginVertical: 14,
    height: 1,
    backgroundColor: 'rgba(127,127,127,0.25)',
  },
  emotionCard: {
    borderRadius: 10,
    backgroundColor: 'rgba(17, 24, 39, 0.06)',
    borderWidth: 1,
    borderColor: 'rgba(17, 24, 39, 0.12)',
    paddingHorizontal: 10,
    paddingVertical: 6,
  },
  emotionRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 6,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(127,127,127,0.16)',
  },
  emotionRowLast: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 6,
  },
  fieldLabel: {
    fontSize: 12,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 0.4,
  },
  fieldValue: {
    fontSize: 13,
    fontWeight: '500',
  },
  fieldValueStrong: {
    fontSize: 14,
    fontWeight: '700',
  },
  detailsEmptyText: {
    fontSize: 13,
    fontStyle: 'italic',
  },
  clearButton: {
    position: 'absolute',
    bottom: 20,
    left: 16,
    right: 16,
    paddingVertical: 14,
    borderRadius: 8,
    alignItems: 'center',
  },
  clearButtonText: {
    color: '#FFFFFF',
    fontWeight: '600',
    fontSize: 16,
  },
});
