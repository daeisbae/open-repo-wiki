/**
 * Request signing utilities for API authentication.
 *
 * Uses HMAC-SHA256 to sign requests, preventing unauthorized API access.
 * The signing key is embedded at build time via environment variable.
 */

// Signing key from environment - embedded at build time
const SIGNING_KEY = import.meta.env.VITE_SIGNING_KEY || '';

/**
 * Convert Uint8Array to hex string.
 */
function bytesToHex(bytes: Uint8Array): string {
  return Array.from(bytes)
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('');
}

/**
 * Generate HMAC-SHA256 signature using Web Crypto API.
 *
 * @param message - Message to sign
 * @param key - Signing key
 * @returns Hex-encoded signature
 */
async function hmacSHA256(message: string, key: string): Promise<string> {
  const encoder = new TextEncoder();
  const keyData = encoder.encode(key);
  const messageData = encoder.encode(message);

  const cryptoKey = await crypto.subtle.importKey(
    'raw',
    keyData,
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign']
  );

  const signature = await crypto.subtle.sign('HMAC', cryptoKey, messageData);
  return bytesToHex(new Uint8Array(signature));
}

/**
 * Signature result with timestamp and hex-encoded signature.
 */
export interface SignatureResult {
  timestamp: string;
  signature: string;
}

/**
 * Generate request signature for API authentication.
 *
 * Creates an HMAC-SHA256 signature of "{timestamp}:{method}:{path}"
 * that the Lambda authorizer will validate.
 *
 * @param method - HTTP method (GET, POST, etc.)
 * @param path - Request path (e.g., /jobs)
 * @returns Timestamp and signature for headers
 */
export async function generateSignature(
  method: string,
  path: string
): Promise<SignatureResult> {
  const timestamp = Math.floor(Date.now() / 1000).toString();
  const message = `${timestamp}:${method}:${path}`;

  if (!SIGNING_KEY) {
    console.warn('VITE_SIGNING_KEY not set, request signing disabled');
    return { timestamp, signature: '' };
  }

  const signature = await hmacSHA256(message, SIGNING_KEY);
  return { timestamp, signature };
}

/**
 * Check if request signing is enabled (signing key is available).
 */
export function isSigningEnabled(): boolean {
  return Boolean(SIGNING_KEY);
}
