import 'dart:io';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../data/upload_repository.dart';

final uploadStateProvider = StateNotifierProvider<UploadNotifier, AsyncValue<Map<String, dynamic>?>>((ref) {
  return UploadNotifier(ref.watch(uploadRepositoryProvider));
});

class UploadNotifier extends StateNotifier<AsyncValue<Map<String, dynamic>?>> {
  final UploadRepository _repository;

  UploadNotifier(this._repository) : super(const AsyncData(null));

  Future<void> uploadFile(File file) async {
    state = const AsyncLoading();
    try {
      final result = await _repository.uploadPdf(file);
      state = AsyncData(result);
    } catch (e, stack) {
      state = AsyncError(e, stack);
    }
  }
}
