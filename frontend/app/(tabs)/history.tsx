import { Colors } from '@/constants/theme';
import { useColorScheme } from '@/hooks/use-color-scheme';
import { clearHistory, getTranslationHistory } from '@/utils/translationService';
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

interface TranslationRecord {
  id: string;
  text: string;
  date: string;
}

export default function HistoryScreen() {
  const colorScheme = useColorScheme() ?? 'light';
  const [history, setHistory] = useState<TranslationRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);

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
        onPress: () => {
          setHistory(history.filter((item) => item.id !== id));
        },
      },
    ]);
  };

  const renderHistoryItem = ({ item }: { item: TranslationRecord }) => (
    <TouchableOpacity
      style={[
        styles.historyItem,
        {
          backgroundColor: Colors[colorScheme].background,
          borderColor: Colors[colorScheme].tabIconDefault,
        },
      ]}
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
