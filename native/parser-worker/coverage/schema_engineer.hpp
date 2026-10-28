#pragma once
#include "query_dml.hpp"
#include "create_serial.hpp"

namespace coverage {
inline bool prefix(const Statement &s, std::initializer_list<const char *> words) {
  if (s.unsafe || s.tokens.empty()) return false;
  size_t i = 0;
  for (auto word : words) {
    if (i == s.tokens.size()) return true; // native parser diagnoses incomplete input
    if (s.tokens[i].kind != 'w' || s.tokens[i].text != word) return false;
    ++i;
  }
  return true;
}
inline bool named_tail(const Statement &s, size_t begin, bool commas = false, bool strings = false) {
  for (size_t i = begin; i < s.tokens.size(); ++i)
    if (!ordinary_identifier(s.tokens[i]) && !(commas && s.tokens[i].text == ",") &&
        !(strings && s.tokens[i].kind == 's')) return false;
  return true;
}
inline bool integer_columns(const Statement &s, size_t begin, size_t target) {
  for (size_t i = begin; i < s.tokens.size(); ++i) {
    const auto &t = s.tokens[i];
    if (ordinary_identifier(t)) {
      // A name can only introduce a column, never an object datatype or call.
      if (i != target && (!i || (s.tokens[i-1].text != "(" && s.tokens[i-1].text != "," &&
                                s.tokens[i-1].text != "ADD" && s.tokens[i-1].text != "COLUMN"))) return false;
    } else if (t.kind == 'w') {
      if (t.text != "INT" && t.text != "INTEGER" && t.text != "BIGINT" && t.text != "SMALLINT") return false;
    } else if (t.text != "(" && t.text != ")" && t.text != ",") return false;
    if (t.text == "(" && i && (s.tokens[i-1].kind == 'w' || s.tokens[i-1].kind == 'q') && i-1 != target) return false;
  }
  return true;
}
inline bool create_table(const Statement &s) {
  return s.tokens.size() >= 2 && prefix(s, {"CREATE", "TABLE"}) &&
    (s.tokens.size() < 3 || ordinary_identifier(s.tokens[2])) && integer_columns(s, 2, 2);
}
inline bool alter_table(const Statement &s) {
  if (s.tokens.size() < 2 || !prefix(s, {"ALTER", "TABLE"})) return false;
  if (s.tokens.size() > 2 && !ordinary_identifier(s.tokens[2])) return false;
  if (s.tokens.size() > 3 && s.tokens[3].text != "ADD") return false;
  size_t begin = s.tokens.size() > 4 && s.tokens[4].text == "COLUMN" ? 5 : 4;
  return integer_columns(s, begin, 2);
}
inline bool view_query(const Statement &s, bool alter) {
  if (s.tokens.size() < 2 || !prefix(s, {alter ? "ALTER" : "CREATE", "VIEW"})) return false;
  if (s.tokens.size() > 2 && !ordinary_identifier(s.tokens[2])) return false;
  size_t begin = alter ? 5 : 4;
  if (s.tokens.size() > 3 && s.tokens[3].text != (alter ? "CHANGE" : "AS")) return false;
  if (alter && s.tokens.size() > 4 && s.tokens[4].text != "QUERY") return false;
  if (s.tokens.size() <= begin) return true;
  Statement query; query.tokens.assign(s.tokens.begin() + begin, s.tokens.end());
  return bounded_query(query);
}
inline bool create_view(const Statement &s) { return view_query(s, false); }
inline bool alter_view(const Statement &s) { return view_query(s, true); }
inline bool drop_entity(const Statement &s) {
  return s.tokens.size() >= 2 && (prefix(s, {"DROP", "TABLE"}) || prefix(s, {"DROP", "VIEW"})) && named_tail(s, 2, true);
}
inline bool index_form(const Statement &s, const char *verb, bool columns) {
  if (s.tokens.size() < 2 || !prefix(s, {verb, "INDEX"})) return false;
  for (size_t i = 2; i < s.tokens.size(); ++i) {
    const auto &t = s.tokens[i];
    if (ordinary_identifier(t)) { /* simple syntactic reference */ }
    else if (t.kind == 'w' && (t.text == "ON" || (columns && (t.text == "ASC" || t.text == "DESC")) ||
                             (std::string(verb) == "ALTER" && t.text == "REBUILD"))) { }
    else if (!(columns && (t.text == "(" || t.text == ")" || t.text == ","))) return false;
    // Only ON's table name may introduce the index column list. No functions,
    // prefix lengths, expression calls or datatype-call exceptions are allowed.
    if (t.text == "(" && i && (s.tokens[i-1].kind == 'w' || s.tokens[i-1].kind == 'q') &&
        !(i == 5 && ordinary_identifier(s.tokens[4]) && s.tokens[3].text == "ON")) return false;
  }
  return true;
}
inline bool create_index(const Statement &s) { return index_form(s, "CREATE", true); }
inline bool alter_index(const Statement &s) { return index_form(s, "ALTER", false); }
inline bool drop_index(const Statement &s) { return index_form(s, "DROP", false); }
inline bool alter_serial(const Statement &s) {
  if (s.tokens.size() < 2 || !prefix(s, {"ALTER", "SERIAL"})) return false;
  Statement serial = s; serial.tokens[0].text = "CREATE"; return create_serial(serial);
}
inline bool drop_serial(const Statement &s) {
  return s.tokens.size() >= 3 && prefix(s, {"DROP", "SERIAL"}) && named_tail(s, 2);
}
inline bool show_trace(const Statement &s) {
  return s.tokens.size() == 2 && prefix(s, {"SHOW", "TRACE"});
}
inline bool evaluate(const Statement &s) {
  if (!prefix(s, {"EVALUATE"})) return false;
  Statement expression = s; expression.tokens[0].text = "SELECT";
  return query_features(expression, {});
}
inline bool update_statistics(const Statement &s) {
  return s.tokens.size() >= 2 && prefix(s, {"UPDATE", "STATISTICS", "ON"}) && named_tail(s, 3, true);
}
inline bool set_system_parameters(const Statement &s) {
  if (s.tokens.size() < 2 || !prefix(s, {"SET", "SYSTEM", "PARAMETERS"})) return false;
  for (size_t i = 3; i < s.tokens.size(); ++i) if (s.tokens[i].kind != 's' && s.tokens[i].text != ",") return false;
  return true;
}
inline bool set_trace(const Statement &s) {
  if (s.tokens.size() < 2 || !prefix(s, {"SET", "TRACE"})) return false;
  for (size_t i = 2; i < s.tokens.size(); ++i)
    if (s.tokens[i].kind != 'w' || (s.tokens[i].text != "ON" && s.tokens[i].text != "OFF" &&
        s.tokens[i].text != "OUTPUT" && s.tokens[i].text != "TEXT" && s.tokens[i].text != "JSON")) return false;
  return true;
}
inline bool commit(const Statement &s) {
  if (!prefix(s, {"COMMIT"})) return false;
  for (size_t i = 1; i < s.tokens.size(); ++i)
    if (s.tokens[i].kind != 'w' || (s.tokens[i].text != "WORK" && s.tokens[i].text != "RETAIN" && s.tokens[i].text != "LOCK")) return false;
  return true;
}
inline bool rollback(const Statement &s) {
  if (!prefix(s, {"ROLLBACK"})) return false;
  for (size_t i = 1; i < s.tokens.size(); ++i)
    if (!ordinary_identifier(s.tokens[i]) && s.tokens[i].kind != 's' &&
        !(s.tokens[i].kind == 'w' && (s.tokens[i].text == "WORK" || s.tokens[i].text == "TO" || s.tokens[i].text == "SAVEPOINT"))) return false;
  return true;
}
inline bool savepoint(const Statement &s) { return prefix(s, {"SAVEPOINT"}) && named_tail(s, 1, false, true); }
}
