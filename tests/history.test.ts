/**
 * Session file persistence (conversation id + resume fields).
 */

import { existsSync, rmSync } from "node:fs";
import { join } from "node:path";
import { afterEach, describe, expect, it, vi } from "vitest";
import {
  createSession,
  loadSession,
  patchSessionConversationId,
  saveSession,
} from "../src/chat/history";

const TEST_HOME = join(process.cwd(), ".test-sessions-home");

vi.mock("../src/platform/config.js", () => ({
  sessionsDir: () => join(TEST_HOME, "sessions"),
}));

describe("session persistence", () => {
  afterEach(() => {
    if (existsSync(TEST_HOME)) rmSync(TEST_HOME, { recursive: true, force: true });
  });

  it("round-trips conversationId on save/load", () => {
    const session = createSession({
      agentName: "default",
      workingDir: "/tmp",
      conversationId: "server-conv-abc",
    });
    session.messages.push({
      role: "user",
      content: "hi",
      timestamp: new Date().toISOString(),
      agentName: "default",
      tokenCount: null,
    });
    saveSession(session);
    const loaded = loadSession(session.sessionId);
    expect(loaded?.conversationId).toBe("server-conv-abc");
    expect(loaded?.messages).toHaveLength(1);
  });

  it("patchSessionConversationId updates existing file", () => {
    const session = createSession({ agentName: "default", workingDir: "/tmp" });
    saveSession(session);
    patchSessionConversationId(session.sessionId, "new-id");
    const loaded = loadSession(session.sessionId);
    expect(loaded?.conversationId).toBe("new-id");
  });
});
