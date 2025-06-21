import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { createBrowserRouter, RouterProvider} from "react-router";
import './index.css'
import App from './App.jsx'
import Layout from './layouts/Default/index.jsx';
import HomePage from './pages/Home/index.jsx';
import ProjectOverviewPage from "./pages/ProjectOverviewPage/index.jsx";
import {WebSocketProvider} from './contexts/WebSocketContext/index.jsx';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const queryClient = new QueryClient();

const router = createBrowserRouter([
  {
    Component: App, // root layout route
    children: [
      {
        path: '/',
        Component: Layout,
        children: [
          {
            path: '',
            Component: HomePage,
          },
          {
            path: 'about',
            Component: ProjectOverviewPage,
          },
        ],
      },
    ],
  },
]);

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <WebSocketProvider>
          <RouterProvider router={router} />
      </WebSocketProvider>
    </QueryClientProvider>
  </StrictMode>,
)
