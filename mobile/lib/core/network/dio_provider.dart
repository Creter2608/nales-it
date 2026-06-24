import 'dart:async';

import 'package:dio/dio.dart';
import 'package:sentry_flutter/sentry_flutter.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../config/app_config.dart';

/// Methods considered safe to retry (idempotent operations).
const _retryableMethods = {'GET', 'HEAD', 'OPTIONS', 'PUT', 'DELETE'};

/// Maximum number of retry attempts before giving up.
const _maxRetries = 3;

/// Interceptor that retries failed requests with exponential backoff.
///
/// Only retries idempotent methods (GET, HEAD, OPTIONS, PUT, DELETE) on:
/// - Connection timeouts
/// - Receive timeouts
/// - 5xx server errors
///
/// Backoff sequence: 1s → 2s → 4s.
class _RetryInterceptor extends Interceptor {
  _RetryInterceptor(this._dio);

  final Dio _dio;

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) async {
    final method = err.requestOptions.method.toUpperCase();

    if (!_retryableMethods.contains(method)) {
      return handler.next(err);
    }

    if (!_shouldRetry(err)) {
      return handler.next(err);
    }

    final attempt = (err.requestOptions.extra['_retryCount'] as int?) ?? 0;
    if (attempt >= _maxRetries) {
      Sentry.captureException(
        err,
        stackTrace: err.stackTrace,
        withScope: (scope) {
          scope.setTag('method', method);
          scope.setTag('path', err.requestOptions.path);
        },
      );
      return handler.next(err);
    }

    final nextAttempt = attempt + 1;
    final delay = Duration(seconds: 1 << attempt); // 1s, 2s, 4s

    debugPrint(
      '[DIO Retry] $method ${err.requestOptions.path} — '
      'attempt $nextAttempt/$_maxRetries after ${delay.inSeconds}s '
      '(${err.type.name})',
    );

    await Future<void>.delayed(delay);

    err.requestOptions.extra['_retryCount'] = nextAttempt;

    try {
      final response = await _dio.fetch(err.requestOptions);
      handler.resolve(response);
    } on DioException catch (e) {
      handler.next(e);
    }
  }

  bool _shouldRetry(DioException err) {
    // Retry on connection & receive timeouts.
    if (err.type == DioExceptionType.connectionTimeout ||
        err.type == DioExceptionType.receiveTimeout) {
      return true;
    }

    // Retry on 5xx server errors.
    final statusCode = err.response?.statusCode;
    if (statusCode != null && statusCode >= 500) {
      return true;
    }

    return false;
  }
}

/// Global Dio instance provider.
///
/// Configured with:
/// - Base URL from [AppConfig.apiBaseUrl]
/// - `X-API-Key` header from [AppConfig.apiKey] (if set)
/// - Retry interceptor for transient failures
/// - Debug-only request/response logging
final dioProvider = Provider<Dio>((ref) {
  final dio = Dio(
    BaseOptions(
      baseUrl: AppConfig.apiBaseUrl,
      connectTimeout: AppConfig.connectTimeout,
      receiveTimeout: AppConfig.receiveTimeout,
      headers: {
        if (AppConfig.apiKey.isNotEmpty) 'X-API-Key': AppConfig.apiKey,
      },
    ),
  );

  // Retry interceptor — added before logging so retries are visible in logs.
  dio.interceptors.add(_RetryInterceptor(dio));

  // Only log in debug mode to avoid leaking data in production.
  if (kDebugMode) {
    dio.interceptors.add(
      LogInterceptor(
        request: true,
        requestHeader: true,
        requestBody: false,
        responseHeader: true,
        responseBody: true,
        error: true,
        logPrint: (obj) => debugPrint('[DIO] $obj'),
      ),
    );
  }

  return dio;
});
