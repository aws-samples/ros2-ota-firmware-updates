import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import DeviceList from './components/DeviceList';
import UpdateDevice from './components/UpdateDevice';
import { Authenticator } from '@aws-amplify/ui-react';
import { fetchAuthSession } from '@aws-amplify/auth';
import UnauthorizedPage from './components/UnauthorizedPage';
import AppLayout from "@cloudscape-design/components/app-layout";
import TopNavigation from "@cloudscape-design/components/top-navigation";

// Apply dark mode styles
document.body.setAttribute('data-mode', 'dark');

function getNameFromEmail(email) {
    if (!email) return '';
    const name = email.split('@')[0];
    return name.charAt(0).toUpperCase() + name.slice(1);
}

function App() {
    const [isAuthorized, setIsAuthorized] = useState(null);
    const [error, setError] = useState(null);

    useEffect(() => {
        verifyUserGroup();
    }, []);

    async function verifyUserGroup() {
        try {
            const { accessToken } = (await fetchAuthSession()).tokens ?? {};
            
            if (!accessToken) {
                throw new Error('No access token found');
            }

            const groups = accessToken.payload['cognito:groups'] || [];

            if (groups.includes('ROS-OTA-AuthorizedUsers')) {
                setIsAuthorized(true);
            } else {
                setIsAuthorized(false);
            }
        } catch (err) {
            console.error('Error verifying user group:', err);
            setError(err.message);
            setIsAuthorized(false);
        }
    }
  
    if (isAuthorized === null) {
        return <div>Loading...</div>;
    }
  
    if (error) {
        return (
            <div>
                <h1>Error</h1>
                <p>{error}</p>
            </div>
        );
    }

    return (
        <Authenticator>
            {({ signOut, user }) => (
                <Router future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
                    <div className="awsui-dark-mode">
                        <TopNavigation
                            identity={{
                                href: "/",
                                title: "IoT Devices Management Home"
                            }}
                            utilities={[
                                {
                                    type: "button",
                                    text: `${getNameFromEmail(user.signInDetails?.loginId) || user.username}`,
                                    iconName: "user-profile"
                                },
                                {
                                    type: "button",
                                    text: "Sign out",
                                    onClick: signOut
                                }
                            ]}
                        />
                        <AppLayout
                            content={
                                isAuthorized ? (
                                    <Routes>
                                        <Route path="/" element={<DeviceList />} />
                                        <Route path="/update-device" element={<UpdateDevice />} />
                                        <Route path="*" element={<Navigate to="/" />} />
                                    </Routes>
                                ) : (
                                    <UnauthorizedPage />
                                )
                            }
                            toolsHide={true}
                            navigationHide={true}
                        />
                    </div>
                </Router>
            )}
        </Authenticator>
    );
}

export default App;
