import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class UploadScreen extends ConsumerWidget {
  const UploadScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Nales-It - Upload Exam'),
      ),
      body: Center(
        child: ElevatedButton.icon(
          onPressed: () {
            // TODO: Implement file upload
          },
          icon: const Icon(Icons.upload_file),
          label: const Text('Upload PDF/Word'),
        ),
      ),
    );
  }
}
