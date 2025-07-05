import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Box,
  Button,
  CircularProgress,
  Container,
  Paper,
  Stack,
  Tab,
  Tabs,
  TextField,
  Typography,
} from '@mui/material';
import BoldIcon from '@mui/icons-material/Bolt';
import { ReadyState } from 'react-use-websocket';
import { useQuery, useQueryClient } from '@tanstack/react-query';

import AgentLogViewer from '../../components/AgentLogViewer/index.jsx';
import AgentArtifactGallery from '../../components/AgentArtifactGallery/index.jsx';

import { useWebSocketContext } from '../../contexts/WebSocketContext/index.jsx';
import StateViewer from "../../components/StateViewer/index.jsx";

export default function HomePage() {
  const queryClient = useQueryClient();
  const { sendJsonMessage, lastJsonMessage, readyState } = useWebSocketContext();

  const [loading, setLoading] = useState(false);
  const [tab, setTab] = useState(0);

  const initialPrompt =
    'I’m looking for inspiration for a red Victorian dress with lace and floral patterns, suitable for a royal ball in the 1800s.';

  // Load persisted prompt from cache
  const { data: cachedPrompt = initialPrompt } = useQuery({
    queryKey: ['agentPrompt'],
    queryFn: () => initialPrompt,
    staleTime: Infinity,
    initialData: initialPrompt,
  });

  const [inputValue, setInputValue] = useState(cachedPrompt);

  // Sync prompt to cache after delay
  useEffect(() => {
    const timeout = setTimeout(() => {
      queryClient.setQueryData(['agentPrompt'], inputValue);
    }, 300);
    return () => clearTimeout(timeout);
  }, [inputValue, queryClient]);

  // Load logs and artifacts
  const { data: agentLogs = [] } = useQuery({
    queryKey: ['agentLogs'],
    queryFn: () => [],
    staleTime: Infinity,
    initialData: [],
  });

    const { data: agentState = {} } = useQuery({
    queryKey: ['agentState'],
    queryFn: () => ({}),
    staleTime: Infinity,
    initialData: {},
    });

  const { data: agentArtifacts = [] } = useQuery({
    queryKey: ['agentArtifacts'],
    queryFn: () => [],
    staleTime: Infinity,
    initialData: [],
  });

  // Handle WebSocket messages
  useEffect(() => {
    if (!lastJsonMessage) return;
    const { event, data } = lastJsonMessage;
    if (['function_call', 'function_response', 'text_response'].includes(event)) {
      setLoading(!data?.is_final);
    }
  }, [lastJsonMessage]);

  const isWsReady = useMemo(() => readyState === ReadyState.OPEN, [readyState]);

  const handleClick = useCallback(() => {
    if (!isWsReady) {
      console.error('WebSocket is not open. Current state:', readyState);
      return;
    }

    queryClient.setQueryData(['agentPrompt'], inputValue);
    queryClient.setQueryData(['agentLogs'], []);
    queryClient.setQueryData(['agentState'], {});
    queryClient.setQueryData(['agentArtifacts'], []);
    setLoading(true);

    sendJsonMessage({
      event: 'start_design',
      data: { prompt: inputValue },
    });
  }, [inputValue, isWsReady, queryClient, sendJsonMessage, readyState]);

  return (
    <div style={{
          width: '100%',
          minHeight: '100vh',  // ✅ Ensures full screen height
          overflow: 'auto',
          background: 'linear-gradient(-45deg, #1e3c72, #2a5298, #2980b9, #6dd5fa)',
          backgroundSize: '400% 400%',  // ✅ Required for animated flow effect
          animation: 'gradientFlow 18s ease infinite',
        }}>
      <style>{`
        @keyframes gradientFlow {
          0% { background-position: 0% 50%; }
          50% { background-position: 100% 50%; }
          100% { background-position: 0% 50%; }
        }
      `}</style>

      <Container
           sx={{
            flex: 1,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            px: 2,
          }}
      >
        <Paper
          elevation={3}
          sx={{
            p: 4,
            my: 10,
            borderRadius: 4,
            maxWidth: 900,
            width: '100%',
          }}
        >
          <Stack spacing={4} alignItems="center">
            <Typography variant="h4" align="center">
              Welcome to AI Fashion House
            </Typography>
            <Typography variant="subtitle1" align="center" color="text.secondary">
              Let’s bring your dream dress to life. What would you like to design today?
            </Typography>

            <TextField
              label="Describe your fashion idea"
              multiline
              rows={4}
              variant="outlined"
              fullWidth
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
            />

            <Button
              variant="contained"
              endIcon={!loading ? <BoldIcon /> : <CircularProgress size={20} />}
              onClick={handleClick}
              disabled={loading || !isWsReady}
              sx={{ py: 1.5, px: 4, minWidth: 200 }}
            >
              {loading ? 'Agents are working...' : 'Start Design'}
            </Button>

            {agentLogs.length > 0 && (
              <Box sx={{ width: '100%' }}>
                <Tabs value={tab} onChange={(_, newValue) => setTab(newValue)} centered>
                  <Tab label="Agents Log" />
                  <Tab label="State Log" disabled={Object.keys(agentState).length === 0} />
                  <Tab label="Artifacts Gallery" disabled={agentArtifacts.length === 0} />
                </Tabs>

                <Box sx={{ mt: 3 }}>
                  {tab === 0 && <AgentLogViewer logs={agentLogs} />}
                {tab === 1 && <StateViewer state={agentState} />}
                  {tab === 2 && <AgentArtifactGallery artifacts={agentArtifacts} />}
                </Box>
              </Box>
            )}
          </Stack>
        </Paper>
      </Container>
    </div>
  );
}
