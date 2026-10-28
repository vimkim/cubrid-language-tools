#pragma once
#include "literal_select.hpp"
#include "query_dml.hpp"
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
    {"PT_SELECT", PT_SELECT, bounded_query},
    {"PT_INSERT", PT_INSERT, bounded_insert},
    {"PT_UPDATE", PT_UPDATE, bounded_update},
    {"PT_DELETE", PT_DELETE, bounded_delete},
    {"PT_MERGE", PT_MERGE, bounded_merge},
    {"PT_CREATE_SERIAL", PT_CREATE_SERIAL, create_serial},
  };
  for (const auto &family : families) if (family.admits(statement)) return &family;
  return nullptr;
}
}
