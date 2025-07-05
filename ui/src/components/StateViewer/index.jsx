import React from 'react';
import {
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Typography,
  Chip,
  Box,
  IconButton,
  Tooltip,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import CodeIcon from '@mui/icons-material/Code';
import ReactMarkdown from 'react-markdown';

export default function StateViewer({ state }) {
  const handleCopy = (value) => {
    navigator.clipboard.writeText(value);
  };

  return (
    <Box>
      {Object.entries(state).map(([key, value], index) => (
        <Accordion key={index} sx={{ mb: 1 }}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Box display="flex" alignItems="center" gap={1} width="100%">
              <CodeIcon fontSize="small" />
              <Chip label="state" color="info" size="small" />
              <Typography variant="body2" sx={{ fontWeight: 500, flexGrow: 1 }}>
                {key}
              </Typography>
              <Tooltip title="Copy to clipboard">
                <IconButton
                  size="small"
                  onClick={(e) => {
                    e.stopPropagation(); // prevent accordion toggle
                    handleCopy(value);
                  }}
                >
                  <ContentCopyIcon fontSize="small" cursor="pointer" />
                </IconButton>
              </Tooltip>
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <Box >
              <ReactMarkdown>{value}</ReactMarkdown>
            </Box>
          </AccordionDetails>
        </Accordion>
      ))}
    </Box>
  );
}
