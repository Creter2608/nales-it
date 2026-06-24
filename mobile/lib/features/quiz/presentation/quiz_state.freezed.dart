// GENERATED CODE - DO NOT MODIFY BY HAND
// coverage:ignore-file
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'quiz_state.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

// dart format off
T _$identity<T>(T value) => value;
/// @nodoc
mixin _$QuizState {

 AsyncValue<Quiz?> get quiz; QuizMode get mode; int get currentQuestionIndex; Map<String, String> get userAnswers; bool get isSubmitted; AsyncValue<Map<String, dynamic>?> get gradeResult; bool get isStreaming; String? get progressMessage; Set<String> get viewingAnswers; Set<String> get loadingAnswers;
/// Create a copy of QuizState
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$QuizStateCopyWith<QuizState> get copyWith => _$QuizStateCopyWithImpl<QuizState>(this as QuizState, _$identity);



@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is QuizState&&(identical(other.quiz, quiz) || other.quiz == quiz)&&(identical(other.mode, mode) || other.mode == mode)&&(identical(other.currentQuestionIndex, currentQuestionIndex) || other.currentQuestionIndex == currentQuestionIndex)&&const DeepCollectionEquality().equals(other.userAnswers, userAnswers)&&(identical(other.isSubmitted, isSubmitted) || other.isSubmitted == isSubmitted)&&(identical(other.gradeResult, gradeResult) || other.gradeResult == gradeResult)&&(identical(other.isStreaming, isStreaming) || other.isStreaming == isStreaming)&&(identical(other.progressMessage, progressMessage) || other.progressMessage == progressMessage)&&const DeepCollectionEquality().equals(other.viewingAnswers, viewingAnswers)&&const DeepCollectionEquality().equals(other.loadingAnswers, loadingAnswers));
}


@override
int get hashCode => Object.hash(runtimeType,quiz,mode,currentQuestionIndex,const DeepCollectionEquality().hash(userAnswers),isSubmitted,gradeResult,isStreaming,progressMessage,const DeepCollectionEquality().hash(viewingAnswers),const DeepCollectionEquality().hash(loadingAnswers));

@override
String toString() {
  return 'QuizState(quiz: $quiz, mode: $mode, currentQuestionIndex: $currentQuestionIndex, userAnswers: $userAnswers, isSubmitted: $isSubmitted, gradeResult: $gradeResult, isStreaming: $isStreaming, progressMessage: $progressMessage, viewingAnswers: $viewingAnswers, loadingAnswers: $loadingAnswers)';
}


}

/// @nodoc
abstract mixin class $QuizStateCopyWith<$Res>  {
  factory $QuizStateCopyWith(QuizState value, $Res Function(QuizState) _then) = _$QuizStateCopyWithImpl;
@useResult
$Res call({
 AsyncValue<Quiz?> quiz, QuizMode mode, int currentQuestionIndex, Map<String, String> userAnswers, bool isSubmitted, AsyncValue<Map<String, dynamic>?> gradeResult, bool isStreaming, String? progressMessage, Set<String> viewingAnswers, Set<String> loadingAnswers
});




}
/// @nodoc
class _$QuizStateCopyWithImpl<$Res>
    implements $QuizStateCopyWith<$Res> {
  _$QuizStateCopyWithImpl(this._self, this._then);

  final QuizState _self;
  final $Res Function(QuizState) _then;

/// Create a copy of QuizState
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? quiz = null,Object? mode = null,Object? currentQuestionIndex = null,Object? userAnswers = null,Object? isSubmitted = null,Object? gradeResult = null,Object? isStreaming = null,Object? progressMessage = freezed,Object? viewingAnswers = null,Object? loadingAnswers = null,}) {
  return _then(_self.copyWith(
quiz: null == quiz ? _self.quiz : quiz // ignore: cast_nullable_to_non_nullable
as AsyncValue<Quiz?>,mode: null == mode ? _self.mode : mode // ignore: cast_nullable_to_non_nullable
as QuizMode,currentQuestionIndex: null == currentQuestionIndex ? _self.currentQuestionIndex : currentQuestionIndex // ignore: cast_nullable_to_non_nullable
as int,userAnswers: null == userAnswers ? _self.userAnswers : userAnswers // ignore: cast_nullable_to_non_nullable
as Map<String, String>,isSubmitted: null == isSubmitted ? _self.isSubmitted : isSubmitted // ignore: cast_nullable_to_non_nullable
as bool,gradeResult: null == gradeResult ? _self.gradeResult : gradeResult // ignore: cast_nullable_to_non_nullable
as AsyncValue<Map<String, dynamic>?>,isStreaming: null == isStreaming ? _self.isStreaming : isStreaming // ignore: cast_nullable_to_non_nullable
as bool,progressMessage: freezed == progressMessage ? _self.progressMessage : progressMessage // ignore: cast_nullable_to_non_nullable
as String?,viewingAnswers: null == viewingAnswers ? _self.viewingAnswers : viewingAnswers // ignore: cast_nullable_to_non_nullable
as Set<String>,loadingAnswers: null == loadingAnswers ? _self.loadingAnswers : loadingAnswers // ignore: cast_nullable_to_non_nullable
as Set<String>,
  ));
}

}


