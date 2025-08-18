import React from 'react';
import { Box, Chip, Typography } from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { useAuthStatus } from '../../hooks/useApi';

const ConnectionStatus = () => {
  const { data: authStatus, isLoading, error } = useAuthStatus();

  const getStatusConfig = () => {
    if (isLoading) {
      return {
        color: 'default',
        icon: <WarningIcon />,
        label: 'Checking...',
        description: 'Verifying connection',
        bgColor: 'rgba(245, 158, 11, 0.1)',
        borderColor: 'rgba(245, 158, 11, 0.3)',
      };
    }

    if (error) {
      return {
        color: 'error',
        icon: <ErrorIcon />,
        label: 'Disconnected',
        description: 'Backend not reachable',
        bgColor: 'rgba(239, 68, 68, 0.1)',
        borderColor: 'rgba(239, 68, 68, 0.3)',
      };
    }

    if (authStatus?.authenticated) {
      return {
        color: 'success',
        icon: <CheckCircleIcon />,
        label: 'Connected',
        description: 'Zerodha authenticated',
        bgColor: 'rgba(16, 185, 129, 0.1)',
        borderColor: 'rgba(16, 185, 129, 0.3)',
      };
    }

    return {
      color: 'warning',
      icon: <WarningIcon />,
      label: 'Not Authenticated',
      description: 'Please login to Zerodha',
      bgColor: 'rgba(245, 158, 11, 0.1)',
      borderColor: 'rgba(245, 158, 11, 0.3)',
    };
  };

  const statusConfig = getStatusConfig();

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <Box
        sx={{
          p: 2,
          borderRadius: 2,
          background: statusConfig.bgColor,
          border: `1px solid ${statusConfig.borderColor}`,
          backdropFilter: 'blur(10px)',
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
          <Box sx={{ mr: 1, color: statusConfig.color === 'success' ? '#10B981' : statusConfig.color === 'error' ? '#EF4444' : '#F59E0B' }}>
            {statusConfig.icon}
          </Box>
          <Typography
            variant="body2"
            sx={{
              fontWeight: 600,
              color: 'white',
              fontSize: '0.875rem',
            }}
          >
            {statusConfig.label}
          </Typography>
        </Box>
        <Typography
          variant="caption"
          sx={{
            color: 'rgba(255, 255, 255, 0.7)',
            fontSize: '0.75rem',
            display: 'block',
          }}
        >
          {statusConfig.description}
        </Typography>
        
        {authStatus?.profile_name && (
          <Chip
            label={authStatus.profile_name}
            size="small"
            sx={{
              mt: 1,
              height: 20,
              fontSize: '0.65rem',
              background: 'rgba(255, 255, 255, 0.1)',
              color: 'white',
              border: '1px solid rgba(255, 255, 255, 0.2)',
            }}
          />
        )}
      </Box>
    </motion.div>
  );
};

export default ConnectionStatus;