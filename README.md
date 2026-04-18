# Sign Language Translator 🤟

A React Native mobile application that translates sign language into text and speech in real-time. This app supports both iOS and Android platforms using Expo and provides a modern, user-friendly interface for sign language recognition and translation.

## Features

✨ **Core Functionality:**
- Real-time sign language detection via camera
- Translation of sign language to text
- Text-to-speech audio output
- Translation history tracking
- Configurable settings

🎨 **User Experience:**
- iOS/Apple-style design system
- Dark and light mode support
- Smooth animations and haptic feedback
- Intuitive tab-based navigation
- Clean, modern UI components

📱 **Platform Support:**
- iOS (iPhone/iPad)
- Android (phones/tablets)
- Responsive design for various screen sizes

## Getting Started

### Prerequisites

- Node.js (v18 or higher)
- npm or yarn package manager
- Expo CLI (`npm install -g expo-cli`)
- iOS Simulator (for iOS development) or Android Emulator (for Android development)

### Installation

1. **Clone or navigate to the project directory:**
   ```bash
   cd /Users/cye/unmute/SignLanguageTranslator
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start the development server:**
   ```bash
   npm start
   ```

### Running on Different Platforms

**iOS Simulator:**
```bash
npm run ios
```

**Android Emulator:**
```bash
npm run android
```

**Web (development only):**
```bash
npm run web
```

## Project Structure

```
SignLanguageTranslator/
├── app/
│   ├── (tabs)/
│   │   ├── _layout.tsx          # Tab navigation layout
│   │   ├── index.tsx            # Translator/camera screen
│   │   ├── history.tsx          # Translation history screen
│   │   └── settings.tsx         # Settings and configuration
│   ├── _layout.tsx              # Root layout
│   └── modal.tsx                # Modal screen template
├── utils/
│   └── translationService.ts    # Translation and storage utilities
├── components/                  # Reusable UI components
├── hooks/                       # Custom React hooks
├── constants/                   # App constants and themes
├── app.json                     # Expo configuration
├── package.json                 # Dependencies
├── tsconfig.json                # TypeScript configuration
└── README.md                    # This file
```

## Screens

### 1. Translator Screen (Home)
- Camera preview showing live feed
- Start translation button
- Real-time translation display
- Recording indicator
- Processing state indicator

### 2. History Screen
- List of past translations
- Timestamp for each translation
- Long-press to delete individual items
- Clear all history button
- Empty state when no translations exist

### 3. Settings Screen
- Audio and feedback preferences
- Recognition configuration
- Language selection (Input/Output)
- Privacy policy
- About information

## Core Functionality

### Translation Service (`utils/translationService.ts`)

The translation service provides the following functions:

```typescript
// Simulate sign language translation
simulateSignTranslation(): Promise<string>

// Store a translation in device storage
storeTranslation(translation: string): Promise<void>

// Get translation history
getTranslationHistory(): Promise<TranslationRecord[]>

// Clear all history
clearHistory(): Promise<void>

// Delete a specific translation
deleteTranslation(id: string): Promise<void>
```

**Note:** Currently, the translation feature uses simulated data. In a production app, you would integrate an actual ML model for sign language recognition.

## Technology Stack

- **Framework:** React Native with Expo
- **Language:** TypeScript
- **Navigation:** Expo Router (file-based routing)
- **Storage:** AsyncStorage (device local storage)
- **Camera:** expo-camera
- **UI:** React Native built-in components
- **Styling:** StyleSheet (CSS-in-JS)

## Dependencies

Key dependencies include:
- `expo`: Development and deployment framework
- `expo-router`: File-based routing system
- `expo-camera`: Camera access and video capture
- `expo-av`: Audio and video playback
- `@react-native-async-storage/async-storage`: Local data storage
- `react-navigation`: Navigation library
- React Native

See `package.json` for complete dependency list.

## Development Guidelines

### Code Quality
```bash
npm run lint
```

Run the linter to check for code style issues and potential errors.

### Best Practices

1. **Component Organization:** Organize components by feature
2. **Type Safety:** Use TypeScript for all code
3. **State Management:** Use React hooks for state
4. **Error Handling:** Implement proper error boundaries
5. **Performance:** Optimize re-renders with useMemo and useCallback
6. **Testing:** Add unit tests for critical functions

### Adding New Features

1. Create screens in `app/(tabs)/` for tab navigation
2. Create utility functions in `utils/` for business logic
3. Add reusable components in `components/`
4. Use constants from `constants/` for theming and configuration
5. Follow TypeScript types and interfaces

## Permissions

The app requires the following permissions:

- **Camera:** Access to device camera for sign language detection
- **Microphone:** (Optional) For audio input if needed
- **Storage:** Read/write access for translation history

On iOS: Permissions are handled via `Info.plist`
On Android: Permissions are handled via `AndroidManifest.xml` (auto-configured by Expo)

## Configuration

### app.json

The Expo configuration file includes:
- App name and slug
- Supported platforms and versions
- Icon and splash screen assets
- Plugins and experimental features
- iOS and Android specific settings

## Theming

The app supports iOS/Apple design system with automatic light and dark mode detection:

```typescript
import { useColorScheme } from '@/hooks/use-color-scheme';

// Get current color scheme
const colorScheme = useColorScheme();

// Use theme colors
const { background, text, tint } = Colors[colorScheme];
```

## Building for Production

### iOS Build
```bash
eas build --platform ios
```

### Android Build
```bash
eas build --platform android
```

Requires EAS CLI and an Expo account.

## Future Enhancements

- 🧠 Integration with ML model for actual sign language recognition
- 🔊 Real text-to-speech synthesis
- 🌍 Support for multiple sign languages (ASL, LSF, ISL, etc.)
- 📊 Analytics and usage statistics
- 🤖 User-specific translation accuracy
- 🔐 Cloud backup of translation history
- 🎓 Educational mode for learning sign language
- 👥 Social features for sharing translations

## Troubleshooting

**Camera not working:**
- Check that camera permissions are granted
- Ensure you have a camera on your device
- Test with `expo-camera` example app

**Translation history not saving:**
- Verify AsyncStorage is properly installed
- Check device storage availability
- Clear app cache if experiencing issues

**Performance issues:**
- Monitor with React DevTools
- Profile with Chrome DevTools
- Optimize heavy computations with useMemo

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run lint and tests
5. Submit a pull request

## License

This project is available for educational and commercial use. See LICENSE file for details.

## Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check existing documentation
- Refer to [Expo documentation](https://docs.expo.dev/)
- Check [React Native documentation](https://reactnative.dev/)

## Acknowledgments

- Built with [Expo](https://expo.dev)
- Uses [React Navigation](https://reactnavigation.org/)
- Inspired by iOS design principles
- Sign language recognition integration ready for ML models

---

**Happy translating! 🤟**
