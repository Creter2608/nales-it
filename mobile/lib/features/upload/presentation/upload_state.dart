import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:file_picker/file_picker.dart';
import '../data/upload_repository.dart';

final uploadStateProvider = StateNotifierProvider.autoDispose<UploadNotifier, AsyncValue<Map<String, dynamic>?>>((ref) {
  return UploadNotifier(ref.watch(uploadRepositoryProvider));
});

class UploadNotifier extends StateNotifier<AsyncValue<Map<String, dynamic>?>> {
  final UploadRepository _repository;

  UploadNotifier(this._repository) : super(const AsyncData(null));

  Future<void> uploadFile(PlatformFile file) async {
    state = const AsyncLoading();
    try {
      // Not used anymore as we stream directly in UploadScreen, but keeping for compile
      final stream = _repository.uploadPdfStream(file);
      state = AsyncData(null);
    } catch (e, stack) {
      state = AsyncError(e, stack);
    }
  }
}
