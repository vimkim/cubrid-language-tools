// CUBRID private headers are confined to this serial, parse-only process.
#include "config.h"
#include "parser.h"
#include "error_manager.h"
#include "language_support.h"
#include "message_catalog.h"
#include "system_parameter.h"
#include "release_string.h"
#include "qualification.hpp"
#include <rapidjson/document.h>
#include <rapidjson/writer.h>
#include <rapidjson/stringbuffer.h>
#include <openssl/sha.h>
#include <dlfcn.h>
#include <sys/resource.h>
#include <unistd.h>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include "coverage/registry.hpp"

using Json = rapidjson::Document;
using Value = rapidjson::Value;
using Alloc = rapidjson::Document::AllocatorType;
struct InputFailure : std::runtime_error { using std::runtime_error::runtime_error; };
static Value str(const std::string &s, Alloc &a) { return Value(s.data(), s.size(), a); }
static std::string read(const std::string &path) {
  std::ifstream in(path, std::ios::binary);
  if (!in) throw std::runtime_error("runtime file unavailable: " + path);
  std::ostringstream data; data << in.rdbuf(); return data.str();
}
static std::string sha(const std::string &s) {
  unsigned char digest[SHA256_DIGEST_LENGTH]; SHA256((const unsigned char *)s.data(), s.size(), digest);
  static const char *hex = "0123456789abcdef"; std::string result;
  for (auto c : digest) { result += hex[c >> 4]; result += hex[c & 15]; } return result;
}
template<class T> T symbol(void *handle, const char *name) {
  auto address = dlsym(handle, name); if (!address) throw std::runtime_error(std::string("native symbol missing: ") + name);
  return reinterpret_cast<T>(address);
}
#define NATIVE(name) symbol<decltype(&name)>(handle, #name)