/// Adds pattern-matching-related methods to [QuizState].
extension QuizStatePatterns on QuizState {
/// A variant of `map` that fallback to returning `orElse`.
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case final Subclass value:
///     return ...;
///   case _:
///     return orElse();
/// }
/// ```

@optionalTypeArgs TResult maybeMap<TResult extends Object?>(TResult Function( _QuizState value)?  $default,{required TResult orElse(),}){
final _that = this;
switch (_that) {
case _QuizState() when $default != null:
return $default(_that);case _:
  return orElse();

}
}
/// A `switch`-like method, using callbacks.
///
/// Callbacks receives the raw object, upcasted.
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case final Subclass value:
///     return ...;
///   case final Subclass2 value:
///     return ...;
/// }
/// ```

@optionalTypeArgs TResult map<TResult extends Object?>(TResult Function( _QuizState value)  $default,){
final _that = this;
switch (_that) {
case _QuizState():
return $default(_that);case _:
  throw StateError('Unexpected subclass');

}
}
/// A variant of `map` that fallback to returning `null`.
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case final Subclass value:
///     return ...;
///   case _:
///     return null;
/// }
/// ```

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>(TResult? Function( _QuizState value)?  $default,){
final _that = this;
switch (_that) {
case _QuizState() when $default != null:
return $default(_that);case _:
  return null;

}
}
/// A variant of `when` that fallback to an `orElse` callback.
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case Subclass(:final field):
///     return ...;
///   case _:
///     return orElse();
/// }
/// ```

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>(TResult Function( AsyncValue<Quiz?> quiz,  QuizMode mode,  int currentQuestionIndex,  Map<String, String> userAnswers,  bool isSubmitted,  AsyncValue<Map<String, dynamic>?> gradeResult,  bool isStreaming,  String? progressMessage,  Set<String> viewingAnswers,  Set<String> loadingAnswers)?  $default,{required TResult orElse(),}) {final _that = this;
switch (_that) {
case _QuizState() when $default != null:
return $default(_that.quiz,_that.mode,_that.currentQuestionIndex,_that.userAnswers,_that.isSubmitted,_that.gradeResult,_that.isStreaming,_that.progressMessage,_that.viewingAnswers,_that.loadingAnswers);case _:
  return orElse();

}
}
/// A `switch`-like method, using callbacks.
///
/// As opposed to `map`, this offers destructuring.
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case Subclass(:final field):
///     return ...;
///   case Subclass2(:final field2):
///     return ...;
/// }
/// ```

@optionalTypeArgs TResult when<TResult extends Object?>(TResult Function( AsyncValue<Quiz?> quiz,  QuizMode mode,  int currentQuestionIndex,  Map<String, String> userAnswers,  bool isSubmitted,  AsyncValue<Map<String, dynamic>?> gradeResult,  bool isStreaming,  String? progressMessage,  Set<String> viewingAnswers,  Set<String> loadingAnswers)  $default,) {final _that = this;
switch (_that) {
case _QuizState():
return $default(_that.quiz,_that.mode,_that.currentQuestionIndex,_that.userAnswers,_that.isSubmitted,_that.gradeResult,_that.isStreaming,_that.progressMessage,_that.viewingAnswers,_that.loadingAnswers);case _:
  throw StateError('Unexpected subclass');

}
}
/// A variant of `when` that fallback to returning `null`
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case Subclass(:final field):
///     return ...;
///   case _:
///     return null;
/// }
/// ```

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>(TResult? Function( AsyncValue<Quiz?> quiz,  QuizMode mode,  int currentQuestionIndex,  Map<String, String> userAnswers,  bool isSubmitted,  AsyncValue<Map<String, dynamic>?> gradeResult,  bool isStreaming,  String? progressMessage,  Set<String> viewingAnswers,  Set<String> loadingAnswers)?  $default,) {final _that = this;
switch (_that) {
case _QuizState() when $default != null:
return $default(_that.quiz,_that.mode,_that.currentQuestionIndex,_that.userAnswers,_that.isSubmitted,_that.gradeResult,_that.isStreaming,_that.progressMessage,_that.viewingAnswers,_that.loadingAnswers);case _:
  return null;

}
}

}

