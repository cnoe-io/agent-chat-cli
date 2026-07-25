import { describe, expect, it } from "vitest";
import { oauthIssuerFromConfig } from "../src/platform/discovery.js";

describe("oauthIssuerFromConfig", () => {
  it("returns explicit issuer when present", () => {
    expect(
      oauthIssuerFromConfig({
        oauth: {
          issuer: "https://idp.example.com/realms/caipe/",
          token_endpoint: "https://other.example.com/token",
        },
      }),
    ).toBe("https://idp.example.com/realms/caipe");
  });

  it("derives issuer from Keycloak token endpoint", () => {
    expect(
      oauthIssuerFromConfig({
        oauth: {
          token_endpoint:
            "https://idp.example.com/realms/caipe/protocol/openid-connect/token",
          authorization_endpoint:
            "https://idp.example.com/realms/caipe/protocol/openid-connect/auth",
        },
      }),
    ).toBe("https://idp.example.com/realms/caipe");
  });

  it("returns undefined when oauth block is missing", () => {
    expect(oauthIssuerFromConfig({})).toBeUndefined();
  });
});
