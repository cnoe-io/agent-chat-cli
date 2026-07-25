/**
 * OIDC claim extraction from JWT access/id tokens (payload only; server validates).
 */

export interface OidcUserClaims {
  sub?: string;
  email?: string;
  name?: string;
  preferredUsername?: string;
}

export function decodeJwtPayload(jwt: string): Record<string, unknown> | null {
  const part = jwt.split(".")[1];
  if (!part) return null;
  try {
    return JSON.parse(Buffer.from(part, "base64url").toString()) as Record<string, unknown>;
  } catch {
    return null;
  }
}

export function oidcClaimsFromJwt(jwt: string): OidcUserClaims {
  const payload = decodeJwtPayload(jwt);
  if (!payload) return {};
  const email = typeof payload.email === "string" ? payload.email.trim() : undefined;
  const sub = typeof payload.sub === "string" ? payload.sub.trim() : undefined;
  const name = typeof payload.name === "string" ? payload.name.trim() : undefined;
  const preferredUsername =
    typeof payload.preferred_username === "string" ? payload.preferred_username.trim() : undefined;
  return { sub, email, name, preferredUsername };
}

export function mergeOidcClaims(...sources: OidcUserClaims[]): OidcUserClaims {
  const out: OidcUserClaims = {};
  for (const s of sources) {
    if (s.sub && !out.sub) out.sub = s.sub;
    if (s.email && !out.email) out.email = s.email;
    if (s.name && !out.name) out.name = s.name;
    if (s.preferredUsername && !out.preferredUsername) out.preferredUsername = s.preferredUsername;
  }
  return out;
}
