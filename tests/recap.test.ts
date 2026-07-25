import { describe, expect, it } from "vitest";
import { extractRecap } from "../src/chat/recap.js";

describe("extractRecap", () => {
  it("splits * Recap: line from body", () => {
    const { recap, body } = extractRecap("* Recap: Checked open issues\n\n## Results\n\nHello");
    expect(recap).toBe("Checked open issues");
    expect(body).toBe("## Results\n\nHello");
  });

  it("accepts Recap: without asterisk", () => {
    const { recap, body } = extractRecap("Recap: Done\nBody");
    expect(recap).toBe("Done");
    expect(body).toBe("Body");
  });

  it("returns null recap when absent", () => {
    const text = "No recap here\n\n**Bold**";
    expect(extractRecap(text)).toEqual({ recap: null, body: text });
  });
});
