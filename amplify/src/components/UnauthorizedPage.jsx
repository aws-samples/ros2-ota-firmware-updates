import React from 'react';
import Alert from "@cloudscape-design/components/alert";
import Box from "@cloudscape-design/components/box";
import SpaceBetween from "@cloudscape-design/components/space-between";

export default function UnauthorizedPage() {
  return (
    <Box margin="xxl">
      <SpaceBetween size="l">
        <Alert
          type="error"
          header="Access Denied"
        >
          You do not have the required permissions to access this page. 
          Please contact an administrator to request access to the IoT Device Management System.
        </Alert>
      </SpaceBetween>
    </Box>
  );
}
