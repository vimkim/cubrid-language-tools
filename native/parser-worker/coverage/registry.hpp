#pragma once
#include "literal_select.hpp"
#include "create_serial.hpp"
namespace coverage {
struct Family {
  const char *kind;
  PT_NODE_TYPE native_kind;
  bool (*admits)(const Statement &);
};
inline const Family *admit(const Statement &statement) {
  static const Family families[] = {
    {"PT_SELECT", PT_SELECT, literal_select},
    {"PT_CREATE_SERIAL", PT_CREATE_SERIAL, create_serial},
  };
  for (const auto &family : families) if (family.admits(statement)) return &family;
  return nullptr;
}
}
