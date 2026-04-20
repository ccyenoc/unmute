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
  SafeAreaView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';

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
              <Text style={[styles.detailsTitle, { color: Colors[colorScheme].text }]}>Selected Translation</Text>
              <Text style={[styles.detailsTranslationText, { color: Colors[colorScheme].text }]}>
                {selectedRecord.text}
              </Text>
              <Text style={[styles.detailsDateText, { color: Colors[colorScheme].tabIconDefault }]}>
                {selectedRecord.date}
              </Text>

              <View style={styles.separator} />
              <Text style={[styles.detailsTitle, { color: Colors[colorScheme].text }]}>Facial Expression API</Text>

              {selectedRecord.emotion ? (
                <>
                  <Text style={[styles.detailsFieldText, { color: Colors[colorScheme].text }]}> 
                    Emotion: {selectedRecord.emotion.emotion}
                  </Text>
                  <Text style={[styles.detailsFieldText, { color: Colors[colorScheme].text }]}> 
                    Confidence: {selectedRecord.emotion.confidence}
                  </Text>
                  <Text style={[styles.detailsFieldText, { color: Colors[colorScheme].text }]}> 
                    Faces Detected: {selectedRecord.emotion.faces_detected}
                  </Text>
                  <Text style={[styles.detailsFieldText, { color: Colors[colorScheme].text }]}> 
                    Provider: {selectedRecord.emotion.provider ?? 'unknown'}
                  </Text>
                  <Text style={[styles.detailsFieldText, { color: Colors[colorScheme].text }]}> 
                    Fusion: {selectedRecord.emotion.fusion_status ?? 'aligned'}
                  </Text>
                </>
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
    borderRadius: 10,
    borderWidth: 1,
    padding: 12,
  },
  detailsTitle: {
    fontSize: 13,
    fontWeight: '700',
    textTransform: 'uppercase',
    marginBottom: 8,
  },
  detailsTranslationText: {
    fontSize: 16,
    fontWeight: '600',
  },
  detailsDateText: {
    marginTop: 4,
    fontSize: 12,
  },
  separator: {
    marginVertical: 12,
    height: 1,
    backgroundColor: 'rgba(127,127,127,0.3)',
  },
  detailsFieldText: {
    fontSize: 13,
    marginBottom: 6,
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
