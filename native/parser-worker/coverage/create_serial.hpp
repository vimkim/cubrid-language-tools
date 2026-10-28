#pragma once
#include "scan.hpp"
#include <set>
namespace coverage {
inline bool create_serial(const Statement &s) {
  if (s.unsafe || s.tokens.size() < 2 || s.tokens[0].text != "CREATE" || s.tokens[1].text != "SERIAL") return false;
  static const std::set<std::string> options = {"START", "WITH", "INCREMENT", "BY", "MINVALUE", "MAXVALUE",
    "NOMINVALUE", "NOMAXVALUE", "CYCLE", "NOCYCLE", "CACHE", "NOCACHE", "COMMENT"};
  if (s.tokens.size() > 2 && s.tokens[2].kind != 'w') return false;
  for (size_t i = 3; i < s.tokens.size(); ++i) {
    const auto &t = s.tokens[i];
    if (t.kind == 'n' && t.text.size() > 38) return false;
    if (t.kind == 'n' || t.kind == 's' || t.text == "-" || t.text == "+" || options.count(t.text)) continue;
    return false;
  }
  return true;
}
}
