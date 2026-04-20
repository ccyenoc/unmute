// https://docs.expo.dev/guides/using-eslint/
const path = require('path');
const expoConfig = require(path.join(__dirname, 'frontend/node_modules/eslint-config-expo/flat'));

module.exports = [
  ...expoConfig,
  {
    ignores: ['dist/*'],
  },
];
