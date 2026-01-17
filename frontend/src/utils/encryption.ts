/**
 * Encryption Utilities for Offline Data
 * Uses Web Crypto API for AES-GCM encryption of cached gallery data
 *
 * Security Features:
 * - AES-GCM 256-bit encryption
 * - Key stored in memory only (never persisted)
 * - PBKDF2 key derivation from user password/PIN
 * - Random IV for each encryption operation
 * - Authentication tag for data integrity
 *
 * T2-2: Create encryption utilities for cached data
 */

/**
 * Encryption algorithm and configuration
 */
const ALGORITHM = 'AES-GCM';
const KEY_LENGTH = 256; // bits
const IV_LENGTH = 12; // bytes (96 bits recommended for AES-GCM)
const SALT_LENGTH = 16; // bytes
const PBKDF2_ITERATIONS = 100000; // OWASP recommended minimum
const TAG_LENGTH = 128; // bits (authentication tag)

/**
 * In-memory storage for encryption key
 * Key is derived from user password/PIN and stored only in runtime memory
 * Never persisted to localStorage, IndexedDB, or any other storage
 */
let encryptionKey: CryptoKey | null = null;

/**
 * Encrypted data structure
 * Contains all information needed to decrypt: salt, IV, and ciphertext
 */
export interface EncryptedData {
  salt: string; // Base64-encoded salt used for key derivation
  iv: string; // Base64-encoded initialization vector
  ciphertext: string; // Base64-encoded encrypted data
  algorithm: string; // Algorithm identifier for version compatibility
}

/**
 * Check if Web Crypto API is available in this environment
 */
export function isCryptoAvailable(): boolean {
  try {
    return (
      typeof crypto !== 'undefined' &&
      typeof crypto.subtle !== 'undefined' &&
      typeof crypto.getRandomValues === 'function'
    );
  } catch {
    return false;
  }
}

/**
 * Generate random bytes using Web Crypto API
 * @param length - Number of bytes to generate
 * @returns Uint8Array of random bytes
 */
function getRandomBytes(length: number): Uint8Array {
  const bytes = new Uint8Array(length);
  crypto.getRandomValues(bytes);
  return bytes;
}

/**
 * Convert ArrayBuffer to Base64 string
 * @param buffer - ArrayBuffer to encode
 * @returns Base64-encoded string
 */
function arrayBufferToBase64(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer);
  let binary = '';
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary);
}

/**
 * Convert Base64 string to ArrayBuffer
 * @param base64 - Base64-encoded string
 * @returns ArrayBuffer
 */
function base64ToArrayBuffer(base64: string): ArrayBuffer {
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes.buffer;
}

/**
 * Derive encryption key from user password/PIN using PBKDF2
 * @param password - User-provided password or PIN
 * @param salt - Salt for key derivation (random for new keys, stored for decryption)
 * @returns CryptoKey suitable for AES-GCM encryption/decryption
 * @throws Error if Web Crypto API is not available or key derivation fails
 */
async function deriveKey(password: string, salt: Uint8Array): Promise<CryptoKey> {
  if (!isCryptoAvailable()) {
    throw new Error('Web Crypto API is not available in this environment');
  }

  try {
    // Convert password string to bytes
    const encoder = new TextEncoder();
    const passwordBytes = encoder.encode(password);

    // Import password as raw key material
    const keyMaterial = await crypto.subtle.importKey(
      'raw',
      passwordBytes,
      { name: 'PBKDF2' },
      false,
      ['deriveBits', 'deriveKey']
    );

    // Derive AES-GCM key using PBKDF2
    const key = await crypto.subtle.deriveKey(
      {
        name: 'PBKDF2',
        salt: salt,
        iterations: PBKDF2_ITERATIONS,
        hash: 'SHA-256',
      },
      keyMaterial,
      {
        name: ALGORITHM,
        length: KEY_LENGTH,
      },
      false, // Not extractable - cannot export key
      ['encrypt', 'decrypt']
    );

    return key;
  } catch (error) {
    throw new Error(
      `Key derivation failed: ${error instanceof Error ? error.message : 'Unknown error'}`
    );
  }
}