/// @nodoc


class _QuizState implements QuizState {
  const _QuizState({this.quiz = const AsyncLoading(), this.mode = QuizMode.instantFeedback, this.currentQuestionIndex = 0, final  Map<String, String> userAnswers = const {}, this.isSubmitted = false, this.gradeResult = const AsyncData(null), this.isStreaming = false, this.progressMessage, final  Set<String> viewingAnswers = const {}, final  Set<String> loadingAnswers = const {}}): _userAnswers = userAnswers,_viewingAnswers = viewingAnswers,_loadingAnswers = loadingAnswers;
  

@override@JsonKey() final  AsyncValue<Quiz?> quiz;
@override@JsonKey() final  QuizMode mode;
@override@JsonKey() final  int currentQuestionIndex;
 final  Map<String, String> _userAnswers;
@override@JsonKey() Map<String, String> get userAnswers {
  if (_userAnswers is EqualUnmodifiableMapView) return _userAnswers;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableMapView(_userAnswers);
}

@override@JsonKey() final  bool isSubmitted;
@override@JsonKey() final  AsyncValue<Map<String, dynamic>?> gradeResult;
@override@JsonKey() final  bool isStreaming;
@override final  String? progressMessage;
 final  Set<String> _viewingAnswers;
@override@JsonKey() Set<String> get viewingAnswers {
  if (_viewingAnswers is EqualUnmodifiableSetView) return _viewingAnswers;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableSetView(_viewingAnswers);
}

 final  Set<String> _loadingAnswers;
@override@JsonKey() Set<String> get loadingAnswers {
  if (_loadingAnswers is EqualUnmodifiableSetView) return _loadingAnswers;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableSetView(_loadingAnswers);
}


/// Create a copy of QuizState
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$QuizStateCopyWith<_QuizState> get copyWith => __$QuizStateCopyWithImpl<_QuizState>(this, _$identity);



@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _QuizState&&(identical(other.quiz, quiz) || other.quiz == quiz)&&(identical(other.mode, mode) || other.mode == mode)&&(identical(other.currentQuestionIndex, currentQuestionIndex) || other.currentQuestionIndex == currentQuestionIndex)&&const DeepCollectionEquality().equals(other._userAnswers, _userAnswers)&&(identical(other.isSubmitted, isSubmitted) || other.isSubmitted == isSubmitted)&&(identical(other.gradeResult, gradeResult) || other.gradeResult == gradeResult)&&(identical(other.isStreaming, isStreaming) || other.isStreaming == isStreaming)&&(identical(other.progressMessage, progressMessage) || other.progressMessage == progressMessage)&&const DeepCollectionEquality().equals(other._viewingAnswers, _viewingAnswers)&&const DeepCollectionEquality().equals(other._loadingAnswers, _loadingAnswers));
}


