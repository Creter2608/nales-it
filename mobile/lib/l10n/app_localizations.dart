import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:intl/intl.dart' as intl;

import 'app_localizations_en.dart';
import 'app_localizations_vi.dart';

// ignore_for_file: type=lint

/// Callers can lookup localized strings with an instance of AppLocalizations
/// returned by `AppLocalizations.of(context)`.
///
/// Applications need to include `AppLocalizations.delegate()` in their app's
/// `localizationDelegates` list, and the locales they support in the app's
/// `supportedLocales` list. For example:
///
/// ```dart
/// import 'l10n/app_localizations.dart';
///
/// return MaterialApp(
///   localizationsDelegates: AppLocalizations.localizationsDelegates,
///   supportedLocales: AppLocalizations.supportedLocales,
///   home: MyApplicationHome(),
/// );
/// ```
///
/// ## Update pubspec.yaml
///
/// Please make sure to update your pubspec.yaml to include the following
/// packages:
///
/// ```yaml
/// dependencies:
///   # Internationalization support.
///   flutter_localizations:
///     sdk: flutter
///   intl: any # Use the pinned version from flutter_localizations
///
///   # Rest of dependencies
/// ```
///
/// ## iOS Applications
///
/// iOS applications define key application metadata, including supported
/// locales, in an Info.plist file that is built into the application bundle.
/// To configure the locales supported by your app, you’ll need to edit this
/// file.
///
/// First, open your project’s ios/Runner.xcworkspace Xcode workspace file.
/// Then, in the Project Navigator, open the Info.plist file under the Runner
/// project’s Runner folder.
///
/// Next, select the Information Property List item, select Add Item from the
/// Editor menu, then select Localizations from the pop-up menu.
///
/// Select and expand the newly-created Localizations item then, for each
/// locale your application supports, add a new item and select the locale
/// you wish to add from the pop-up menu in the Value field. This list should
/// be consistent with the languages listed in the AppLocalizations.supportedLocales
/// property.
abstract class AppLocalizations {
  AppLocalizations(String locale)
    : localeName = intl.Intl.canonicalizedLocale(locale.toString());

  final String localeName;

  static AppLocalizations? of(BuildContext context) {
    return Localizations.of<AppLocalizations>(context, AppLocalizations);
  }

  static const LocalizationsDelegate<AppLocalizations> delegate =
      _AppLocalizationsDelegate();

  /// A list of this localizations delegate along with the default localizations
  /// delegates.
  ///
  /// Returns a list of localizations delegates containing this delegate along with
  /// GlobalMaterialLocalizations.delegate, GlobalCupertinoLocalizations.delegate,
  /// and GlobalWidgetsLocalizations.delegate.
  ///
  /// Additional delegates can be added by appending to this list in
  /// MaterialApp. This list does not have to be used at all if a custom list
  /// of delegates is preferred or required.
  static const List<LocalizationsDelegate<dynamic>> localizationsDelegates =
      <LocalizationsDelegate<dynamic>>[
        delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
      ];

  /// A list of this localizations delegate's supported locales.
  static const List<Locale> supportedLocales = <Locale>[
    Locale('en'),
    Locale('vi'),
  ];

  /// No description provided for @appTitle.
  ///
  /// In vi, this message translates to:
  /// **'Nales-It Gia Sư AI'**
  String get appTitle;

  /// No description provided for @modeSelectionTitle.
  ///
  /// In vi, this message translates to:
  /// **'Chọn Chế Độ Làm Bài'**
  String get modeSelectionTitle;

  /// No description provided for @modeInstant.
  ///
  /// In vi, this message translates to:
  /// **'Ôn luyện'**
  String get modeInstant;

  /// No description provided for @modeInstantDesc.
  ///
  /// In vi, this message translates to:
  /// **'Báo màu xanh đỏ ngay khi chọn.'**
  String get modeInstantDesc;

  /// No description provided for @modeExam.
  ///
  /// In vi, this message translates to:
  /// **'Thi thử'**
  String get modeExam;

  /// No description provided for @modeExamDesc.
  ///
  /// In vi, this message translates to:
  /// **'Chấm điểm ở cuối giờ.'**
  String get modeExamDesc;

  /// No description provided for @modeAi.
  ///
  /// In vi, this message translates to:
  /// **'Đánh giá AI'**
  String get modeAi;

  /// No description provided for @modeAiDesc.
  ///
  /// In vi, this message translates to:
  /// **'AI nhận xét tổng quan kỹ năng của bạn.'**
  String get modeAiDesc;

  /// No description provided for @modePractice.
  ///
  /// In vi, this message translates to:
  /// **'Tự do'**
  String get modePractice;

  /// No description provided for @modePracticeDesc.
  ///
  /// In vi, this message translates to:
  /// **'Không chấm điểm, chỉ đọc câu hỏi.'**
  String get modePracticeDesc;

  /// No description provided for @questionGridTitle.
  ///
  /// In vi, this message translates to:
  /// **'Bảng câu hỏi'**
  String get questionGridTitle;

  /// No description provided for @resolveDialogTitle.
  ///
  /// In vi, this message translates to:
  /// **'Yêu cầu giải lại?'**
  String get resolveDialogTitle;

  /// No description provided for @resolveDialogDesc.
  ///
  /// In vi, this message translates to:
  /// **'Bạn thấy cấn cấn? Yêu cầu Gia sư AI kiểm tra và giải lại câu này?'**
  String get resolveDialogDesc;

  /// No description provided for @cancel.
  ///
  /// In vi, this message translates to:
  /// **'Hủy'**
  String get cancel;

  /// No description provided for @resolve.
  ///
  /// In vi, this message translates to:
  /// **'Giải lại'**
  String get resolve;

  /// No description provided for @resolvingMsg.
  ///
  /// In vi, this message translates to:
  /// **'Đang yêu cầu AI giải lại...'**
  String get resolvingMsg;

  /// No description provided for @resolvedMsg.
  ///
  /// In vi, this message translates to:
  /// **'Đã cập nhật lời giải mới!'**
  String get resolvedMsg;

  /// No description provided for @resolveErrorMsg.
  ///
  /// In vi, this message translates to:
  /// **'Lỗi: Không thể giải lại lúc này.'**
  String get resolveErrorMsg;
}

class _AppLocalizationsDelegate
    extends LocalizationsDelegate<AppLocalizations> {
  const _AppLocalizationsDelegate();

  @override
  Future<AppLocalizations> load(Locale locale) {
    return SynchronousFuture<AppLocalizations>(lookupAppLocalizations(locale));
  }

  @override
  bool isSupported(Locale locale) =>
      <String>['en', 'vi'].contains(locale.languageCode);

  @override
  bool shouldReload(_AppLocalizationsDelegate old) => false;
}

AppLocalizations lookupAppLocalizations(Locale locale) {
  // Lookup logic when only language code is specified.
  switch (locale.languageCode) {
    case 'en':
      return AppLocalizationsEn();
    case 'vi':
      return AppLocalizationsVi();
  }

  throw FlutterError(
    'AppLocalizations.delegate failed to load unsupported locale "$locale". This is likely '
    'an issue with the localizations generation tool. Please file an issue '
    'on GitHub with a reproducible sample app and the gen-l10n configuration '
    'that was used.',
  );
}
