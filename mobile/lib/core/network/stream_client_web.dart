import 'package:http/http.dart' as http;
import 'package:fetch_client/fetch_client.dart';

http.Client createStreamClient() => FetchClient(mode: RequestMode.cors);
