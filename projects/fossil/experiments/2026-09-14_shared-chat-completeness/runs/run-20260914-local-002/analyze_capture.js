const fs = require("fs");
const crypto = require("crypto");

const sourcePath = process.argv[2];
const outputPath = process.argv[3];
if (!sourcePath || !outputPath) {
  throw new Error("usage: node analyze_capture.js SOURCE_RESPONSE OUTPUT_JSON");
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
const serializedStream = JSON.parse(enqueueArgument);
const values = JSON.parse(serializedStream);
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
  ) {
    return value;
  }
  if (Array.isArray(value)) {
    const result = [];
    cache.set(reference, result);
    for (const item of value) result.push(decode(item));
    return result;
  }
  const result = {};
  cache.set(reference, result);
  for (const [key, item] of Object.entries(value)) {
    result[decodeKey(key)] = decode(item);
  }
  return result;
}

const data = decode(0).loaderData["routes/share.$shareId.($action)"].serverResponse.data;
const entries = Object.entries(data.mapping);
const messageEntries = entries.filter(
  ([, node]) => node && node.message && typeof node.message === "object",
);
const roots = entries.filter(([, node]) => !node?.parent).map(([id]) => id);
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
const childRefs = new Set(
  entries.flatMap(([, node]) => (Array.isArray(node?.children) ? node.children : [])),
);
const unresolvedChildRefs = [...childRefs].filter((id) => !data.mapping[id]);
const messageIds = messageEntries
  .map(([, node]) => node.message?.id)
  .filter((id) => typeof id === "string");
const roles = {};
for (const [, node] of messageEntries) {
  const role = node.message?.author?.role ?? "unknown";
  roles[role] = (roles[role] ?? 0) + 1;
}

const result = {
  schema_version: "lab.shared-chat-completeness.v1",
  source_representation: {
    parser: "React Router streamed devalue graph decoder",
    response_bytes: raw.length,
    response_sha256: crypto.createHash("sha256").update(raw).digest("hex"),
    conversation_id: data.conversation_id,
    title: data.title,
    is_public: data.is_public,
    current_node: data.current_node,
    root_nodes: roots,
    mapping_node_count: entries.length,
    message_bearing_node_count: messageEntries.length,
    unique_message_id_count: new Set(messageIds).size,
    linear_conversation_count: Array.isArray(data.linear_conversation)
      ? data.linear_conversation.length
      : null,
    role_counts: roles,
    active_branch_node_count: activeBranch.length,
    active_branch_message_count: activeBranch.filter(
      (id) => data.mapping[id]?.message,
    ).length,
    non_active_exposed_node_count: entries.filter(([id]) => !activeSet.has(id)).length,
    unresolved_child_reference_count: unresolvedChildRefs.length,
    active_branch_first_node: activeBranch[0] ?? null,
    active_branch_last_node: activeBranch.at(-1) ?? null,
    discovered_node_ids: entries.map(([id]) => id).sort(),
    message_node_ids: messageEntries.map(([id]) => id).sort(),
    active_branch_node_ids: [...activeSet].sort(),
    non_active_exposed_node_ids: entries
      .filter(([id]) => !activeSet.has(id))
      .map(([id]) => id)
      .sort(),
    unresolved_refs: unresolvedChildRefs.map((id) => ({
      from_node_id: "unknown-parent",
      relation: "child",
      target_node_id: id,
    })),
    continuation_field: data.continue_conversation_url ?? null,
  },
  completeness: "incomplete",
  completeness_scope: "the mapping graph exposed in this public-share response is fully accounted for, but an exposed continuation URL could not be traversed",
  completeness_basis: [
    "source mapping enumerated",
    "source linear_conversation sequence counted",
    "root and current node recorded",
    "active parent traversal terminated at root",
    "all child references resolved",
    "no exposed non-active mapping nodes remained",
    "provider continuation URL was probed and returned HTTP 403 Cloudflare challenge",
  ],
  continuation_probe: {
    url: data.continue_conversation_url ?? null,
    http_status: 403,
    outcome: "blocked_by_provider_challenge",
    completeness_effect: "unresolved continuation prevents complete classification",
  },
  limitations: [
    "This is not an authenticated account export.",
    "Completeness does not claim access to provider data not exposed by this public-share response.",
  ],
};
fs.writeFileSync(outputPath, `${JSON.stringify(result, null, 2)}\n`, "utf8");
console.log(JSON.stringify(result, null, 2));
