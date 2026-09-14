const fs = require("fs");
const crypto = require("crypto");

const sourcePath = process.argv[2];
const outputPath = process.argv[3];
const runtimeSpecsPath = process.argv[4];
if (!sourcePath || !outputPath || !runtimeSpecsPath) {
  throw new Error("usage: node analyze_complete_capture.js SOURCE RESPONSE_JSON RUNTIME_SPECS_JSON");
}

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
const activeSet = new Set(activeBranch);
const linear = Array.isArray(data.linear_conversation) ? data.linear_conversation : [];
const linearIds = linear.map((item) => item?.id ?? null);
const childRefs = new Set(
  entries.flatMap(([, node]) => Array.isArray(node?.children) ? node.children : []),
);
const unresolvedChildRefs = [...childRefs].filter((id) => !data.mapping[id]);
const messageEntries = entries.filter(([, node]) => node?.message && typeof node.message === "object");
const messageIds = messageEntries.map(([, node]) => node.message?.id).filter((id) => typeof id === "string");
const roles = {};
for (const [, node] of messageEntries) {
  const role = node.message?.author?.role ?? "unknown";
  roles[role] = (roles[role] ?? 0) + 1;
}

const graphChecks = {
  mapping_nonempty: entries.length > 0,
  linear_count_matches_mapping: linear.length === entries.length,
  linear_count_matches_active_branch: linear.length === activeBranch.length,
  linear_ids_are_mapping_nodes: linearIds.every((id) => typeof id === "string" && Boolean(data.mapping[id])),
  linear_ids_match_active_branch_order: linearIds.length === activeBranch.length && linearIds.every((id, index) => id === activeBranch[index]),
  root_present: activeBranch.length > 0 && activeBranch[0] === entries.find(([, node]) => !node?.parent)?.[0],
  current_is_last_linear_node: linear.at(-1)?.id === data.current_node,
  current_has_no_children: !Array.isArray(data.mapping[data.current_node]?.children) || data.mapping[data.current_node].children.length === 0,
  all_child_references_resolved: unresolvedChildRefs.length === 0,
  no_non_active_exposed_nodes: entries.every(([id]) => activeSet.has(id)),
  message_ids_unique: new Set(messageIds).size === messageIds.length,
};
const graphComplete = Object.values(graphChecks).every(Boolean);
if (!graphComplete) throw new Error(`source graph did not satisfy complete representation checks: ${JSON.stringify(graphChecks)}`);

function roleForSource(role) {
  if (role === "user") return "human";
  if (["assistant", "system", "tool"].includes(role)) return role;
  return "other";
}
function sourceNodeId(nodeId) {
  return `ln_src_${nodeId.replace(/-/g, "")}`;
}
function messageId(nodeId) {
  return `msg_src_${nodeId.replace(/-/g, "")}`;
}
const usedMarkers = new Set();
function messageMarker(message) {
  const parts = Array.isArray(message.content?.parts)
    ? message.content.parts.filter((part) => typeof part === "string")
    : [];
  const text = parts.join("\n");
  const firstLine = text.split(/\r?\n/, 1)[0];
  const candidate = firstLine.slice(0, 96);
  // A marker is deliberately required to be an exact byte-visible substring
  // of the captured HTML.  A message ID can occur both as a mapping key and
  // inside the message object, so the fallback grows a local-only context
  // window until it is unique in the immutable source bytes.
  if (
    candidate.length >= 16 &&
    html.includes(candidate) &&
    html.indexOf(candidate) === html.lastIndexOf(candidate) &&
    !usedMarkers.has(candidate)
  ) {
    usedMarkers.add(candidate);
    return candidate;
  }
  const id = String(message.id);
  let position = -1;
  while (true) {
    position = html.indexOf(id, position + 1);
    if (position < 0) break;
    for (let length = id.length; length <= 4096; length += 16) {
      const context = html.slice(position, position + length);
      if (context.length < id.length) continue;
      if (
        html.indexOf(context) === position &&
        html.lastIndexOf(context) === position &&
        !usedMarkers.has(context)
      ) {
        usedMarkers.add(context);
        return context;
      }
    }
  }
  throw new Error(`could not find a unique source marker for message ${id}`);
}