@override
int get hashCode => Object.hash(runtimeType,quiz,mode,currentQuestionIndex,const DeepCollectionEquality().hash(_userAnswers),isSubmitted,gradeResult,isStreaming,progressMessage,const DeepCollectionEquality().hash(_viewingAnswers),const DeepCollectionEquality().hash(_loadingAnswers));

@override
String toString() {
  return 'QuizState(quiz: $quiz, mode: $mode, currentQuestionIndex: $currentQuestionIndex, userAnswers: $userAnswers, isSubmitted: $isSubmitted, gradeResult: $gradeResult, isStreaming: $isStreaming, progressMessage: $progressMessage, viewingAnswers: $viewingAnswers, loadingAnswers: $loadingAnswers)';
}


}

/// @nodoc
abstract mixin class _$QuizStateCopyWith<$Res> implements $QuizStateCopyWith<$Res> {
  factory _$QuizStateCopyWith(_QuizState value, $Res Function(_QuizState) _then) = __$QuizStateCopyWithImpl;
@override @useResult
$Res call({
 AsyncValue<Quiz?> quiz, QuizMode mode, int currentQuestionIndex, Map<String, String> userAnswers, bool isSubmitted, AsyncValue<Map<String, dynamic>?> gradeResult, bool isStreaming, String? progressMessage, Set<String> viewingAnswers, Set<String> loadingAnswers
});




}
/// @nodoc
class __$QuizStateCopyWithImpl<$Res>
    implements _$QuizStateCopyWith<$Res> {
  __$QuizStateCopyWithImpl(this._self, this._then);

  final _QuizState _self;
  final $Res Function(_QuizState) _then;

/// Create a copy of QuizState
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? quiz = null,Object? mode = null,Object? currentQuestionIndex = null,Object? userAnswers = null,Object? isSubmitted = null,Object? gradeResult = null,Object? isStreaming = null,Object? progressMessage = freezed,Object? viewingAnswers = null,Object? loadingAnswers = null,}) {
  return _then(_QuizState(
quiz: null == quiz ? _self.quiz : quiz // ignore: cast_nullable_to_non_nullable
as AsyncValue<Quiz?>,mode: null == mode ? _self.mode : mode // ignore: cast_nullable_to_non_nullable
as QuizMode,currentQuestionIndex: null == currentQuestionIndex ? _self.currentQuestionIndex : currentQuestionIndex // ignore: cast_nullable_to_non_nullable
as int,userAnswers: null == userAnswers ? _self._userAnswers : userAnswers // ignore: cast_nullable_to_non_nullable
as Map<String, String>,isSubmitted: null == isSubmitted ? _self.isSubmitted : isSubmitted // ignore: cast_nullable_to_non_nullable
as bool,gradeResult: null == gradeResult ? _self.gradeResult : gradeResult // ignore: cast_nullable_to_non_nullable
as AsyncValue<Map<String, dynamic>?>,isStreaming: null == isStreaming ? _self.isStreaming : isStreaming // ignore: cast_nullable_to_non_nullable
as bool,progressMessage: freezed == progressMessage ? _self.progressMessage : progressMessage // ignore: cast_nullable_to_non_nullable
as String?,viewingAnswers: null == viewingAnswers ? _self._viewingAnswers : viewingAnswers // ignore: cast_nullable_to_non_nullable
as Set<String>,loadingAnswers: null == loadingAnswers ? _self._loadingAnswers : loadingAnswers // ignore: cast_nullable_to_non_nullable
as Set<String>,
  ));
}


}

// dart format on
