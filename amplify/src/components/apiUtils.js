import { get, post } from 'aws-amplify/api';
import { fetchAuthSession } from 'aws-amplify/auth';

async function getIdToken() {
    try {
      const session = await fetchAuthSession();
      return session.tokens.idToken.toString();
    } catch (error) {
      console.error('Error getting auth session:', error);
      throw error;
    }
  }
  
export async function fetchDevices() {
    try {
        const token = await getIdToken();
        const restOperation = get({ 
            apiName: 'DeviceApi', 
            path: '/devices',
            options: {
                headers: {
                    Authorization: `Bearer ${token}`
                }
            }
        });
        
        const { body } = await restOperation.response;
        const devices = await body.json();
        
        return devices;
    } catch (error) {
        console.error('Failed to fetch devices:', error);
        return [];
    }
}

export async function fetchFirmwareVersions() {
    try {
        const token = await getIdToken();
        const restOperation = get({ 
            apiName: 'DeviceApi', 
            path: '/versions',
            options: {
                headers: {
                    Authorization: `Bearer ${token}`
                }
            }
        });
        const { body }  = await restOperation.response;
        const versions = await body.json();
        return versions;
    } catch (error) {
        console.error('Failed to fetch versions:', error);
        throw error;
    }
}

// Function to update a device's firmware
export async function updateDeviceFirmware(deviceName, newVersion) {
    try {
        const token = await getIdToken();
        const restOperation = post({
            apiName: 'DeviceApi', 
            path: '/update-device',
            options: {
                body: JSON.stringify({
                    device_name: deviceName,
                    new_version: newVersion
                }),
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${token}`
                }
            }
        });
        const response = await restOperation.response;
        return response;
    } catch (error) {
        console.error('Failed to update device:', error);
        throw new Error('Failed to update device');
    }
}