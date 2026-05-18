/**
 * Split message content into { body, sources }.
 * Streaming-safe: strips "Sources:" from body the moment it appears,
 * then chips render progressively as each [label](url) completes.
 */
export function parseSources(content) {
  const splitIdx = content.search(/\*?\*?Sources:\*?\*?\s*/im);
  if (splitIdx === -1) return { body: content, sources: [] };

  const body = content.slice(0, splitIdx).trim();
  const sourcesText = content.slice(splitIdx);

  const sources = [];
  const linkRegex = /\[([^\]]+)\]\(([^)]+)\)/g;
  let m;
  while ((m = linkRegex.exec(sourcesText)) !== null) {
    sources.push({ label: m[1], url: m[2] });
  }

  return { body, sources };
}


export function groupMessages(messages) {
  const groups = [];
  let i = 0;
  while (i < messages.length) {
    if (messages[i].role === 'tool') {
      const toolBatch = [];
      while (i < messages.length && messages[i].role === 'tool') {
        toolBatch.push(messages[i]);
        i++;
      }
      groups.push({ type: 'tool_group', messages: toolBatch, key: toolBatch[0].id });
    } else {
      groups.push({ type: messages[i].role, message: messages[i], key: messages[i].id });
      i++;
    }
  }
  return groups;
}