struct Runtime {
  Json manifest;
  void *handle = nullptr;
  std::string scratch;
  bool ready = false;
  explicit Runtime(const std::string &path) {
    std::string content = read(path);
    if (sha(content) != manifest_sha) throw std::runtime_error("qualification manifest digest mismatch");
    manifest.Parse(content.c_str());
    for (auto it = manifest["files"].MemberBegin(); it != manifest["files"].MemberEnd(); ++it)
      if (sha(read(it->name.GetString())) != it->value.GetString()) throw std::runtime_error("qualified runtime file digest mismatch");
  }
  void initialize() {
    char temp[] = "/tmp/cubrid-parser-worker-XXXXXX";
    char *path = mkdtemp(temp); if (!path) throw std::runtime_error("private directory creation failed"); scratch = path;
    // Clear all ambient CUBRID settings, loader settings and user configuration.
    clearenv(); setenv("PATH", "/usr/bin:/bin", 1); setenv("LANG", "C.UTF-8", 1);
    setenv("HOME", scratch.c_str(), 1);
    // envvar_confdir_file() reads CUBRID/conf independently of CUBRID_CONF.
    // Supply a private prefix so an installation's locale configuration is never inherited.
    std::filesystem::create_directory(scratch + "/conf");
    const auto assets = std::filesystem::path(manifest["runtimePrefix"].GetString());
    std::filesystem::create_directory_symlink(assets / "msg", scratch + "/msg");
    std::filesystem::create_directory_symlink(assets / "lib", scratch + "/lib");
    std::ofstream(scratch + "/conf/cubrid_locales.txt") << "# Built-in locales only\n";
    setenv("CUBRID", scratch.c_str(), 1);
    for (const char *key : {"CUBRID_CONF", "CUBRID_DATABASES", "CUBRID_TMP"}) setenv(key, scratch.c_str(), 1);
    setenv("CUBRID_LANG", "en_US.utf8", 1);
    if (chdir(scratch.c_str())) throw std::runtime_error("private working directory unavailable");
    std::string conf = scratch + "/cubrid.conf";
    std::ofstream(conf) << "[common]\nansi_quotes=yes\nno_backslash_escapes=no\npipes_as_concat=yes\n"
      "oracle_style_empty_string=no\nquery_trace=no\nintl_check_input_string=yes\nintl_collation=utf8_bin\n"
      "unicode_input_normalization=no\nunicode_output_normalization=no\n";
    std::ofstream(scratch + "/databases.txt");
    handle = dlopen(manifest["library"].GetString(), RTLD_NOW | RTLD_LOCAL);
    if (!handle) throw std::runtime_error(std::string("native runtime unavailable: ") + dlerror());
    auto version = symbol<decltype(&rel_version_string)>(handle, "_Z18rel_version_stringv");
    if (std::string(version()) != manifest["nativeVersion"].GetString()) throw std::runtime_error("native version mismatch");
    if (NATIVE(er_init)((scratch + "/parser.err").c_str(), ER_NEVER_EXIT) || NATIVE(lang_init)()
        || NATIVE(lang_set_charset_lang)("en_US.utf8") || NATIVE(msgcat_init)()
        || NATIVE(sysprm_load_and_init)(nullptr, conf.c_str(), 0)) throw std::runtime_error("native initialization failed");
    NATIVE(prm_set_bool_value)(PRM_ID_ANSI_QUOTES, true);
    NATIVE(prm_set_bool_value)(PRM_ID_NO_BACKSLASH_ESCAPES, false);
    NATIVE(prm_set_bool_value)(PRM_ID_PIPES_AS_CONCAT, true);
    NATIVE(prm_set_bool_value)(PRM_ID_ORACLE_STYLE_EMPTY_STRING, false);
    NATIVE(prm_set_bool_value)(PRM_ID_QUERY_TRACE, false);
    NATIVE(prm_set_bool_value)(PRM_ID_INTL_CHECK_INPUT_STRING, true);
    NATIVE(prm_set_integer_value)(PRM_ID_COMPAT_MODE, 0);
    NATIVE(prm_set_bool_value)(PRM_ID_UNICODE_INPUT_NORMALIZATION, false);
    NATIVE(prm_set_bool_value)(PRM_ID_UNICODE_OUTPUT_NORMALIZATION, false);
    NATIVE(lang_set_parser_use_client_charset)(true);
    verify_settings();
    ready = true;
  }
  void verify_settings() {
    if (!NATIVE(lang_get_parser_use_client_charset)()
        || NATIVE(lang_get_client_charset)() != INTL_CODESET_UTF8
        || !NATIVE(prm_get_value)(PRM_ID_ANSI_QUOTES)->b
        || NATIVE(prm_get_value)(PRM_ID_NO_BACKSLASH_ESCAPES)->b
        || !NATIVE(prm_get_value)(PRM_ID_PIPES_AS_CONCAT)->b
        || NATIVE(prm_get_value)(PRM_ID_ORACLE_STYLE_EMPTY_STRING)->b
        || NATIVE(prm_get_value)(PRM_ID_QUERY_TRACE)->b
        || !NATIVE(prm_get_value)(PRM_ID_INTL_CHECK_INPUT_STRING)->b
        || NATIVE(prm_get_value)(PRM_ID_COMPAT_MODE)->i != 0
        || NATIVE(prm_get_value)(PRM_ID_UNICODE_INPUT_NORMALIZATION)->b
        || NATIVE(prm_get_value)(PRM_ID_UNICODE_OUTPUT_NORMALIZATION)->b
        || !NATIVE(prm_get_value)(PRM_ID_INTL_COLLATION)->str
        || std::string(NATIVE(prm_get_value)(PRM_ID_INTL_COLLATION)->str) != "utf8_bin")
      throw std::runtime_error("native syntax settings differ from profile");
  }
  ~Runtime() { if (!scratch.empty()) { chdir("/"); std::filesystem::remove_all(scratch); } }
};

