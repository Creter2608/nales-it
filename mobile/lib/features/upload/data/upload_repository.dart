import 'dart:io';
import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

// Provide a Dio instance
final dioProvider = Provider((ref) => Dio(BaseOptions(
  // 10.0.2.2 là localhost từ máy ảo Android Emulator
  baseUrl: 'http://10.0.2.2:8000', 
  connectTimeout: const Duration(seconds: 30),
  receiveTimeout: const Duration(seconds: 120), // Quá trình AI xử lý có thể mất nhiều thời gian
)));

final uploadRepositoryProvider = Provider((ref) {
  return UploadRepository(ref.watch(dioProvider));
});

class UploadRepository {
  final Dio _dio;
  
  UploadRepository(this._dio);

  Future<Map<String, dynamic>> uploadPdf(File file) async {
    final formData = FormData.fromMap({
      'file': await MultipartFile.fromFile(file.path, filename: file.path.split('/').last),
    });

    final response = await _dio.post('/api/v1/upload/pdf', data: formData);
    return response.data;
  }
}
