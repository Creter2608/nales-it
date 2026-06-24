/// Centralized application configuration.
///
/// Values are injected at compile time via `--dart-define`:
/// ```bash
/// flutter run --dart-define=API_BASE_URL=https://api.nales-it.com \
///             --dart-define=API_KEY=your_secret_key
/// ```
class AppConfig {
  AppConfig._();

  /// Base URL for the backend API.
  /// Defaults to localhost for development.
  static const String apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://localhost:8000',
  );

  /// API key for `X-API-Key` authentication header.
  /// Empty string means no key is sent (dev mode).
  static const String apiKey = String.fromEnvironment('API_KEY');

  /// Connection timeout for HTTP requests.
  static const Duration connectTimeout = Duration(seconds: 30);

  /// Receive timeout for HTTP requests (long for SSE streaming).
  static const Duration receiveTimeout = Duration(minutes: 5);
}
