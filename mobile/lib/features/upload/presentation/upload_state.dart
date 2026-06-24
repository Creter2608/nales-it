import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Upload state provider.
///
/// Tracks whether an upload flow is currently in progress.
/// The actual streaming logic lives in [UploadScreen._pickAndUploadFile].
final uploadStateProvider =
    StateNotifierProvider.autoDispose<UploadNotifier, AsyncValue<Map<String, dynamic>?>>((ref) {
  return UploadNotifier();
});

class UploadNotifier extends StateNotifier<AsyncValue<Map<String, dynamic>?>> {
  UploadNotifier() : super(const AsyncData(null));

  /// Signal that an upload has started.
  void setLoading() => state = const AsyncLoading();

  /// Signal that an upload has completed with a result.
  void setResult(Map<String, dynamic>? data) => state = AsyncData(data);

  /// Signal that an upload has failed.
  void setError(Object error, StackTrace stack) => state = AsyncError(error, stack);

  /// Reset back to initial idle state.
  void reset() => state = const AsyncData(null);
}
