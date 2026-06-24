import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart'; // Để dùng kIsWeb
import 'dart:convert';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:file_picker/file_picker.dart';
import 'package:http/http.dart' as http;
import 'package:fetch_client/fetch_client.dart';

// Provide a Dio instance
final dioProvider = Provider((ref) {
  final dio = Dio(
    BaseOptions(
      // Nếu chạy trên Web -> gọi localhost. Nếu chạy trên Android ảo -> gọi 10.0.2.2
      baseUrl: kIsWeb ? 'http://localhost:8000' : 'http://10.0.2.2:8000',
      connectTimeout: const Duration(seconds: 30),
      receiveTimeout: const Duration(minutes: 5),
    ),
  );

  // Ghi log chi tiết mọi request/response gửi qua mạng (rất hữu ích khi debug file upload)
  dio.interceptors.add(
    LogInterceptor(
      request: true,
      requestHeader: true,
      requestBody:
          false, // Không in log dữ liệu thô của file để tránh rác màn hình
      responseHeader: true,
      responseBody: true,
      error: true,
      logPrint: (obj) => print('[DIO LOG] $obj'),
    ),
  );

  return dio;
});

final uploadRepositoryProvider = Provider((ref) {
  return UploadRepository(ref.watch(dioProvider));
});

class UploadRepository {
  final Dio _dio;

  UploadRepository(this._dio);

  Stream<Map<String, dynamic>> uploadPdfStream(PlatformFile file) async* {
    if (kIsWeb) {
      // Use fetch_client on Web for progressive SSE streaming
      final url = Uri.parse('http://localhost:8000/api/v1/upload/pdf');
      final request = http.MultipartRequest('POST', url);
      request.files.add(
        http.MultipartFile.fromBytes('file', file.bytes!, filename: file.name),
      );

      final fetchClient = FetchClient(mode: RequestMode.cors);
      final response = await fetchClient.send(request);

      String buffer = '';
      await for (final chunk in response.stream.transform(utf8.decoder)) {
        buffer += chunk;
        while (buffer.contains('\n\n')) {
          final index = buffer.indexOf('\n\n');
          final block = buffer.substring(0, index);
          buffer = buffer.substring(index + 2);

          final lines = block.split('\n');
          for (final line in lines) {
            if (line.startsWith('data: ')) {
              final jsonStr = line.substring(6);
              if (jsonStr.trim().isNotEmpty) {
                try {
                  yield jsonDecode(jsonStr) as Map<String, dynamic>;
                } catch (e) {
                  debugPrint('[SSE] JSON Decode Error: $e');
                  yield {'type': 'error', 'detail': 'Lỗi JSON: $e'};
                }
              }
            }
          }
        }
      }
    } else {
      // Use Dio on Mobile/Desktop
      MultipartFile multipartFile = await MultipartFile.fromFile(
        file.path!,
        filename: file.name,
      );

      final formData = FormData.fromMap({'file': multipartFile});

      final response = await _dio.post(
        '/api/v1/upload/pdf',
        data: formData,
        options: Options(responseType: ResponseType.stream),
      );

      final stream = response.data.stream;
      final byteStream = stream.map((bytes) {
        if (bytes is String) return utf8.encode(bytes);
        return bytes as List<int>;
      });

      String buffer = '';
      await for (final chunk in byteStream.transform(utf8.decoder)) {
        buffer += chunk;
        while (buffer.contains('\n\n')) {
          final index = buffer.indexOf('\n\n');
          final block = buffer.substring(0, index);
          buffer = buffer.substring(index + 2);

          final lines = block.split('\n');
          for (final line in lines) {
            if (line.startsWith('data: ')) {
              final jsonStr = line.substring(6);
              if (jsonStr.trim().isNotEmpty) {
                try {
                  yield jsonDecode(jsonStr) as Map<String, dynamic>;
                } catch (e) {
                  debugPrint('[SSE] JSON Decode Error: $e');
                  yield {'type': 'error', 'detail': 'Lỗi JSON: $e'};
                }
              }
            }
          }
        }
      }
    }
  }
}
