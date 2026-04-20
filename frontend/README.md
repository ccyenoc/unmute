# Sign Language Translator Frontend

Expo React Native frontend for real-time sign language translation and facial emotion integration.

## Run Frontend (Copy/Paste)

From the project root:

```bash
cd frontend
npm install
npx expo start --tunnel --clear
```

If tunnel fails (for example ngrok outage), use one of these:

```bash
# Same network with phone/emulator
npx expo start --lan

# Browser testing only
npx expo start --web
```

## Other Useful Commands

```bash
cd frontend
npm run android
npm run ios
npm run web
npm run lint
```

## Notes

- Tunnel mode depends on ngrok availability.
- Backend should be running at http://localhost:8000 (or your configured backend URL).
