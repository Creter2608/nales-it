import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:flutter_math_fork/flutter_math.dart';

/// Custom Markdown builder that renders LaTeX math expressions.
class MathMarkdownBuilder extends MarkdownElementBuilder {
  @override
  Widget visitElementAfter(element, TextStyle? preferredStyle) {
    if (element.textContent.isEmpty) return const SizedBox();
    return Math.tex(
      element.textContent,
      textStyle: preferredStyle?.copyWith(fontSize: 18),
      mathStyle: MathStyle.display,
    );
  }
}
