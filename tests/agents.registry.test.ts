import { describe, expect, it } from "vitest";
import { pickSessionAgent } from "../src/agents/registry.js";
import type { Agent } from "../src/agents/types.js";

const agents: Agent[] = [
  {
    name: "agent-alpha",
    displayName: "Alpha",
    description: "",
    endpoint: "",
    protocols: ["agui"],
    available: true,
    domain: "general",
  },
  {
    name: "agent-sre",
    displayName: "SRE",
    description: "",
    endpoint: "",
    protocols: ["agui"],
    available: true,
    domain: "general",
  },
];

describe("pickSessionAgent", () => {
  it("uses explicit agent when requested", () => {
    expect(pickSessionAgent(agents, "agent-sre").name).toBe("agent-sre");
  });

  it("uses configured default before first in list", () => {
    expect(pickSessionAgent(agents, "default", "agent-sre").name).toBe("agent-sre");
    expect(pickSessionAgent(agents, undefined, "agent-sre").name).toBe("agent-sre");
  });

  it("falls back to first available when no default configured", () => {
    expect(pickSessionAgent(agents).name).toBe("agent-alpha");
  });

  it("falls back when configured default is not in list", () => {
    expect(pickSessionAgent(agents, "default", "missing-agent").name).toBe("agent-alpha");
  });
});
