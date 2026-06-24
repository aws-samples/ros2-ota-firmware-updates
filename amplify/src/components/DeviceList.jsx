import React, { useState, useEffect } from 'react';
import { fetchDevices } from './apiUtils';
import { useNavigate } from 'react-router-dom';
import Cards from "@cloudscape-design/components/cards";
import Box from "@cloudscape-design/components/box";
import SpaceBetween from "@cloudscape-design/components/space-between";
import Button from "@cloudscape-design/components/button";
import Header from "@cloudscape-design/components/header";
import Alert from "@cloudscape-design/components/alert";
import Spinner from "@cloudscape-design/components/spinner";

function DeviceList() {
    const navigate = useNavigate();
    const [devices, setDevices] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        async function loadDevices() {
            try {
                const response = await fetchDevices();
                setDevices(response);
            } catch (err) {
                setError('Failed to load devices. Please try again later.');
            } finally {
                setLoading(false);
            }
        }
        loadDevices();
    }, []);

    if (loading) {
        return (
            <Box margin="xxl" textAlign="center">
                <Spinner size="large" />
            </Box>
        );
    }

    if (error) {
        return (
            <Box margin="xxl">
                <Alert type="error">
                    {error}
                </Alert>
            </Box>
        );
    }

    return (
        <Box margin="xxl">
            <SpaceBetween size="xl">
                <Header
                    variant="h1"
                    description="Manage and update your IoT devices"
                >
                    IoT Device Management
                </Header>
                
                {devices.length === 0 ? (
                    <Alert type="info">
                        No devices found
                    </Alert>
                ) : (
                    <Cards
                        cardDefinition={{
                            header: item => item.device_name,
                            sections: [
                                {
                                    id: "version",
                                    header: "Current Version",
                                    content: item => item.current_version
                                }
                            ]
                        }}
                        cardsPerRow={[
                            { cards: 1, minWidth: 0 },
                            { cards: 2, minWidth: 500 },
                            { cards: 3, minWidth: 900 }
                        ]}
                        items={devices}
                        loadingText="Loading devices"
                        empty={
                            <Box textAlign="center" color="inherit">
                                <SpaceBetween size="m">
                                    <b>No devices</b>
                                    <Box variant="p" color="inherit">
                                        No devices to display.
                                    </Box>
                                </SpaceBetween>
                            </Box>
                        }
                        header={
                            <Header
                                counter={`(${devices.length})`}
                                actions={
                                    <Button
                                        variant="primary"
                                        onClick={() => navigate('/update-device')}
                                    >
                                        Update Device
                                    </Button>
                                }
                            >
                                Devices
                            </Header>
                        }
                    />
                )}
            </SpaceBetween>
        </Box>
    );
}

export default DeviceList;