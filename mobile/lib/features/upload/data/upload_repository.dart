import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart'; // Để dùng kIsWeb
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:file_picker/file_picker.dart';

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

  Future<Map<String, dynamic>> uploadPdf(PlatformFile file) async {
    MultipartFile multipartFile;

    if (kIsWeb) {
      // Trên Web, không có đường dẫn vật lý (path null), bắt buộc lấy file từ bytes bộ nhớ
      multipartFile = MultipartFile.fromBytes(file.bytes!, filename: file.name);
    } else {
      // Trên Mobile/Desktop, lấy theo đường dẫn
      multipartFile = await MultipartFile.fromFile(
        file.path!,
        filename: file.name,
      );
    }

    final formData = FormData.fromMap({'file': multipartFile});

    final response = await _dio.post('/api/v1/upload/pdf', data: formData);
    return response.data;
  }
}
