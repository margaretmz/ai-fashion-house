import * as React from 'react';
import HomeIcon from '@mui/icons-material/Home';
import InfoIcon from '@mui/icons-material/Info';
import { ReactRouterAppProvider } from '@toolpad/core/react-router';
import { Outlet } from 'react-router';
import {useEffect} from "react";
import {useWebSocketContext} from "./contexts/WebSocketContext/index.jsx";
import {useQueryClient} from "@tanstack/react-query";
import {createSvgIcon, createTheme, SvgIcon} from "@mui/material";
import AppIconSVG from './Assets/logo.svg'; // Adjust the path to your logo SVG


const NAVIGATION = [
  {
    kind: 'header',
    title: 'Main Navigation',
  },
  {
    title: 'Home',
    icon: <HomeIcon />,
  },
  {
    segment: 'about',
    title: 'Project Info',
    icon: <InfoIcon />,
  },
];

const BRANDING = {
  title: 'Fashion House',
    logo: <img src={AppIconSVG} />
};

const customTheme = createTheme({
  cssVariables: {
    colorSchemeSelector: 'data-toolpad-color-scheme',
  },
  colorSchemes: {
    light: {
      palette: {
        background: {
          default: '#F9F9FE',
          paper: '#EEEEF9',
        },
      },
    },
    dark: {
      palette: {
        background: {
          default: '#2A4364',
          paper: '#112E4D',
        },
      },
    },
  },
  breakpoints: {
    values: {
      xs: 0,
      sm: 600,
      md: 600,
      lg: 1200,
      xl: 1536,
    },
  },
});



export default function App() {

  const queryClient = useQueryClient();
  const { lastJsonMessage } = useWebSocketContext();

  // --- Update logs when WebSocket sends a message
  useEffect(() => {
    if (!lastJsonMessage) return;

    const { event, data } = lastJsonMessage;
    console.log('Received WebSocket message:', lastJsonMessage);

    if (['function_call', 'function_response', 'text_response'].includes(event)) {
      queryClient.setQueryData(['agentLogs'], (prev = []) => [...prev, { event, data }]);
    }
    if (event === 'artifact') {
      queryClient.setQueryData(['agentArtifacts'], (prev = []) => [...prev, data]);
    }
  }, [lastJsonMessage, queryClient]);



  return (
    <ReactRouterAppProvider navigation={NAVIGATION} branding={BRANDING} theme={customTheme}>
        <Outlet />
    </ReactRouterAppProvider>
  );
}
