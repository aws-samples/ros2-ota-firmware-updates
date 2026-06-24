import { Amplify } from 'aws-amplify';
import outputs from './amplify_outputs.json';
import { Authenticator } from '@aws-amplify/ui-react';
import '@aws-amplify/ui-react/styles.css';
import App from './App';
import React from 'react';
import ReactDOM from 'react-dom/client';

Amplify.configure({
    Auth: {
        Cognito: 
        {
            identityPoolId: outputs.auth.identity_pool_id,
            allowGuestAccess: outputs.auth.unauthenticated_identities_enabled,
            userPoolClientId: outputs.auth.user_pool_client_id,
            userPoolId: outputs.auth.user_pool_id,
            signUpAttributes: ['email'],
            loginWith: {email: true },
            mandatorySignIn: true,
        }
    },
    API: {
      REST: {
        ['DeviceApi']: {
          endpoint: outputs.custom.api_endpoint,
          region: "us-east-1",
        },
      },
    },
  });

// Add global styles to body
document.body.style.backgroundColor = '#1a1a1a';
document.body.style.color = '#ffffff';
document.body.style.margin = '0';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
    <Authenticator>
      <React.StrictMode>
          <App />
      </React.StrictMode>
    </Authenticator>
);