const runtimeMessages = [];
const runtimeNodes = [];
for (const [index, item] of linear.entries()) {
  const message = item?.message;
  if (!message || typeof message !== "object") continue;
  const nodeId = String(item.id);
  const role = roleForSource(String(message.author?.role ?? "other"));
  const marker = messageMarker(message);
  const generatedMessageId = messageId(nodeId);
  runtimeMessages.push({
    message_id: generatedMessageId,
    role,
    actor_id: `chatgpt-share-${role}`,
    marker,
    source_node_id: nodeId,
    source_message_id_present: typeof message.id === "string" && html.includes(message.id),
  });
  const kind = index === linear.length - 1
    ? "conclusion"
    : role === "human" ? "question" : role === "assistant" ? "claim" : "observation";
  runtimeNodes.push({
    node_id: sourceNodeId(nodeId),
    kind,
    label: `Observed ${role} source node ${nodeId.slice(0, 12)}`,
    text: marker,
    message_index: runtimeMessages.length - 1,
    position_state: index === linear.length - 1 ? "current" : "historical",
  });
}

const source = {
  parser: "React Router streamed devalue graph decoder",
  response_bytes: raw.length,
  response_sha256: crypto.createHash("sha256").update(raw).digest("hex"),
  conversation_id: data.conversation_id,
  title: data.title,
  is_public: data.is_public,
  current_node: data.current_node,
  root_nodes: entries.filter(([, node]) => !node?.parent).map(([id]) => id),
  mapping_node_count: entries.length,
  message_bearing_node_count: messageEntries.length,
  unique_message_id_count: new Set(messageIds).size,
  linear_conversation_count: linear.length,
  role_counts: roles,
  active_branch_node_count: activeBranch.length,
  active_branch_message_count: activeBranch.filter((id) => data.mapping[id]?.message).length,
  non_active_exposed_node_count: entries.filter(([id]) => !activeSet.has(id)).length,
  unresolved_child_reference_count: unresolvedChildRefs.length,
  active_branch_first_node: activeBranch[0] ?? null,
  active_branch_last_node: activeBranch.at(-1) ?? null,
  discovered_node_ids: entries.map(([id]) => id).sort(),
  message_node_ids: messageEntries.map(([id]) => id).sort(),
  active_branch_node_ids: [...activeSet].sort(),
  non_active_exposed_node_ids: entries.filter(([id]) => !activeSet.has(id)).map(([id]) => id).sort(),
  unresolved_refs: unresolvedChildRefs.map((id) => ({
    from_node_id: "unknown-parent",
    relation: "child",
    target_node_id: id,
  })),
  continue_conversation_action_url: data.continue_conversation_url ?? null,
};
const result = {
  schema_version: "lab.shared-chat-completeness.v1",
  source_representation: source,
  completeness: "complete",
  completeness_scope: "all nodes and messages exposed by this public-share representation; not an authenticated account export",
  completeness_basis: [
    "source mapping enumerated",
    "linear_conversation contains one entry for every mapping node",
    "linear_conversation IDs match the active parent walk exactly and in order",
    "current node is the final linear node and has no child obligations",
    "all exposed child references resolve within the mapping",
    "no exposed mapping nodes remain outside the active branch",
    "the share payload exposes a full graph and sequence; continue_conversation_url is recorded separately as an optional user-action URL, not a pagination cursor",
  ],
  graph_checks: graphChecks,
  continuation: {
    state: "not_present",
    mechanism: null,
    attempts: [],
    termination_reason: "source_terminal",
  },
  optional_action_url: data.continue_conversation_url ?? null,
  limitations: [
    "This is a verbatim captured public-share representation, not an authenticated account export.",
    "Derived messages and lineage are reconstructed from the preserved source artifact and remain explicitly reconstructed in FOSSIL.",
    "The optional continuation action was probed separately; its HTTP challenge/route behavior is not used to claim missing source nodes.",
  ],
};
fs.writeFileSync(outputPath, `${JSON.stringify(result, null, 2)}\n`, "utf8");
fs.writeFileSync(runtimeSpecsPath, `${JSON.stringify({
  conversation_id: `conv_shared_chat_completeness_run_20260914_local_003`,
  source_conversation_id: data.conversation_id,
  title: data.title,
  messages: runtimeMessages,
  lineage: {
    nodes: runtimeNodes,
    edges: runtimeNodes.slice(1).map((node, index) => ({
      edge_id: `le_src_${String(index + 1).padStart(4, "0")}`,
      source_node_id: runtimeNodes[index].node_id,
      target_node_id: node.node_id,
      relation_type: "leads_to",
    })),
    current_conclusion_refs: runtimeNodes.length ? [runtimeNodes.at(-1).node_id] : [],
  },
}, null, 2)}\n`, "utf8");
console.log(JSON.stringify({
  completeness: result.completeness,
  response_bytes: source.response_bytes,
  response_sha256: source.response_sha256,
  mapping_node_count: source.mapping_node_count,
  message_count: runtimeMessages.length,
  graph_checks: graphChecks,
  optional_action_url: result.optional_action_url,
}, null, 2));