/**
 * Set encryption key in memory from user password/PIN
 * This should be called when user enables encryption or enters their PIN
 * @param password - User-provided password or PIN
 * @param salt - Optional salt for key derivation (omit to generate new salt)
 * @returns Base64-encoded salt (store this with encrypted data)
 * @throws Error if Web Crypto API is not available or key derivation fails
 */
export async function setEncryptionPassword(password: string, salt?: string): Promise<string> {
  const saltBytes = salt ? new Uint8Array(base64ToArrayBuffer(salt)) : getRandomBytes(SALT_LENGTH);
  encryptionKey = await deriveKey(password, saltBytes);
  return arrayBufferToBase64(saltBytes);
}

/**
 * Clear encryption key from memory
 * Call this when user logs out or disables encryption
 */
export function clearEncryptionKey(): void {
  encryptionKey = null;
}

/**
 * Check if encryption key is currently set in memory
 * @returns true if key is available, false otherwise
 */
export function hasEncryptionKey(): boolean {
  return encryptionKey !== null;
}

/**
 * Encrypt data using AES-GCM
 * @param data - Data to encrypt (string, object, or Blob)
 * @param password - Optional password to use (if not using stored key)
 * @returns EncryptedData structure containing salt, IV, and ciphertext
 * @throws Error if no encryption key is set or encryption fails
 */
export async function encrypt(
  data: string | Record<string, unknown> | Blob,
  password?: string
): Promise<EncryptedData> {
  if (!isCryptoAvailable()) {
    throw new Error('Web Crypto API is not available in this environment');
  }

  try {
    // Use provided password or existing key
    let key: CryptoKey;
    let salt: Uint8Array;

    if (password) {
      salt = getRandomBytes(SALT_LENGTH);
      key = await deriveKey(password, salt);
    } else {
      if (!encryptionKey) {
        throw new Error('No encryption key set. Call setEncryptionPassword() first.');
      }
      key = encryptionKey;
      // Generate new salt for this operation (not used, but kept for consistency)
      salt = getRandomBytes(SALT_LENGTH);
    }

    // Convert data to bytes
    let dataBytes: Uint8Array;
    if (data instanceof Blob) {
      const arrayBuffer = await data.arrayBuffer();
      dataBytes = new Uint8Array(arrayBuffer);
    } else if (typeof data === 'string') {
      const encoder = new TextEncoder();
      dataBytes = encoder.encode(data);
    } else {
      const encoder = new TextEncoder();
      dataBytes = encoder.encode(JSON.stringify(data));
    }

    // Generate random IV for this encryption operation
    const iv = getRandomBytes(IV_LENGTH);

    // Encrypt data
    const ciphertext = await crypto.subtle.encrypt(
      {
        name: ALGORITHM,
        iv: iv,
        tagLength: TAG_LENGTH,
      },
      key,
      dataBytes
    );

    return {
      salt: arrayBufferToBase64(salt),
      iv: arrayBufferToBase64(iv),
      ciphertext: arrayBufferToBase64(ciphertext),
      algorithm: `${ALGORITHM}-${KEY_LENGTH}`,
    };
  } catch (error) {
    throw new Error(
      `Encryption failed: ${error instanceof Error ? error.message : 'Unknown error'}`
    );
  }
}

/**
 * Decrypt data using AES-GCM
 * @param encryptedData - EncryptedData structure from encrypt()
 * @param password - Optional password to use (if not using stored key)
 * @param outputFormat - Desired output format ('string', 'json', 'blob')
 * @returns Decrypted data in requested format
 * @throws Error if no encryption key is set or decryption fails
 */
