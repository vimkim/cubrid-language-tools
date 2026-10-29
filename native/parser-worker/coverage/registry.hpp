#pragma once
#include "literal_select.hpp"
#include "query_dml.hpp"
#include "schema_engineer.hpp"
namespace coverage {
struct Family {
  const char *kind;
  PT_NODE_TYPE native_kind;
  bool (*admits)(const Statement &);
};
inline const Family *admit(const Statement &statement) {
  static const Family ordered = {"PT_SELECT", PT_SELECT, literal_select};
  for (const auto &token : statement.tokens)
    if (token.kind == 'h') return ordered.admits(statement) ? &ordered : nullptr;
  static const Family families[] = {
    {"PT_SELECT", PT_SELECT, literal_select},
    {"PT_SELECT", PT_SELECT, bounded_query},
    {"PT_INSERT", PT_INSERT, bounded_insert},
    {"PT_UPDATE", PT_UPDATE, bounded_update},
    {"PT_DELETE", PT_DELETE, bounded_delete},
    {"PT_MERGE", PT_MERGE, bounded_merge},
    {"PT_CREATE_SERIAL", PT_CREATE_SERIAL, create_serial},
    {"PT_CREATE_ENTITY", PT_CREATE_ENTITY, create_table},
    {"PT_CREATE_ENTITY", PT_CREATE_ENTITY, create_view},
    {"PT_ALTER", PT_ALTER, alter_table},
    {"PT_ALTER", PT_ALTER, alter_view},
    {"PT_DROP", PT_DROP, drop_entity},
    {"PT_CREATE_INDEX", PT_CREATE_INDEX, create_index},
    {"PT_ALTER_INDEX", PT_ALTER_INDEX, alter_index},
    {"PT_DROP_INDEX", PT_DROP_INDEX, drop_index},
    {"PT_ALTER_SERIAL", PT_ALTER_SERIAL, alter_serial},
    {"PT_DROP_SERIAL", PT_DROP_SERIAL, drop_serial},
    {"PT_SELECT", PT_SELECT, show_trace},
    {"PT_EVALUATE", PT_EVALUATE, evaluate},
    {"PT_UPDATE_STATS", PT_UPDATE_STATS, update_statistics},
    {"PT_SET_SYS_PARAMS", PT_SET_SYS_PARAMS, set_system_parameters},
    {"PT_QUERY_TRACE", PT_QUERY_TRACE, set_trace},
    {"PT_COMMIT_WORK", PT_COMMIT_WORK, commit},
    {"PT_ROLLBACK_WORK", PT_ROLLBACK_WORK, rollback},
    {"PT_SAVEPOINT", PT_SAVEPOINT, savepoint},
  };
  for (const auto &family : families) if (family.admits(statement)) return &family;
  return nullptr;
}
}
