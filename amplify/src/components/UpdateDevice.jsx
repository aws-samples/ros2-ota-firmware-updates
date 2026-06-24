import React, { useState, useEffect } from 'react';
import { fetchDevices, fetchFirmwareVersions, updateDeviceFirmware } from './apiUtils'; 
import { useNavigate } from 'react-router-dom';
import Form from "@cloudscape-design/components/form";
import SpaceBetween from "@cloudscape-design/components/space-between";
import Button from "@cloudscape-design/components/button";
import Header from "@cloudscape-design/components/header";
import FormField from "@cloudscape-design/components/form-field";
import Input from "@cloudscape-design/components/input";
import Container from "@cloudscape-design/components/container";
import Alert from "@cloudscape-design/components/alert";
import Box from "@cloudscape-design/components/box";
import Select from "@cloudscape-design/components/select";
import Flashbar from "@cloudscape-design/components/flashbar";

function UpdateDevice() {
    const navigate = useNavigate();
    const [selectedDevice, setSelectedDevice] = useState('');
    const [devices, setDevices] = useState([]);
    const [firmwareVersions, setFirmwareVersions] = useState([]);
    const [filteredFirmwareVersions, setFilteredFirmwareVersions] = useState([]);
    const [newFirmwareVersion, setNewFirmwareVersion] = useState('');
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(false);
    const [updateStatus, setUpdateStatus] = useState(null);

    useEffect(() => {
        async function loadData() {
            try {
                const [devicesData, versionsData] = await Promise.all([
                    fetchDevices(),
                    fetchFirmwareVersions()
                ]);
                setDevices(devicesData);
                setFirmwareVersions(versionsData);
            } catch (error) {
                console.error('Failed to fetch data:', error);
                setError('Failed to load devices and firmware versions. Please try again.');
            }
        }
        loadData();
    }, []);

    const handleDeviceChange = ({ detail }) => {
        const deviceName = detail.selectedOption?.value;
        setSelectedDevice(deviceName);
        
        if (deviceName) {
            const device = devices.find(d => d.device_name === deviceName);
            if (device) {
                const availableVersions = firmwareVersions.filter(v => 
                    v !== device.current_version
                );
                setFilteredFirmwareVersions(availableVersions);
            }
        } else {
            setFilteredFirmwareVersions([]);
        }
    };

    const handleVersionChange = ({ detail }) => {
        setNewFirmwareVersion(detail.selectedOption?.value || '');
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        try {
            // Add your update logic here
            console.log('Updating device:', { selectedDevice, newFirmwareVersion });
            
            // Show update in progress message
            setUpdateStatus({
                type: 'info',
                loading: true,
                content: `Creating Firmware Update Job for ${selectedDevice} to version ${newFirmwareVersion}...`
            });

            // Simulate update process (replace with actual update logic)
            await updateDeviceFirmware(selectedDevice, newFirmwareVersion);

            // Show success message
            setUpdateStatus({
                type: 'success',
                content: `Successfully created Firmware Update Job for ${selectedDevice} to version ${newFirmwareVersion}!`,
                dismissible: true
            });

            // Wait a moment before redirecting
            setTimeout(() => {
                navigate('/');
            }, 3000);

        } catch (err) {
            setError('Failed to update device. Please try again.');
            setUpdateStatus(null);
            setLoading(false);
        }
    };

    const formFields = [
        error && (
            <Alert type="error" key="error-alert">
                {error}
            </Alert>
        ),
        <FormField
            key="device-select"
            label="Device Name"
            description="Select the name of the device to update"
            constraintText="Required"
        >
            <Select
                selectedOption={
                    selectedDevice 
                        ? { value: selectedDevice, label: selectedDevice }
                        : null
                }
                onChange={handleDeviceChange}
                options={devices.map(device => ({ 
                    value: device.device_name, 
                    label: device.device_name 
                }))}
                placeholder="Choose a device"
                ariaLabel="Select device"
            />
        </FormField>,
        selectedDevice && (
            <FormField
                key="current-version"
                label="Current Version"
                description="Current firmware version of the device"
            >
                <Input
                    value={devices.find(d => d.device_name === selectedDevice)?.current_version || ''}
                    disabled={true}
                    ariaLabel="Current firmware version"
                />
            </FormField>
        ),
        <FormField
            key="firmware-select"
            label="Firmware Version"
            description="Select the new firmware version"
            constraintText="Required"
        >
            <Select
                selectedOption={
                    newFirmwareVersion 
                        ? { value: newFirmwareVersion, label: newFirmwareVersion }
                        : null
                }
                onChange={handleVersionChange}
                options={filteredFirmwareVersions.map(version => ({ 
                    value: version, 
                    label: version 
                }))}
                disabled={!selectedDevice}
                placeholder="Choose a firmware version"
                ariaLabel="Select firmware version"
            />
        </FormField>
    ].filter(Boolean);

    return (
        <Box margin="xxl">
            <SpaceBetween size="xl">
                {updateStatus && (
                    <Flashbar
                        items={[{
                            type: updateStatus.type,
                            loading: updateStatus.loading,
                            content: updateStatus.content,
                            dismissible: updateStatus.dismissible,
                            onDismiss: () => setUpdateStatus(null)
                        }]}
                    />
                )}

                <Header
                    variant="h1"
                    description="Update firmware version for your IoT device"
                >
                    Update Device
                </Header>

                <Container>
                    <form onSubmit={handleSubmit} noValidate>
                        <Form
                            actions={
                                <SpaceBetween direction="horizontal" size="xs">
                                    <Button 
                                        key="cancel"
                                        formAction="none"
                                        variant="link"
                                        onClick={() => navigate('/')}
                                        disabled={loading}
                                    >
                                        Cancel
                                    </Button>
                                    <Button 
                                        key="submit"
                                        variant="primary"
                                        loading={loading}
                                        type="submit"
                                        disabled={!selectedDevice || !newFirmwareVersion || loading}
                                    >
                                        Update Device
                                    </Button>
                                </SpaceBetween>
                            }
                            errorText={error}
                        >
                            <SpaceBetween size="l">
                                {formFields}
                            </SpaceBetween>
                        </Form>
                    </form>
                </Container>
            </SpaceBetween>
        </Box>
    );
}

export default UpdateDevice;
