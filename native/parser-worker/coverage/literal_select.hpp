#pragma once
#include "scan.hpp"
namespace coverage {
inline bool literal_select(const Statement &s) {
  if (s.unsafe || s.tokens.empty() || s.tokens[0].text != "SELECT") return false;
  for (size_t i = 1; i < s.tokens.size(); ++i) {
    const auto &t = s.tokens[i];
    if (t.kind == 'n' && t.text.size() > 38) return false;
    if (t.text == "-" || t.text == "+") {
      if (i != 1 && s.tokens[i-1].text != ",") return false;
      if (i + 1 < s.tokens.size() && s.tokens[i+1].kind != 'n') return false;
      continue;
    }
    if (t.kind == 'n' || t.kind == 's' || t.text == "NULL" || t.text == ",") continue;
    return false;
  }
  return true;
}
}
