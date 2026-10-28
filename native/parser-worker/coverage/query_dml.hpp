#pragma once
#include "scan.hpp"
#include "keywords.hpp"
#include <set>

namespace coverage {
inline std::string identifier_text(const Token &token) {
  std::string value = token.kind == 'q' ? token.text.substr(1, token.text.size() - 2) : token.text;
  for (char &c : value) if ((unsigned char)c < 0x80) c = std::toupper((unsigned char)c);
  return value;
}
inline bool ordinary_identifier(const Token &token) {
  if (token.kind == 'w') return !native_keyword(token.text);
  if (token.kind != 'q') return false;
  // Only simple delimited names: embedded delimiter/escape/dot spellings are
  // intentionally outside this revision, regardless of what the lexer accepts.
  for (size_t j = 1; j + 1 < token.text.size(); ++j) {
    unsigned char c = token.text[j];
    if (!(std::isalnum(c) || c == '_' || c == ' ' || c >= 0x80)) return false;
  }
  return true;
}
inline bool query_features(const Statement &s, const std::set<std::string> &extra) {
  if (s.unsafe || s.tokens.empty()) return false;
  static const std::set<std::string> words = {
    "SELECT", "WITH", "AS", "FROM", "WHERE", "DISTINCT", "JOIN", "INNER",
    "LEFT", "RIGHT", "OUTER", "CROSS", "ON", "AND", "OR", "NOT", "EXISTS", "IS", "NULL"
  };
  static const std::set<std::string> punctuation = {"(", ")", ",", ".", "+", "-", "*", "/", "=", "<", ">", "<=", ">=", "<>", "!="};
  static const std::set<std::string> serial_names = {"CURRENT_VALUE", "CURRVAL", "NEXT_VALUE", "NEXTVAL"};
  static const std::set<std::string> structural_parens = {
    "SELECT", "DISTINCT", "AS", "FROM", "WHERE", "JOIN", "ON", "AND", "OR", "NOT", "EXISTS",
    "VALUE", "VALUES", "INTO", "USING", "INSERT", "UPDATE", "WITH", "IS"
  };
  for (size_t i = 0; i < s.tokens.size(); ++i) {
    const auto &t = s.tokens[i];
    const bool identifier = ordinary_identifier(t);
    if (t.kind == 'n') { if (t.text.size() > 38) return false; }
    else if (t.kind == 's') { /* audited ordinary character literal */ }
    else if (identifier) { if (serial_names.count(identifier_text(t))) return false; }
    else if (t.kind == 'w') { if (!words.count(t.text) && !extra.count(t.text)) return false; }
    else if (t.kind != 'p' || !punctuation.count(t.text)) return false;
    if (t.text == "INTO" && i != 1) return false; // no SELECT INTO / output variables
    if (i && (t.text == "INSERT" || t.text == "UPDATE" || t.text == "DELETE") &&
        !(s.tokens[0].text == "MERGE" && s.tokens[i - 1].text == "THEN")) return false;
    if (i + 1 == s.tokens.size()) continue;
    const auto &next = s.tokens[i + 1];
    // Decimal/exponent/bit/hex literals and charset/national string prefixes
    // must not be mistaken for audited integers or ordinary strings.
    if ((t.kind == 'n' && (next.text == "." || (next.kind == 'w' && t.end == next.begin))) ||
        (t.text == "." && next.kind == 'n') || (identifier && next.kind == 's')) return false;
    // Only audited structural keyword-( pairs may precede parentheses. This
    // also denies reserved LEFT/RIGHT, SET(subquery), and nonreserved MATCHED
    // as a generic function name. INSERT's simple target column list is the
    // sole ordinary identifier-( exception; no SQL grammar is duplicated here.
    if ((t.kind == 'w' || t.kind == 'q') && next.text == "(" &&
        !(t.kind == 'w' && structural_parens.count(t.text)) &&
        !(identifier && s.tokens[0].text == "INSERT" && (i == 1 || (i == 2 && s.tokens[1].text == "INTO")))) return false;
    // Exclude Oracle (+), right-arrow paths and extended operator paths.
    if (t.text == "(" && next.text == "+" && i + 2 < s.tokens.size() && s.tokens[i + 2].text == ")") return false;
  }
  return true;
}
inline bool bounded_query(const Statement &s) {
  return !s.tokens.empty() && (s.tokens[0].text == "SELECT" || s.tokens[0].text == "WITH") && query_features(s, {});
}
inline bool bounded_insert(const Statement &s) {
  return !s.tokens.empty() && s.tokens[0].text == "INSERT" && query_features(s, {"INSERT", "INTO", "VALUES", "VALUE"});
}
inline bool bounded_update(const Statement &s) {
  return !s.tokens.empty() && s.tokens[0].text == "UPDATE" && query_features(s, {"UPDATE", "SET"});
}
inline bool bounded_delete(const Statement &s) {
  return !s.tokens.empty() && s.tokens[0].text == "DELETE" && query_features(s, {"DELETE"});
}
inline bool bounded_merge(const Statement &s) {
  return !s.tokens.empty() && s.tokens[0].text == "MERGE" && query_features(s,
    {"MERGE", "INTO", "USING", "WHEN", "MATCHED", "THEN", "UPDATE", "SET", "INSERT", "VALUES", "VALUE"});
}
}
