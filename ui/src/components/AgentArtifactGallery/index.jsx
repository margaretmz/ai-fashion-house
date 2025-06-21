import React, { useState, useMemo } from 'react';
import {
  Grid,
  Card,
  CardMedia,
  CardContent,
  Typography,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
  Box
} from '@mui/material';

import ImageIcon from '@mui/icons-material/Image';
import VideoLibraryIcon from '@mui/icons-material/VideoLibrary';
import TableChartIcon from '@mui/icons-material/TableChart';
import Papa from 'papaparse';

const columnsToShow = [
  'object_id',
  'object_name',
  'object_begin_date',
  'object_end_date',
  'distance',
  "gcs_url"
];


export default function AgentArtifactGallery({ artifacts }) {
  const [open, setOpen] = useState(false);
  const [selectedItem, setSelectedItem] = useState(null);

  const getMediaSource = (item) => {
    if (item.content && item.mime_type) {
      return `data:${item.mime_type};base64,${item.content}`;
    }
    return item.url;
  };

  const handleOpen = (item) => {
    setSelectedItem(item);
    setOpen(true);
  };

  const handleClose = () => {
    setOpen(false);
    setSelectedItem(null);
  };

  const getIcon = (mimeType) => {
    if (!mimeType) return null;
    if (mimeType.startsWith('image/')) return <ImageIcon fontSize="small" />;
    if (mimeType.startsWith('video/')) return <VideoLibraryIcon fontSize="small" />;
    if (mimeType === 'text/csv') return <TableChartIcon fontSize="small" />;
    return null;
  };

  const parsedCsv = useMemo(() => {
  if (selectedItem?.mime_type === 'text/csv' && selectedItem.content) {
    try {
      const csvString = atob(selectedItem.content);
      const result = Papa.parse(csvString, {
        header: true,
        skipEmptyLines: true,
      });
      return result.data;
    } catch (err) {
      console.error('Error parsing CSV with PapaParse:', err);
      return null;
    }
  }
  return null;
}, [selectedItem]);

  if (!artifacts || artifacts.length === 0) {
    return (
      <Typography variant="body1" color="text.secondary">
        No artifacts available yet.
      </Typography>
    );
  }

  return (
    <>
      <Grid container spacing={2}>
        {artifacts.map((item, index) => (
          <Grid item xs={12} sm={6} md={4} key={index}>
            <Card sx={{ maxWidth: '100%' }}>
              {item.mime_type?.startsWith('image/') && (
                <CardMedia
                  component="img"
                  height="300"
                  image={getMediaSource(item)}
                  alt={item.caption || 'Generated image'}
                  onClick={() => handleOpen(item)}
                  sx={{ cursor: 'pointer' }}
                />
              )}
              {item.mime_type?.startsWith('video/') && (
                <CardMedia
                  component="video"
                  controls
                  height="300"
                  src={getMediaSource(item)}
                  onClick={() => handleOpen(item)}
                  sx={{ cursor: 'pointer' }}
                />
              )}
              {item.mime_type === 'text/csv' && (
                <CardContent
                  sx={{ cursor: 'pointer' }}
                  onClick={() => handleOpen(item)}
                >
                  <Typography variant="body1" fontWeight="bold">
                    {item.filename}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Click to view CSV results
                  </Typography>
                </CardContent>
              )}

              <CardContent>
                <Box display="flex" alignItems="center" gap={1}>
                  {getIcon(item.mime_type)}
                  <Typography variant="body2" color="text.secondary">
                    {item.caption || item.filename || item.mime_type}
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Dialog open={open} onClose={handleClose} maxWidth="lg" fullWidth>
        <DialogTitle>{selectedItem?.filename || 'Preview'}</DialogTitle>
        <DialogContent dividers>
          {selectedItem?.mime_type?.startsWith('image/') && (
            <img
              src={getMediaSource(selectedItem)}
              alt={selectedItem.caption || 'Preview'}
              style={{ width: '100%', maxHeight: '70vh', objectFit: 'contain' }}
            />
          )}
          {selectedItem?.mime_type?.startsWith('video/') && (
            <video
              src={getMediaSource(selectedItem)}
              controls
              style={{ width: '100%', maxHeight: '70vh' }}
            />
          )}
          {selectedItem?.mime_type === 'text/csv' && parsedCsv && (
            <Table size="small">
            <TableHead>
              <TableRow>
                {columnsToShow.map((col, idx) => (
                  <TableCell key={idx}>{col}</TableCell>
                ))}
              </TableRow>
            </TableHead>
            <TableBody>
              {parsedCsv.map((row, rowIdx) => (
                <TableRow key={rowIdx}>
                  {columnsToShow.map((col, colIdx) => (
                    <TableCell key={colIdx}>
                      {row[col] !== undefined ? row[col] : ''}
                    </TableCell>
                  ))}
                </TableRow>
              ))}
            </TableBody>
          </Table>
          )}
        </DialogContent>
        <DialogActions>
          {selectedItem && (
            <a
              href={getMediaSource(selectedItem)}
              download={selectedItem.filename || 'download'}
              style={{ textDecoration: 'none' }}
            >
              <Button variant="contained" color="primary">
                Download
              </Button>
            </a>
          )}
          <Button onClick={handleClose} color="secondary">
            Close
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
}