static void failure(Json &response, const std::string &message, const char *code = "CUBRID-T1002") {
  auto &a = response.GetAllocator();
  response.AddMember("status", "tool-error", a);
  response.AddMember("code", str(code, a), a); response.AddMember("message", str(message, a), a);
}
static Value diagnostic(const char *code, const char *category, const std::string &message,
                        size_t begin, size_t end, Alloc &a) {
  Value d(rapidjson::kObjectType), span(rapidjson::kObjectType);
  span.AddMember("start", uint64_t(begin), a); span.AddMember("end", uint64_t(end), a);
  d.AddMember("code", str(code, a), a); d.AddMember("category", str(category, a), a);
  d.AddMember("severity", str(std::string(category) == "unsupported" ? "warning" : "error", a), a);
  d.AddMember("message", str(message, a), a); d.AddMember("span", span, a);
  d.AddMember("rangePrecision", "statement", a); return d;
}
static void parse(Runtime &runtime, const std::string &text, Json &response) {
  auto &a = response.GetAllocator(); auto handle = runtime.handle;
  if (text.find('\0') != std::string::npos || text.size() > 8 * 1024 * 1024) {
    failure(response, "NUL or input larger than 8 MiB", "CUBRID-T1003"); return;
  }
  runtime.verify_settings();
  Value diagnostics(rapidjson::kArrayType), kinds(rapidjson::kArrayType), decisions(rapidjson::kArrayType), observations(rapidjson::kArrayType);
  int priority = 0; size_t admitted = 0, unsupported = 0;
  bool truncated = false; size_t truncated_begin = 0, processed_end = 0;
  auto append_diagnostic = [&](Value value) {
    if (diagnostics.Size() < 255) diagnostics.PushBack(value, a);
    else truncated = true;
  };
  for (const auto &statement : coverage::scan(text)) {
    if (diagnostics.Size() >= 255) {
      truncated = true; truncated_begin = processed_end; break;
    }
    size_t begin = coverage::codepoints(text, statement.begin), end = coverage::codepoints(text, statement.end);
    processed_end = end;
    const auto *family = coverage::admit(statement);
    const char *kind = family ? family->kind : nullptr;
    Value decision(rapidjson::kObjectType);
    decision.AddMember("start", uint64_t(begin), a); decision.AddMember("end", uint64_t(end), a);
    decision.AddMember("admitted", kind != nullptr && !statement.lexical_error, a);
    decisions.PushBack(decision, a);
    if (statement.lexical_error) {
      append_diagnostic(diagnostic("CUBRID-S1001", "syntax", "Unterminated quoted token or comment", begin, end, a));
      priority = std::max(priority, 2); continue;
    }
    if (!kind) {
      ++unsupported; priority = std::max(priority, 1);
      append_diagnostic(diagnostic("CUBRID-U1002", "unsupported", "Statement is outside qualified native coverage", begin, end, a));
      continue;
    }
    ++admitted;
    NATIVE(er_clear)();
    PARSER_CONTEXT *parser = NATIVE(parser_create_parser)();
    if (!parser) throw std::runtime_error("native parser allocation failed");
    struct Cleanup { void *handle; PARSER_CONTEXT *parser; ~Cleanup() { NATIVE(parser_free_parser)(parser); } } cleanup{handle, parser};
    const auto source = text.substr(statement.begin, statement.end - statement.begin);
    PT_NODE **tree = NATIVE(parser_parse_string_with_escapes)(parser, source.c_str(), false);
#ifdef CUBRID_PARSER_TEST_INTERNAL_ERROR
    // Deterministic classifier fixture. No production request can set this flag.
    parser->flag.has_internal_error = 1;
#endif
    const int native_error = NATIVE(er_errid)();
    const bool internal = parser->flag.has_internal_error;
    const bool flagged = pt_has_error(parser);
    PT_NODE *error = NATIVE(pt_get_errors)(parser);
    size_t errors = 0, trees = 0;
    if (tree) while (tree[trees]) ++trees;
    while (error) {
      int number = 0, line = 0, column = 0; const char *message = nullptr;
      error = NATIVE(pt_get_next_error)(error, &number, &line, &column, &message); ++errors;
      auto d = diagnostic((internal || native_error != NO_ERROR) ? "CUBRID-T1002" : "CUBRID-S1001",
                          (internal || native_error != NO_ERROR) ? "tool" : "syntax",
                          message ? message : "Native parser rejected input", begin, end, a);
      Value coordinates(rapidjson::kObjectType);
      coordinates.AddMember("statement", number, a); coordinates.AddMember("line", line, a); coordinates.AddMember("column", column, a);
      d.AddMember("nativeCoordinates", coordinates, a); append_diagnostic(std::move(d));
    }
    Value observation(rapidjson::kObjectType);
    observation.AddMember("hasTree", tree != nullptr, a); observation.AddMember("treeCount", uint64_t(trees), a);
    observation.AddMember("hasInternalError", internal, a); observation.AddMember("hasError", flagged, a);
    observation.AddMember("errorCount", uint64_t(errors), a);
    observation.AddMember("nativeErrorId", native_error, a);
    observation.AddMember("partialStackCount", parser->stack_top, a); observations.PushBack(observation, a);
    if (internal || (flagged && errors == 0) || native_error != NO_ERROR) {
      priority = 3;
      if (!errors) append_diagnostic(diagnostic("CUBRID-T1002", "tool", "Native internal or unreported error", begin, end, a));
    } else if (errors) priority = std::max(priority, 2);
    else if (trees != 1 || !tree[0] || tree[0]->node_type != family->native_kind) {
      priority = 3; append_diagnostic(diagnostic("CUBRID-T1002", "tool", "Missing, partial or unexpected native statement tree", begin, end, a));
    } else kinds.PushBack(str(kind, a), a);
    if (truncated) {
      truncated_begin = statement.end < text.size() ? end : begin;
      break;
    }
  }
  if (truncated) {
    const size_t end = coverage::codepoints(text, text.size());
    if (processed_end < end) {
      Value tail(rapidjson::kObjectType);
      tail.AddMember("start", uint64_t(processed_end), a); tail.AddMember("end", uint64_t(end), a);
      tail.AddMember("admitted", false, a); decisions.PushBack(tail, a);
    }
    diagnostics.PushBack(diagnostic("CUBRID-T1002", "tool", "256 diagnostic limit reached; result truncated",
                                    truncated_begin, end, a), a);
    response.AddMember("diagnosticsTruncated", true, a);
    priority = 3;
  }
  runtime.verify_settings();
  response.AddMember("syntaxSettingsUnchanged", true, a);
  response.AddMember("status", str(priority == 3 ? "tool-error" : priority == 2 ? "syntax-error" : priority == 1 ? "unsupported" : "valid", a), a);
  response.AddMember("profile", Value(runtime.manifest["profile"], a), a);
  response.AddMember("manifestDigest", str(manifest_sha, a), a);
  response.AddMember("coverage", str(truncated ? (admitted ? "partial" : "none") :
                                   unsupported ? (admitted ? "partial" : "none") : "complete", a), a);
  response.AddMember("diagnostics", diagnostics, a); response.AddMember("statementKinds", kinds, a);
  response.AddMember("coverageDecisions", decisions, a); response.AddMember("nativeObservations", observations, a);
}
int main(int argc, char **argv) {
  rlimit no_core{0, 0}; setrlimit(RLIMIT_CORE, &no_core);
  rlimit memory{512 * 1024 * 1024, 512 * 1024 * 1024};
  if (setrlimit(RLIMIT_AS, &memory)) return 1;
  std::string startup_error; std::unique_ptr<Runtime> runtime;
  try { if (argc != 3 || std::string(argv[1]) != "--manifest") throw std::runtime_error("explicit --manifest is required");
    runtime = std::make_unique<Runtime>(argv[2]); }
  catch (const std::exception &e) { startup_error = e.what(); }
  std::string line;
  // JSON escaping can expand the 8 MiB text input sixfold. Bound the frame too.
  auto read_line = [&]() {
    line.clear(); char c;
    while (std::cin.get(c)) {
      if (c == '\n') return true;
      line += c;
      if (line.size() > 64 * 1024 * 1024) return true;
    }
    return !line.empty();
  };
  while (read_line()) {
    Json request, response; response.SetObject(); auto &a = response.GetAllocator();
    request.Parse<rapidjson::kParseValidateEncodingFlag>(line.data(), line.size());
    response.AddMember("protocolVersion", 1, a);
    if (request.IsObject() && request.HasMember("id")) response.AddMember("id", Value(request["id"], a), a);
    else response.AddMember("id", Value(), a);
    bool stop = false;
    try {
      if (request.HasParseError() && (request.GetParseError() == rapidjson::kParseErrorStringInvalidEncoding
          || request.GetParseError() == rapidjson::kParseErrorStringUnicodeSurrogateInvalid))
        throw InputFailure("request contains invalid UTF-8 or Unicode scalars");
      if (line.size() > 64 * 1024 * 1024 || request.HasParseError() || !request.IsObject() || !request.HasMember("id")
          || !request["id"].IsInt64()
          || !request.HasMember("protocolVersion") || request["protocolVersion"] != 1
          || !request.HasMember("method") || !request["method"].IsString()) throw std::runtime_error("invalid protocol request");
      const std::string method(request["method"].GetString(), request["method"].GetStringLength());
      if (method == "shutdown") { response.AddMember("status", "closed", a); stop = true; }
      else if (!startup_error.empty()) failure(response, startup_error,
          startup_error.find("unavailable") != std::string::npos ? "CUBRID-T1001" : "CUBRID-T1002");
      else if (method == "initialize") {
        if (!request.HasMember("profile") || !request["profile"].IsString()
            || request["profile"] != runtime->manifest["profile"]) {
          response.AddMember("status", "unsupported", a); response.AddMember("code", "CUBRID-U1001", a);
        } else if (request.HasMember("runtimePrefix") && (!request["runtimePrefix"].IsString()
                   || request["runtimePrefix"] != runtime->manifest["runtimePrefix"])) {
          failure(response, "runtime prefix differs from qualified manifest", "CUBRID-T1003");
        } else if (request.HasMember("manifestDigest") && (!request["manifestDigest"].IsString()
                   || std::string(request["manifestDigest"].GetString()) != manifest_sha)) {
          failure(response, "requested manifest digest mismatch");
        } else {
          if (!runtime->ready) runtime->initialize();
          response.AddMember("status", "ready", a);
          for (const char *key : {"profile", "sourceCommit", "nativeVersion", "settings", "platform", "supportedStatementKinds", "coverageRevision", "runtimePrefix", "testOnly"})
            response.AddMember(str(key, a), Value(runtime->manifest[key], a), a);
          response.AddMember("manifestDigest", str(manifest_sha, a), a);
        }
      } else if (method == "parse" && runtime->ready) {
        if (!request.HasMember("text") || !request["text"].IsString()) throw std::runtime_error("parse text must be a UTF-8 string");
        parse(*runtime, std::string(request["text"].GetString(), request["text"].GetStringLength()), response);
      } else throw std::runtime_error("unknown method or runtime not initialized");
    } catch (const InputFailure &e) { failure(response, e.what(), "CUBRID-T1003"); }
    catch (const std::exception &e) { failure(response, e.what()); }
    rapidjson::StringBuffer output; rapidjson::Writer<rapidjson::StringBuffer> writer(output); response.Accept(writer);
    std::cout << output.GetString() << std::endl; if (stop) break;
  }
}
