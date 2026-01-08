/**
 * Device ID utilities for multi-tenant isolation
 */

const DEVICE_ID_KEY = 'banana-slides-device-id';

/**
 * Generate a unique device ID
 */
function generateDeviceId(): string {
  // 使用时间戳 + 随机数生成唯一ID
  const timestamp = Date.now().toString(36);
  const randomStr = Math.random().toString(36).substring(2, 15);
  return `device-${timestamp}-${randomStr}`;
}

/**
 * Get or create device ID from localStorage
 */
export function getDeviceId(): string {
  let deviceId = localStorage.getItem(DEVICE_ID_KEY);

  if (!deviceId) {
    deviceId = generateDeviceId();
    localStorage.setItem(DEVICE_ID_KEY, deviceId);
    console.log('Generated new device ID:', deviceId);
  }

  return deviceId;
}

/**
 * Clear device ID (for testing purposes)
 */
export function clearDeviceId(): void {
  localStorage.removeItem(DEVICE_ID_KEY);
}
