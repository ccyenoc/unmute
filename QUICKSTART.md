# Sign Language Translator - Quick Start Guide

## 🚀 Getting the App Running

### Option 1: Run with Expo Go (Fastest)

Perfect for testing on your device without building.

1. **Install Expo Go on your phone:**
   - iOS: Download from App Store
   - Android: Download from Google Play Store

2. **Start the dev server:**
   ```bash
   cd /Users/cye/unmute/SignLanguageTranslator
   npm start
   ```

3. **Scan the QR code** displayed in terminal with Expo Go app

### Option 2: iOS Simulator (Mac only)

1. **Make sure you have Xcode installed**
   ```bash
   xcode-select --install
   ```

2. **Start the dev server:**
   ```bash
   npm start
   ```

3. **Press `i`** in terminal to launch iOS Simulator

### Option 3: Android Emulator

1. **Install Android Studio and set up emulator**

2. **Start the dev server:**
   ```bash
   npm start
   ```

3. **Press `a`** in terminal to launch Android Emulator

## 📱 App Features to Try

### Translator Screen (Tab 1)
1. **Grant Camera Permission** - First time setup
2. **Tap "Start Translation"** - Simulates 3-second recording
3. **View the Result** - Displays translated text
4. **Hear It Spoken** - Text would be read aloud (in production)

### History Screen (Tab 2)
1. **See Past Translations** - Auto-populated with recent translations
2. **Long-press Items** - Delete individual translations
3. **Clear All** - Remove entire history

### Settings Screen (Tab 3)
1. **Toggle Audio & Feedback** - Configure sound and vibration
2. **Configure Recognition** - Auto-capture mode
3. **Select Languages** - Input/output language choice
4. **View Info** - Privacy policy and about

## 🛠️ Available Commands

```bash
# Start development server
npm start

# Run on iOS simulator
npm run ios

# Run on Android emulator
npm run android

# Run on web
npm run web

# Check code quality
npm run lint

# Reset to fresh project
npm run reset-project
```

## 💡 Tips for Development

### Reload the App
- **iOS/Android:** Press `r` in terminal
- **Full Reload:** Press `Ctrl+Shift+R` (or `Cmd+Shift+R` on Mac)

### Debug Issues
- Check terminal output for errors
- Use React Native Debugger
- Check permissions in device settings

### Test Different Devices
- Use different simulators/emulators
- Test on physical devices with Expo Go
- Check device orientation changes

## 🔧 Making Changes

The app uses **file-based routing**, so:
- Files in `app/(tabs)/` become screens
- Each `.tsx` file is a route
- No routing configuration needed!

### Edit Files
- `app/(tabs)/index.tsx` - Translator screen
- `app/(tabs)/history.tsx` - History screen
- `app/(tabs)/settings.tsx` - Settings screen
- `utils/translationService.ts` - Translation logic
- `constants/theme.ts` - Colors and theming

Changes auto-reload when you save!

## 📚 Common Issues & Solutions

**Q: Camera permission not working?**
- A: Make sure you granted camera access in phone settings

**Q: "Module not found" error?**
- A: Run `npm install` to ensure all dependencies are installed

**Q: App won't reload?**
- A: Press `r` in terminal or force quit and restart Expo

**Q: Translation feature always returns the same thing?**
- A: This is intentional! Replace `simulateSignTranslation()` with real ML model

## 🎯 Next Steps

1. **Integrate Real ML Model:**
   - Replace `simulateSignTranslation()` in `utils/translationService.ts`
   - Use TensorFlow.js or on-device ML models

2. **Add Text-to-Speech:**
   - Install `expo-speech`
   - Update `speakTranslation()` function

3. **Enhance UI:**
   - Add more animations
   - Customize colors and fonts
   - Add loading states

4. **Deploy:**
   - Use EAS Build for App Store/Play Store
   - Set up CI/CD pipeline

## 📖 Resources

- [Expo Documentation](https://docs.expo.dev)
- [React Native Docs](https://reactnative.dev)
- [Expo Router Guide](https://docs.expo.dev/router/introduction)
- [TypeScript React Native](https://reactnative.dev/docs/typescript)

## 🤝 Need Help?

- Check the main README.md for detailed documentation
- Review inline code comments
- Check Expo CLI output for specific errors
- Visit community forums and Discord

---

**Enjoy building your sign language translator! 🤟**