export async function decrypt<T = string>(
  encryptedData: EncryptedData,
  password?: string,
  outputFormat: 'string' | 'json' | 'blob' = 'string'
): Promise<T> {
  if (!isCryptoAvailable()) {
    throw new Error('Web Crypto API is not available in this environment');
  }

  try {
    // Use provided password or existing key
    let key: CryptoKey;

    if (password) {
      const salt = new Uint8Array(base64ToArrayBuffer(encryptedData.salt));
      key = await deriveKey(password, salt);
    } else {
      if (!encryptionKey) {
        throw new Error('No encryption key set. Call setEncryptionPassword() first.');
      }
      key = encryptionKey;
    }

    // Decode IV and ciphertext
    const iv = new Uint8Array(base64ToArrayBuffer(encryptedData.iv));
    const ciphertext = base64ToArrayBuffer(encryptedData.ciphertext);

    // Decrypt data
    const decryptedBuffer = await crypto.subtle.decrypt(
      {
        name: ALGORITHM,
        iv: iv,
        tagLength: TAG_LENGTH,
      },
      key,
      ciphertext
    );

    // Convert to requested format
    if (outputFormat === 'blob') {
      return new Blob([decryptedBuffer]) as T;
    }

    const decoder = new TextDecoder();
    const decryptedText = decoder.decode(decryptedBuffer);

    if (outputFormat === 'json') {
      return JSON.parse(decryptedText) as T;
    }

    return decryptedText as T;
  } catch (error) {
    throw new Error(
      `Decryption failed: ${error instanceof Error ? error.message : 'Unknown error'}`
    );
  }
}

/**
 * Encrypt a Blob (useful for photo files)
 * @param blob - Blob to encrypt
 * @param password - Optional password to use
 * @returns EncryptedData structure
 */
export async function encryptBlob(blob: Blob, password?: string): Promise<EncryptedData> {
  return encrypt(blob, password);
}

/**
 * Decrypt to a Blob (useful for photo files)
 * @param encryptedData - EncryptedData structure
 * @param password - Optional password to use
 * @returns Decrypted Blob
 */
export async function decryptBlob(
  encryptedData: EncryptedData,
  password?: string
): Promise<Blob> {
  return decrypt<Blob>(encryptedData, password, 'blob');
}

/**
 * Encrypt JSON-serializable object
 * @param obj - Object to encrypt
 * @param password - Optional password to use
 * @returns EncryptedData structure
 */
export async function encryptObject(
  obj: Record<string, unknown>,
  password?: string
): Promise<EncryptedData> {
  return encrypt(obj, password);
}

/**
 * Decrypt to JSON object
 * @param encryptedData - EncryptedData structure
 * @param password - Optional password to use
 * @returns Decrypted object
 */
export async function decryptObject<T = Record<string, unknown>>(
  encryptedData: EncryptedData,
  password?: string
): Promise<T> {
  return decrypt<T>(encryptedData, password, 'json');
}

/**
 * Generate a random encryption PIN (6 digits)
 * Useful for quick setup of encryption
 * @returns 6-digit PIN as string
 */
export function generatePIN(): string {
  const pin = Math.floor(100000 + Math.random() * 900000);
  return pin.toString();
}

/**
 * Validate password/PIN strength
 * @param password - Password or PIN to validate
 * @returns Validation result with strength assessment
 */
export function validatePasswordStrength(password: string): {
  valid: boolean;
  strength: 'weak' | 'medium' | 'strong';
  message: string;
} {
  const length = password.length;

  // Minimum length check
  if (length < 4) {
    return {
      valid: false,
      strength: 'weak',
      message: 'Password/PIN must be at least 4 characters',
    };
  }

  // PIN mode (numeric only)
  if (/^\d+$/.test(password)) {
    if (length < 6) {
      return {
        valid: false,
        strength: 'weak',
        message: 'Numeric PIN must be at least 6 digits',
      };
    }
    return {
      valid: true,
      strength: 'medium',
      message: 'PIN is valid',
    };
  }

  // Password mode
  if (length < 8) {
    return {
      valid: false,
      strength: 'weak',
      message: 'Password must be at least 8 characters',
    };
  }

  // Check for complexity
  const hasLower = /[a-z]/.test(password);
  const hasUpper = /[A-Z]/.test(password);
  const hasNumber = /\d/.test(password);
  const hasSpecial = /[!@#$%^&*()_+\-=[\]{};':"\\|,.<>/?]/.test(password);

  const complexityScore = [hasLower, hasUpper, hasNumber, hasSpecial].filter(Boolean).length;

  if (complexityScore < 2) {
    return {
      valid: true,
      strength: 'weak',
      message: 'Password is weak. Consider adding uppercase, numbers, or special characters.',
    };
  }

  if (complexityScore < 3 || length < 12) {
    return {
      valid: true,
      strength: 'medium',
      message: 'Password is acceptable',
    };
  }

  return {
    valid: true,
    strength: 'strong',
    message: 'Password is strong',
  };
}
