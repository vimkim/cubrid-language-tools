#pragma once
#include "scan.hpp"
namespace coverage {
inline bool ordered_hint(const Token &token) {
  std::string name = token.text.substr(3, token.text.size() - 5);
  size_t begin = name.find_first_not_of(" \t\r\n");
  if (begin == std::string::npos) return false;
  name = name.substr(begin, name.find_last_not_of(" \t\r\n") - begin + 1);
  for (char &c : name) if ((unsigned char)c < 0x80) c = std::toupper((unsigned char)c);
  return name == "ORDERED";
}
inline bool literal_select(const Statement &s) {
  if (s.unsafe || s.tokens.empty() || s.tokens[0].text != "SELECT") return false;
  size_t begin = 1;
  if (s.tokens.size() > 1 && s.tokens[1].kind == 'h') {
    if (!ordered_hint(s.tokens[1])) return false;
    begin = 2;
  }
  for (size_t i = begin; i < s.tokens.size(); ++i) {
    const auto &t = s.tokens[i];
    if (t.kind == 'n' && t.text.size() > 38) return false;
    if (t.text == "-" || t.text == "+") {
      if (i != begin && s.tokens[i-1].text != ",") return false;
      if (i + 1 < s.tokens.size() && s.tokens[i+1].kind != 'n') return false;
      continue;
    }
    if (t.kind == 'n' || t.kind == 's' || t.text == "NULL" || t.text == ",") continue;
    return false;
  }
  return true;
}
}
