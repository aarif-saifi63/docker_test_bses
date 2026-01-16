
import forge from 'node-forge';
import apiClient from '../services/apiClient';

// In-memory cache for public key
let cachedPublicKey = null;
let publicKeyFetchPromise = null;


export const fetchPublicKey = async () => {
  // Return cached key if available
  if (cachedPublicKey) {
    return cachedPublicKey;
  }


  if (publicKeyFetchPromise) {
    return publicKeyFetchPromise;
  }


  publicKeyFetchPromise = (async () => {
    try {
      // Using apiClient to leverage existing axios configuration
      // Endpoint: GET /rsa/public-key
      const response = await apiClient.get('/rsa/public-key');

      // Expected response format: { status: true, public_key: "..." }
      if (response.status && response.public_key) {
        cachedPublicKey = response.public_key;
        return cachedPublicKey;
      } else {
        return null;
      }
    } catch (error) {
      return null;
    } finally {
      publicKeyFetchPromise = null;
    }
  })();

  return publicKeyFetchPromise;
};

/**
 * Encrypts credentials using RSA public key
 * @param {string} email - User email
 * @param {string} password - User password
 * @returns {Promise<{payload: object, isEncrypted: boolean}>}
 */
export const encryptCredentials = async (email, password) => {
  try {
    // Fetch public key
    const publicKey = await fetchPublicKey();

    if (!publicKey) {
      return {
        payload: { email_id: email, password },
        isEncrypted: false,
      };
    }


    // Create credentials JSON object (matching Python backend)
    const credentialsJson = JSON.stringify({
      email_id: email,
      password: password,
    });

    // Convert PEM public key to forge format
    const publicKeyForge = forge.pki.publicKeyFromPem(publicKey);

    // Encrypt using OAEP padding (matches Python cryptography library)
    const encryptedBytes = publicKeyForge.encrypt(
      credentialsJson,
      'RSA-OAEP',
      {
        md: forge.md.sha256.create(),
        mgf1: {
          md: forge.md.sha256.create()
        }
      }
    );

    // Convert to base64
    const encryptedPayload = forge.util.encode64(encryptedBytes);

    if (!encryptedPayload) {
      return {
        payload: { email_id: email, password },
        isEncrypted: false,
      };
    }

    return {
      payload: { encrypted_payload: encryptedPayload },
      isEncrypted: true,
    };
  } catch (error) {
    // Fallback to plain credentials on any error
    return {
      payload: { email_id: email, password },
      isEncrypted: false,
    };
  }
};

/**
 * Clears the cached public key (useful for testing or key rotation)
 */
export const clearPublicKeyCache = () => {
  cachedPublicKey = null;
  publicKeyFetchPromise = null;
};

/**
 * Test function to manually encrypt and see the result
 * Usage in browser console:
 * import { testEncryption } from './utils/rsaEncryption'
 * await testEncryption('test@email.com', 'password123')
 */
export const testEncryption = async (email, password) => {
  const publicKey = await fetchPublicKey();

  const credentialsJson = JSON.stringify({ email_id: email, password: password });

  const publicKeyForge = forge.pki.publicKeyFromPem(publicKey);
  const encryptedBytes = publicKeyForge.encrypt(
    credentialsJson,
    'RSA-OAEP',
    {
      md: forge.md.sha256.create(),
      mgf1: { md: forge.md.sha256.create() }
    }
  );
  const encryptedPayload = forge.util.encode64(encryptedBytes);

  return encryptedPayload;
};
