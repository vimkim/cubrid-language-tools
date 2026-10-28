#pragma once
#include <cctype>
#include <string>
#include <vector>

namespace coverage {
struct Token { std::string text; char kind; size_t begin = 0, end = 0; };
struct Statement {
  size_t begin = 0, end = 0;
  std::vector<Token> tokens;
  bool lexical_error = false, unsafe = false;
};
inline size_t codepoints(const std::string &text, size_t end) {
  size_t n = 0; for (size_t i = 0; i < end; ++i) if ((text[i] & 0xc0) != 0x80) ++n; return n;
}
// Only comments, ordinary strings, UTF-8 identifier bytes and audited punctuation.
// This scanner grants coverage, never syntax acceptance.
inline std::vector<Statement> scan(const std::string &text) {
  std::vector<Statement> result; Statement current; size_t i = 0;
  auto finish = [&](size_t end) {
    current.end = end;
    if (!current.tokens.empty() || current.lexical_error || current.unsafe) result.push_back(current);
    current = Statement{}; current.begin = end;
  };
  while (i < text.size()) {
    unsigned char c = text[i];
    if (std::isspace(c)) { ++i; continue; }
    if (text.compare(i, 2, "--") == 0 || text.compare(i, 2, "//") == 0) {
      if (i + 2 < text.size() && text[i+2] == '+') current.unsafe = true;
      i = text.find('\n', i); if (i == std::string::npos) i = text.size(); continue;
    }
    if (text.compare(i, 2, "/*") == 0) {
      if (i + 2 < text.size() && (text[i+2] == '+' || text[i+2] == '!')) current.unsafe = true;
      size_t end = text.find("*/", i + 2);
      if (end == std::string::npos) { current.lexical_error = true; i = text.size(); break; }
      if (text.find("/*", i + 2) < end) current.unsafe = true;
      i = end + 2; continue;
    }
    if (c == ';') { ++i; finish(i); continue; }
    size_t start = i;
    if (c == '\'' || c == '"' || c == '`' || c == '[') {
      char closing = c == '[' ? ']' : c; bool closed = false;
      ++i;
      while (i < text.size()) {
        if (c == '\'' && text[i] == '\\') { i += std::min(size_t(2), text.size() - i); continue; }
        if (text[i++] == closing) {
          if (i < text.size() && text[i] == closing) { ++i; continue; }
          closed = true; break;
        }
      }
      if (!closed) current.lexical_error = true;
      current.tokens.push_back({text.substr(start, i-start), c == '\'' ? 's' : 'q', start, i});
    } else if (std::isalpha(c) || c == '_' || c >= 0x80) {
      while (i < text.size() && (std::isalnum((unsigned char)text[i]) || text[i] == '_' || (unsigned char)text[i] >= 0x80)) ++i;
      std::string word = text.substr(start, i-start);
      for (char &ch : word) if ((unsigned char)ch < 0x80) ch = std::toupper((unsigned char)ch);
      current.tokens.push_back({word, 'w', start, i});
    } else if (std::isdigit(c)) {
      while (i < text.size() && std::isdigit((unsigned char)text[i])) ++i;
      // Restrict this first profile to integer literals; other numeric forms stay unsupported.
      current.tokens.push_back({text.substr(start, i-start), 'n', start, i});
    } else {
      // Preserve native compound tokens so e.g. -> cannot become arithmetic
      // followed by a comparison, or << two audited comparison tokens.
      size_t width = 1;
      for (const char *op : {"->>", "<=>", "->", "||", "<>", ">=", "<=", "?:", "!=", "<<", ">>", "&&", ":="})
        if (text.compare(i, std::char_traits<char>::length(op), op) == 0) { width = std::char_traits<char>::length(op); break; }
      i += width; current.tokens.push_back({text.substr(start, width), 'p', start, i});
    }
  }
  finish(text.size()); return result;
}
}
