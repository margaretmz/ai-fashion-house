import React from 'react';
import {
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Typography,
  Chip,
  Box,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import CodeIcon from '@mui/icons-material/Code';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ChatBubbleIcon from '@mui/icons-material/ChatBubble';
import InfoIcon from '@mui/icons-material/Info';
import HelpIcon from '@mui/icons-material/Help';

const EVENT_DETAILS = {
  function_call: {
    color: 'info',
    icon: <CodeIcon fontSize="small" />,
  },
  function_response: {
    color: 'success',
    icon: <CheckCircleIcon fontSize="small" />,
  },
  text_response: {
    color: 'primary',
    icon: <ChatBubbleIcon fontSize="small" />,
  },
  log: {
    color: 'default',
    icon: <InfoIcon fontSize="small" />,
  },
};

export default function AgentLogViewer({ logs }) {
  const renderLogMessage = (log, index) => {
    const { event, data } = log;
    const eventDetail = EVENT_DETAILS[event] || {
      color: 'secondary',
      icon: <HelpIcon fontSize="small" />,
    };

    let summaryText = '';
    let detailContent = '';

    if (event === 'function_call') {
      summaryText = `🔧 Calling: ${data.function_name}`;
      detailContent = JSON.stringify(data.arguments, null, 2);
    } else if (event === 'function_response') {
      summaryText = `✅ Response from: ${data.function_name}`;
      detailContent = JSON.stringify(data.response, null, 2);
    } else if (event === 'text_response') {
      summaryText = `💬 ${data.author} says: ${data.text}`;
      detailContent = data.text;
    } else if (event === 'log') {
      summaryText = `📘 Log: ${data}`;
      detailContent = data;
    } else {
      summaryText = `🔍 Event: ${event}`;
      detailContent = JSON.stringify(data, null, 2);
    }

    return (
      <Accordion key={index} sx={{ mb: 1 }}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Box display="flex" alignItems="center" gap={1}>
            {eventDetail.icon}
            <Chip label={event} color={eventDetail.color} size="small" />
            <Typography variant="body2" sx={{ fontWeight: 500 }}>
              {summaryText}
            </Typography>
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <Typography
            variant="body2"
            sx={{
              whiteSpace: 'pre-wrap',
              fontFamily: 'monospace',
              color: 'text.secondary',
            }}
          >
            {detailContent}
          </Typography>
        </AccordionDetails>
      </Accordion>
    );
  };

  return (
    <Box>
      {logs.map((log, index) => renderLogMessage(log, index))}
    </Box>
  );
}
