import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:file_picker/file_picker.dart';
import 'upload_state.dart';

class UploadScreen extends ConsumerWidget {
  const UploadScreen({super.key});

  Future<void> _pickAndUploadFile(WidgetRef ref) async {
    FilePickerResult? result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['pdf'],
      withData: true, // Quan trọng: Bắt buộc lấy dữ liệu dạng byte khi chạy trên Web
    );

    if (result != null) {
      PlatformFile file = result.files.single;
      ref.read(uploadStateProvider.notifier).uploadFile(file);
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final uploadState = ref.watch(uploadStateProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Nales-It - AI Quiz', style: TextStyle(fontWeight: FontWeight.bold)),
        centerTitle: true,
        elevation: 0,
      ),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.auto_awesome, size: 80, color: Colors.deepPurple),
              const SizedBox(height: 24),
              const Text(
                'Biến đề thi PDF thành\nTrắc nghiệm thông minh',
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 40),
              
              uploadState.when(
                data: (data) {
                  if (data != null) {
                    return Column(
                      children: [
                        const Icon(Icons.check_circle, color: Colors.green, size: 60),
                        const SizedBox(height: 16),
                        Text(
                          'Đã tạo thành công:\n${data["title"] ?? "Bài Quiz mới"}', 
                          textAlign: TextAlign.center,
                          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)
                        ),
                        const SizedBox(height: 24),
                        ElevatedButton.icon(
                          style: ElevatedButton.styleFrom(
                            padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
                            backgroundColor: Colors.deepPurple,
                            foregroundColor: Colors.white,
                          ),
                          onPressed: () {
                            // TODO: Điều hướng sang màn hình Quiz
                            ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(content: Text('Tính năng đang phát triển...'))
                            );
                          },
                          icon: const Icon(Icons.play_arrow),
                          label: const Text('Làm bài ngay', style: TextStyle(fontSize: 18)),
                        )
                      ],
                    );
                  }
                  
                  return ElevatedButton.icon(
                    style: ElevatedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
                      textStyle: const TextStyle(fontSize: 18),
                      backgroundColor: Colors.deepPurple,
                      foregroundColor: Colors.white,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                    ),
                    onPressed: () => _pickAndUploadFile(ref),
                    icon: const Icon(Icons.upload_file, size: 28),
                    label: const Text('Tải file PDF lên'),
                  );
                },
                loading: () => const Column(
                  children: [
                    CircularProgressIndicator(color: Colors.deepPurple),
                    SizedBox(height: 24),
                    Text(
                      'AI đang đọc và tạo đề thi...\nQuá trình này có thể mất vài chục giây.',
                      textAlign: TextAlign.center,
                      style: TextStyle(color: Colors.grey, fontSize: 16),
                    ),
                  ],
                ),
                error: (error, stack) => Column(
                  children: [
                    const Icon(Icons.error_outline, color: Colors.red, size: 60),
                    const SizedBox(height: 16),
                    Text(
                      'Lỗi xử lý file:\n$error', 
                      textAlign: TextAlign.center, 
                      style: const TextStyle(color: Colors.red)
                    ),
                    const SizedBox(height: 24),
                    OutlinedButton.icon(
                      onPressed: () => _pickAndUploadFile(ref),
                      icon: const Icon(Icons.refresh),
                      label: const Text('Thử lại file khác'),
                    )
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
