import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  Stepper,
  Step,
  StepLabel,
  Paper,
  Chip,
  IconButton,
  Tooltip,
  Alert,
  CircularProgress,
} from '@mui/material';
import {
  Launch as LaunchIcon,
  ContentCopy as ContentCopyIcon,
  CheckCircle as CheckCircleIcon,
  Security as SecurityIcon,
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import toast from 'react-hot-toast';
import { useZerodhaLoginMutation, useTokenExchangeMutation, useAutoAuthenticateMutation } from '../../hooks/useApi';

const steps = ['Generate Login URL', 'Login to Zerodha', 'Enter Request Token'];

const AuthenticationFlow = () => {
  const [activeStep, setActiveStep] = useState(0);
  const [loginUrl, setLoginUrl] = useState('');
  const [requestToken, setRequestToken] = useState('');

  const loginMutation = useZerodhaLoginMutation();
  const tokenMutation = useTokenExchangeMutation();
  const autoAuthMutation = useAutoAuthenticateMutation();

  const handleGenerateLoginUrl = () => {
    loginMutation.mutate(undefined, {
      onSuccess: (data) => {
        if (data.success) {
          setLoginUrl(data.login_url);
          setActiveStep(1);
        }
      },
    });
  };

  const handleCopyUrl = () => {
    navigator.clipboard.writeText(loginUrl);
    toast.success('Login URL copied to clipboard');
  };

  const handleAutoAuthenticate = () => {
    autoAuthMutation.mutate(undefined, {
      onSuccess: (data) => {
        if (data.success) {
          setActiveStep(3);
          // The page will automatically refresh due to auth status change
        }
      },
    });
  };

  const handleTokenSubmit = () => {
    if (!requestToken.trim()) {
      toast.error('Please enter the request token');
      return;
    }

    tokenMutation.mutate(requestToken, {
      onSuccess: (data) => {
        if (data.success) {
          setActiveStep(2);
          // The page will automatically refresh due to auth status change
        }
      },
    });
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.8 }}
    >
      <Box sx={{ textAlign: 'center', mb: 6 }}>
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: 0.2, duration: 0.6 }}
        >
          <SecurityIcon
            sx={{
              fontSize: 80,
              color: '#007AFF',
              mb: 3,
              filter: 'drop-shadow(0 0 20px rgba(0, 122, 255, 0.3))',
            }}
          />
        </motion.div>

        <Typography
          variant="h2"
          sx={{
            fontWeight: 800,
            mb: 2,
            background: 'linear-gradient(135deg, #007AFF 0%, #5856D6 100%)',
            backgroundClip: 'text',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
          }}
        >
          Connect to Zerodha
        </Typography>

        <Typography
          variant="h6"
          sx={{
            color: 'rgba(255, 255, 255, 0.7)',
            maxWidth: 600,
            mx: 'auto',
            lineHeight: 1.6,
          }}
        >
          Securely connect your Zerodha account to access live market data and portfolio management features
        </Typography>
      </Box>

      {/* Auto Connect Section */}
      <Paper
        sx={{
          p: 4,
          mb: 4,
          background: 'rgba(16, 185, 129, 0.1)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(16, 185, 129, 0.3)',
          textAlign: 'center',
        }}
      >
        <Typography
          variant="h5"
          sx={{
            mb: 2,
            fontWeight: 600,
            color: '#10B981',
          }}
        >
          🚀 Quick Connect (Recommended)
        </Typography>
        
        <Typography
          variant="body1"
          sx={{
            mb: 3,
            color: 'rgba(255, 255, 255, 0.8)',
            maxWidth: 500,
            mx: 'auto',
          }}
        >
          Use automatic authentication with saved credentials - no manual token required!
        </Typography>

        <Button
          variant="contained"
          size="large"
          onClick={handleAutoAuthenticate}
          disabled={autoAuthMutation.isLoading}
          sx={{
            py: 2,
            px: 4,
            background: 'linear-gradient(135deg, #10B981 0%, #059669 100%)',
            fontSize: '1.1rem',
            fontWeight: 600,
            '&:hover': {
              background: 'linear-gradient(135deg, #059669 0%, #047857 100%)',
            },
          }}
        >
          {autoAuthMutation.isLoading ? (
            <>
              <CircularProgress size={20} color="inherit" sx={{ mr: 1 }} />
              Connecting...
            </>
          ) : (
            'Auto Connect to Zerodha'
          )}
        </Button>

        <Typography
          variant="body2"
          sx={{
            mt: 2,
            color: 'rgba(255, 255, 255, 0.6)',
          }}
        >
          Or use manual authentication below if auto-connect doesn't work
        </Typography>
      </Paper>

      {/* Manual Authentication Stepper */}
      <Paper
        sx={{
          p: 4,
          mb: 4,
          background: 'rgba(28, 28, 30, 0.8)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
        }}
      >
        <Typography
          variant="h6"
          sx={{
            mb: 3,
            textAlign: 'center',
            color: 'rgba(255, 255, 255, 0.7)',
          }}
        >
          Manual Authentication Steps
        </Typography>
        
        <Stepper activeStep={activeStep} alternativeLabel>
          {steps.map((label, index) => (
            <Step key={label}>
              <StepLabel
                sx={{
                  '& .MuiStepLabel-label': {
                    color: 'rgba(255, 255, 255, 0.7)',
                    '&.Mui-active': {
                      color: '#007AFF',
                    },
                    '&.Mui-completed': {
                      color: '#10B981',
                    },
                  },
                  '& .MuiStepIcon-root': {
                    color: 'rgba(255, 255, 255, 0.3)',
                    '&.Mui-active': {
                      color: '#007AFF',
                    },
                    '&.Mui-completed': {
                      color: '#10B981',
                    },
                  },
                }}
              >
                {label}
              </StepLabel>
            </Step>
          ))}
        </Stepper>
      </Paper>

      {/* Step Content */}
      <Card
        sx={{
          background: 'rgba(28, 28, 30, 0.8)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          maxWidth: 600,
          mx: 'auto',
        }}
      >
        <CardContent sx={{ p: 4 }}>
          {/* Step 0: Generate Login URL */}
          {activeStep === 0 && (
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5 }}
            >
              <Typography variant="h5" sx={{ mb: 3, fontWeight: 600 }}>
                Generate Zerodha Login URL
              </Typography>

              <Alert
                severity="info"
                sx={{
                  mb: 3,
                  background: 'rgba(59, 130, 246, 0.1)',
                  border: '1px solid rgba(59, 130, 246, 0.3)',
                  color: 'white',
                }}
              >
                Click below to generate a secure login link for your Zerodha account
              </Alert>

              <Button
                variant="contained"
                size="large"
                fullWidth
                onClick={handleGenerateLoginUrl}
                disabled={loginMutation.isLoading}
                sx={{
                  py: 2,
                  background: 'linear-gradient(135deg, #007AFF 0%, #5856D6 100%)',
                  fontSize: '1.1rem',
                  fontWeight: 600,
                }}
              >
                {loginMutation.isLoading ? (
                  <CircularProgress size={24} color="inherit" />
                ) : (
                  'Generate Login URL'
                )}
              </Button>
            </motion.div>
          )}

          {/* Step 1: Login to Zerodha */}
          {activeStep === 1 && (
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5 }}
            >
              <Typography variant="h5" sx={{ mb: 3, fontWeight: 600 }}>
                Login to Zerodha
              </Typography>

              <Alert
                severity="success"
                sx={{
                  mb: 3,
                  background: 'rgba(16, 185, 129, 0.1)',
                  border: '1px solid rgba(16, 185, 129, 0.3)',
                  color: 'white',
                }}
              >
                Login URL generated successfully! Click the link below to login.
              </Alert>

              <Paper
                sx={{
                  p: 2,
                  mb: 3,
                  background: 'rgba(255, 255, 255, 0.05)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 2,
                }}
              >
                <Typography
                  variant="body2"
                  sx={{
                    flex: 1,
                    fontFamily: 'monospace',
                    fontSize: '0.75rem',
                    wordBreak: 'break-all',
                    color: 'rgba(255, 255, 255, 0.8)',
                  }}
                >
                  {loginUrl}
                </Typography>
                <Tooltip title="Copy URL">
                  <IconButton onClick={handleCopyUrl} size="small">
                    <ContentCopyIcon />
                  </IconButton>
                </Tooltip>
              </Paper>

              <Box sx={{ display: 'flex', gap: 2 }}>
                <Button
                  variant="contained"
                  startIcon={<LaunchIcon />}
                  onClick={() => window.open(loginUrl, '_blank')}
                  sx={{
                    flex: 1,
                    background: 'linear-gradient(135deg, #007AFF 0%, #5856D6 100%)',
                  }}
                >
                  Open Zerodha Login
                </Button>
                <Button
                  variant="outlined"
                  onClick={() => setActiveStep(2)}
                  sx={{
                    borderColor: 'rgba(255, 255, 255, 0.3)',
                    color: 'white',
                  }}
                >
                  I've Logged In
                </Button>
              </Box>

              <Typography
                variant="body2"
                sx={{
                  mt: 3,
                  color: 'rgba(255, 255, 255, 0.6)',
                  textAlign: 'center',
                }}
              >
                After logging in, you'll be redirected to a page with a request token in the URL
              </Typography>
            </motion.div>
          )}

          {/* Step 2: Enter Request Token */}
          {activeStep === 2 && (
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5 }}
            >
              <Typography variant="h5" sx={{ mb: 3, fontWeight: 600 }}>
                Enter Request Token
              </Typography>

              <Alert
                severity="info"
                sx={{
                  mb: 3,
                  background: 'rgba(59, 130, 246, 0.1)',
                  border: '1px solid rgba(59, 130, 246, 0.3)',
                  color: 'white',
                }}
              >
                Copy the 'request_token' parameter from the URL after successful login
              </Alert>

              <TextField
                fullWidth
                label="Request Token"
                value={requestToken}
                onChange={(e) => setRequestToken(e.target.value)}
                placeholder="Paste the request_token here"
                sx={{ mb: 3 }}
                helperText="Look for 'request_token=' in the redirected URL"
              />

              <Button
                variant="contained"
                size="large"
                fullWidth
                onClick={handleTokenSubmit}
                disabled={tokenMutation.isLoading || !requestToken.trim()}
                sx={{
                  py: 2,
                  background: 'linear-gradient(135deg, #10B981 0%, #059669 100%)',
                  fontSize: '1.1rem',
                  fontWeight: 600,
                }}
              >
                {tokenMutation.isLoading ? (
                  <CircularProgress size={24} color="inherit" />
                ) : (
                  'Connect to Zerodha'
                )}
              </Button>
            </motion.div>
          )}

          {/* Completion Step */}
          {activeStep === 3 && (
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.5 }}
              style={{ textAlign: 'center' }}
            >
              <CheckCircleIcon
                sx={{
                  fontSize: 80,
                  color: '#10B981',
                  mb: 3,
                  filter: 'drop-shadow(0 0 20px rgba(16, 185, 129, 0.3))',
                }}
              />

              <Typography variant="h4" sx={{ mb: 2, fontWeight: 700, color: '#10B981' }}>
                Successfully Connected!
              </Typography>

              <Typography variant="body1" sx={{ color: 'rgba(255, 255, 255, 0.7)' }}>
                Your Zerodha account is now connected. Redirecting to dashboard...
              </Typography>
            </motion.div>
          )}
        </CardContent>
      </Card>

      {/* Security Note */}
      <Box sx={{ mt: 4, textAlign: 'center' }}>
        <Chip
          label="🔒 Secure Connection"
          sx={{
            background: 'rgba(16, 185, 129, 0.1)',
            border: '1px solid rgba(16, 185, 129, 0.3)',
            color: '#10B981',
            mr: 2,
          }}
        />
        <Chip
          label="✅ Zerodha Official API"
          sx={{
            background: 'rgba(59, 130, 246, 0.1)',
            border: '1px solid rgba(59, 130, 246, 0.3)',
            color: '#3B82F6',
          }}
        />
      </Box>
    </motion.div>
  );
};

export default AuthenticationFlow;