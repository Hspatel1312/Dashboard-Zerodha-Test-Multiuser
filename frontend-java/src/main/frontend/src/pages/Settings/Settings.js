import React from 'react';
import { Box, Typography } from '@mui/material';

const Settings = () => {
  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Settings
      </Typography>
      <Typography variant="body1">
        Application settings will be implemented here.
      </Typography>
    </Box>
  );
};

export default Settings;