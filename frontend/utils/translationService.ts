import AsyncStorage from '@react-native-async-storage/async-storage';

const HISTORY_KEY = 'signlanguage_history';

// Sample translations for simulation
const SAMPLE_TRANSLATIONS = [
  'Hello, how are you?',
  'Thank you very much',
  'Nice to meet you',
  'What is your name?',
  'I am learning sign language',
  'This is wonderful',
  'Good morning',
  'See you later',
  'Have a great day',
  'Can you help me?',
];

export interface TranslationRecord {
  id: string;
  text: string;
  date: string;
}

/**
 * Simulates sign language translation by returning a random sample translation
 * In a real application, this would call an actual ML model or API
 */
export async function simulateSignTranslation(): Promise<string> {
  // Simulate processing time
  await new Promise((resolve) => setTimeout(resolve, 1000));
  
  // Return a random translation
  const randomIndex = Math.floor(Math.random() * SAMPLE_TRANSLATIONS.length);
  return SAMPLE_TRANSLATIONS[randomIndex];
}

/**
 * Stores a translation in the device's local storage
 */
export async function storeTranslation(translation: string): Promise<void> {
  try {
    const history = await getTranslationHistory();
    
    const newRecord: TranslationRecord = {
      id: Date.now().toString(),
      text: translation,
      date: new Date().toLocaleString(),
    };
    
    // Add new record to the beginning of the array
    history.unshift(newRecord);
    
    // Keep only the last 50 translations
    if (history.length > 50) {
      history.pop();
    }
    
    await AsyncStorage.setItem(HISTORY_KEY, JSON.stringify(history));
  } catch (error) {
    console.error('Error storing translation:', error);
    throw error;
  }
}

/**
 * Retrieves the translation history from storage
 */
export async function getTranslationHistory(): Promise<TranslationRecord[]> {
  try {
    const history = await AsyncStorage.getItem(HISTORY_KEY);
    return history ? JSON.parse(history) : [];
  } catch (error) {
    console.error('Error retrieving translation history:', error);
    return [];
  }
}

/**
 * Clears all translation history
 */
export async function clearHistory(): Promise<void> {
  try {
    await AsyncStorage.removeItem(HISTORY_KEY);
  } catch (error) {
    console.error('Error clearing history:', error);
    throw error;
  }
}

/**
 * Deletes a single translation from history
 */
export async function deleteTranslation(id: string): Promise<void> {
  try {
    const history = await getTranslationHistory();
    const filtered = history.filter((item) => item.id !== id);
    await AsyncStorage.setItem(HISTORY_KEY, JSON.stringify(filtered));
  } catch (error) {
    console.error('Error deleting translation:', error);
    throw error;
  }
}
