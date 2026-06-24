import 'package:dio/dio.dart';
import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:file_picker/file_picker.dart';
import '../../../core/network/dio_provider.dart';

final uploadRepositoryProvider = Provider((ref) {
  return UploadRepository(ref.watch(dioProvider));
});

class UploadRepository {
  final Dio _dio;

  UploadRepository(this._dio);

  /// Uploads a PDF file and returns a stream of SSE events.
  ///
  /// Each event is a JSON map with a `type` field indicating the event kind:
  /// `chunk`, `progress`, `images_mapped`, `answers_solved`, `done`, or `error`.
  Stream<Map<String, dynamic>> uploadPdfStream(PlatformFile file) async* {
    MultipartFile multipartFile;

    if (kIsWeb) {
      multipartFile = MultipartFile.fromBytes(file.bytes!, filename: file.name);
    } else {
      multipartFile = await MultipartFile.fromFile(
        file.path!,
        filename: file.name,
      );
    }

    final formData = FormData.fromMap({'file': multipartFile});

    final response = await _dio.post(
      '/api/v1/upload/pdf',
      data: formData,
      options: Options(responseType: ResponseType.stream),
    );

    final stream = response.data.stream;
    String buffer = '';

    await for (final bytes in stream) {
      final chunk = utf8.decode(bytes as List<int>, allowMalformed: true);
      buffer += chunk;

      while (buffer.contains('\n\n')) {
        final index = buffer.indexOf('\n\n');
        final block = buffer.substring(0, index);
        buffer = buffer.substring(index + 2);

        final lines = block.split('\n');
        for (final line in lines) {
          if (line.startsWith('data: ')) {
            final jsonStr = line.substring(6).trim();
            if (jsonStr.isEmpty) continue;
            try {
              yield jsonDecode(jsonStr) as Map<String, dynamic>;
            } on FormatException catch (e) {
              debugPrint('[SSE] Malformed JSON skipped: $e');
              yield {'type': 'error', 'detail': 'Malformed SSE data: $e'};
            }
          }
        }
      }
    }
  }
}
