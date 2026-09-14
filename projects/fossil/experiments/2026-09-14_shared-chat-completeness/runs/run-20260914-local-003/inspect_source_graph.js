const fs = require("fs");

const sourcePath = process.argv[2];
if (!sourcePath) throw new Error("usage: node inspect_source_graph.js SOURCE_RESPONSE");
const raw = fs.readFileSync(sourcePath);
const html = raw.toString("utf8");
const scripts = [...html.matchAll(/<script[^>]*>([\s\S]*?)<\/script>/g)].map(
  (match) => match[1],
);
const streamBody = scripts.find((script) => script.includes("streamController.enqueue"));
if (!streamBody) throw new Error("React Router stream script not found");
const enqueueArgument = streamBody.match(/enqueue\(([\s\S]*)\);?$/)?.[1];
if (!enqueueArgument) throw new Error("stream enqueue argument not found");
const values = JSON.parse(JSON.parse(enqueueArgument));
const negative = {
  "-1": "hole",
  "-2": "nan",
  "-3": "infinity",
  "-4": "-infinity",
  "-5": undefined,
  "-6": null,
};
const cache = new Map();
function decodeKey(key) {
  if (!key.startsWith("_")) return key;
  const value = values[Number(key.slice(1))];
  return typeof value === "string" ? value : `#${key.slice(1)}`;
}
function decode(reference) {
  if (typeof reference !== "number") return reference;
  if (reference < 0) return negative[String(reference)] ?? `NEG${reference}`;
  if (cache.has(reference)) return cache.get(reference);
  const value = values[reference];
  if (
    typeof value === "string" ||
    typeof value === "boolean" ||
    value === null ||
    typeof value === "number"
  ) return value;
  if (Array.isArray(value)) {
    const result = [];
    cache.set(reference, result);
    for (const item of value) result.push(decode(item));
    return result;
  }
  const result = {};
  cache.set(reference, result);
  for (const [key, item] of Object.entries(value)) result[decodeKey(key)] = decode(item);
  return result;
}

const data = decode(0).loaderData["routes/share.$shareId.($action)"].serverResponse.data;
const entries = Object.entries(data.mapping);
const activeBranch = [];
const seen = new Set();
let current = data.current_node;
while (current && !seen.has(current)) {
  seen.add(current);
  activeBranch.push(current);
  current = data.mapping[current]?.parent;
}
activeBranch.reverse();
const linear = data.linear_conversation;
const linearSummary = {
  is_array: Array.isArray(linear),
  length: Array.isArray(linear) ? linear.length : null,
  first_type: Array.isArray(linear) && linear.length ? typeof linear[0] : null,
  first_id: Array.isArray(linear) && linear.length ? linear[0]?.id ?? null : null,
  last_id: Array.isArray(linear) && linear.length ? linear.at(-1)?.id ?? null : null,
  keys: linear && typeof linear === "object" && !Array.isArray(linear) ? Object.keys(linear) : [],
};
const linearIds = Array.isArray(linear)
  ? linear.map((item) => typeof item === "string" ? item : item?.node_id ?? item?.id ?? null)
  : [];
const markerDiagnostics = Array.isArray(linear)
  ? linear
      .filter((item) => item?.message && typeof item.message === "object")
      .map((item) => {
        const message = item.message;
        const parts = Array.isArray(message.content?.parts)
          ? message.content.parts.filter((part) => typeof part === "string")
          : [];
        const text = parts.join("\n");
        const firstLine = text.split(/\r?\n/, 1)[0];
        const escaped = JSON.stringify(firstLine).slice(1, -1);
        return {
          id_present: typeof message.id === "string" && html.includes(message.id),
          text_length: text.length,
          first_line_present: Boolean(firstLine) && html.includes(firstLine.slice(0, 96)),
          escaped_first_line_present: Boolean(firstLine) && html.includes(escaped.slice(0, 96)),
          has_text: Boolean(text),
        };
      })
  : [];
const childRefs = new Set(
  entries.flatMap(([, node]) => Array.isArray(node?.children) ? node.children : []),
);
const unresolved = [...childRefs].filter((id) => !data.mapping[id]);
const messageEntries = entries.filter(([, node]) => node?.message && typeof node.message === "object");
const messageIds = messageEntries.map(([, node]) => node.message?.id).filter((id) => typeof id === "string");
const roles = {};
for (const [, node] of messageEntries) {
  const role = node.message?.author?.role ?? "unknown";
  roles[role] = (roles[role] ?? 0) + 1;
}

const graph = {
  response_bytes: raw.length,
  conversation_id: data.conversation_id,
  title: data.title,
  current_node: data.current_node,
  root_nodes: entries.filter(([, node]) => !node?.parent).map(([id]) => id),
  mapping_node_count: entries.length,
  message_bearing_node_count: messageEntries.length,
  unique_message_id_count: new Set(messageIds).size,
  active_branch_node_count: activeBranch.length,
  active_branch_message_count: activeBranch.filter((id) => data.mapping[id]?.message).length,
  non_active_exposed_node_count: entries.filter(([id]) => !new Set(activeBranch).has(id)).length,
  unresolved_child_reference_count: unresolved.length,
  role_counts: roles,
  continuation_field: data.continue_conversation_url ?? null,
};
const linearChecks = {
  count_matches_mapping: Array.isArray(linear) && linear.length === entries.length,
  count_matches_active_branch: Array.isArray(linear) && linear.length === activeBranch.length,
  ids_are_node_ids: Array.isArray(linear) && linearIds.every((id) => typeof id === "string" && Boolean(data.mapping[id])),
  ids_match_active_branch_order: Array.isArray(linear) && linearIds.length === activeBranch.length && linearIds.every((id, index) => id === activeBranch[index]),
  ids_match_active_branch_set: Array.isArray(linear) && new Set(linearIds).size === activeBranch.length && linearIds.every((id) => new Set(activeBranch).has(id)),
};
console.log(JSON.stringify({
  schema_version: "lab.shared-chat-source-graph-inspection.v1",
  graph,
  linear_conversation: linearSummary,
  linear_ids_sample: { first: linearIds.slice(0, 3), last: linearIds.slice(-3) },
  linear_checks: linearChecks,
  marker_diagnostics: {
    message_count: markerDiagnostics.length,
    id_present_count: markerDiagnostics.filter((item) => item.id_present).length,
    first_line_present_count: markerDiagnostics.filter((item) => item.first_line_present).length,
    escaped_first_line_present_count: markerDiagnostics.filter((item) => item.escaped_first_line_present).length,
    text_bearing_count: markerDiagnostics.filter((item) => item.has_text).length,
  },
  source_keys: Object.keys(data).sort(),
  continuation_field_type: typeof data.continue_conversation_url,
}, null, 2));
