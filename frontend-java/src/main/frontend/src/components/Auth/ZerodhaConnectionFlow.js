// frontend-java/src/main/frontend/src/components/Auth/ZerodhaConnectionFlow.js - Multi-User Zerodha Connection
import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Button,
  TextField,
  Typography,
  Alert,
  CircularProgress,
  Chip,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  OpenInNew as OpenInNewIcon,
  ContentCopy as CopyIcon,
  CheckCircle as CheckCircleIcon,
  TrendingUp as TrendingUpIcon,
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import toast from 'react-hot-toast';
import { useZerodhaLoginUrlQuery, useZerodhaTokenExchangeMutation } from '../../hooks/useUserApi';
import { useUser } from '../../contexts/UserContext';

const steps = ['Generate Login URL', 'Login to Zerodha', 'Enter Request Token'];

const ZerodhaConnectionFlow = () => {
  const [activeStep, setActiveStep] = useState(0);
  const [loginUrl, setLoginUrl] = useState('');
  const [requestToken, setRequestToken] = useState('');
  const { user } = useUser();

  const { data: loginUrlData, refetch: fetchLoginUrl, isLoading: urlLoading } = useZerodhaLoginUrlQuery();
  const tokenMutation = useZerodhaTokenExchangeMutation();

  const handleGenerateLoginUrl = async () => {
    const result = await fetchLoginUrl();
    if (result.data?.success) {
      setLoginUrl(result.data.login_url);
      setActiveStep(1);
      toast.success('Login URL generated successfully');
    } else {
      toast.error('Failed to generate login URL');
    }
  };

  const handleCopyUrl = () => {
    navigator.clipboard.writeText(loginUrl);
    toast.success('Login URL copied to clipboard');
  };

  const handleOpenUrl = () => {
    window.open(loginUrl, '_blank');
  };

  const handleTokenSubmit = () => {
    if (!requestToken.trim()) {
      toast.error('Please enter the request token');
      return;
    }

    tokenMutation.mutate({ request_token: requestToken }, {
      onSuccess: (data) => {
        if (data.success) {
          setActiveStep(2);
          toast.success('Zerodha connected successfully!');
          // The page will automatically refresh due to auth status change
        }
      },
    });
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
    >
      <Box sx={{ maxWidth: 800, mx: 'auto' }}>
        <Card
          sx={{
            background: 'rgba(255, 255, 255, 0.05)',
            backdropFilter: 'blur(10px)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: 4,
            overflow: 'hidden',
          }}
        >
          {/* Header */}
          <Box
            sx={{
              p: 3,
              pb: 2,
              textAlign: 'center',
              background: 'linear-gradient(135deg, #007AFF 0%, #5856D6 100%)',
            }}
          >
            <TrendingUpIcon sx={{ fontSize: 48, mb: 1, color: 'white' }} />
            <Typography variant="h4" fontWeight="bold" color="white">
              Connect Your Zerodha Account
            </Typography>
            <Typography variant="subtitle1" color="rgba(255, 255, 255, 0.8)">
              Welcome {user?.full_name}! Connect your Zerodha account to start investing.
            </Typography>
          </Box>

          <CardContent sx={{ p: 4 }}>
            {/* User Info */}
            <Alert 
              severity="info" 
              sx={{ 
                mb: 3,
                backgroundColor: 'rgba(33, 150, 243, 0.1)',
                color: 'white',
                '& .MuiAlert-icon': { color: '#2196F3' }
              }}
            >
              <Typography variant="body2">
                <strong>Logged in as:</strong> {user?.username} ({user?.email})
                <br />
                Your Zerodha API credentials are stored securely. Follow the steps below to connect.
              </Typography>
            </Alert>

            {/* Stepper */}
            <Stepper activeStep={activeStep} orientation="vertical">
              {/* Step 1: Generate Login URL */}
              <Step>
                <StepLabel sx={{ '& .MuiStepLabel-label': { color: 'white', fontSize: '1.1rem' } }}>
                  Generate Login URL
                </StepLabel>
                <StepContent>
                  <Typography
                    variant="body1"
                    sx={{ mb: 3, color: 'rgba(255, 255, 255, 0.8)' }}
                  >
                    Generate a secure login URL using your API credentials.
                  </Typography>

                  <Button
                    variant="contained"
                    size="large"
                    onClick={handleGenerateLoginUrl}
                    disabled={urlLoading}
                    sx={{
                      py: 1.5,
                      px: 4,
                      background: 'linear-gradient(135deg, #007AFF 0%, #5856D6 100%)',
                      fontSize: '1rem',
                      fontWeight: 600,
                      '&:hover': {
                        background: 'linear-gradient(135deg, #0056CC 0%, #4A4A9D 100%)',
                      },
                    }}
                  >
                    {urlLoading ? (
                      <CircularProgress size={24} color="inherit" />
                    ) : (
                      'Generate Login URL'
                    )}
                  </Button>
                </StepContent>
              </Step>

              {/* Step 2: Login to Zerodha */}
              <Step>
                <StepLabel sx={{ '& .MuiStepLabel-label': { color: 'white', fontSize: '1.1rem' } }}>
                  Login to Zerodha
                </StepLabel>
                <StepContent>
                  <Typography
                    variant="body1"
                    sx={{ mb: 2, color: 'rgba(255, 255, 255, 0.8)' }}
                  >
                    Click the login URL to authenticate with your Zerodha account.
                  </Typography>

                  {loginUrl && (
                    <Box sx={{ mb: 3 }}>
                      <Box
                        sx={{
                          p: 2,
                          background: 'rgba(0, 122, 255, 0.1)',
                          border: '1px solid rgba(0, 122, 255, 0.3)',
                          borderRadius: 2,
                          mb: 2,
                        }}
                      >
                        <Typography
                          variant="body2"
                          sx={{
                            color: '#007AFF',
                            wordBreak: 'break-all',
                            fontFamily: 'monospace',
                          }}
                        >
                          {loginUrl}
                        </Typography>
                      </Box>

                      <Box sx={{ display: 'flex', gap: 2 }}>
                        <Button
                          variant="contained"
                          onClick={handleOpenUrl}
                          startIcon={<OpenInNewIcon />}
                          sx={{
                            background: 'linear-gradient(135deg, #10B981 0%, #059669 100%)',
                            '&:hover': {
                              background: 'linear-gradient(135deg, #059669 0%, #047857 100%)',
                            },
                          }}
                        >
                          Open Login Page
                        </Button>

                        <Tooltip title="Copy URL">
                          <IconButton
                            onClick={handleCopyUrl}
                            sx={{
                              color: 'white',
                              border: '1px solid rgba(255, 255, 255, 0.3)',
                              '&:hover': { backgroundColor: 'rgba(255, 255, 255, 0.1)' },
                            }}
                          >
                            <CopyIcon />
                          </IconButton>
                        </Tooltip>
                      </Box>
                    </Box>
                  )}

                  <Alert severity="warning" sx={{ backgroundColor: 'rgba(255, 152, 0, 0.1)' }}>
                    <Typography variant="body2" color="white">
                      After logging in, you'll be redirected to a page with a <strong>request_token</strong> parameter in the URL. 
                      Copy this token for the next step.
                    </Typography>
                  </Alert>

                  <Button
                    onClick={() => setActiveStep(2)}
                    sx={{ mt: 2, color: '#007AFF' }}
                  >
                    I have the request token
                  </Button>
                </StepContent>
              </Step>

              {/* Step 3: Enter Request Token */}
              <Step>
                <StepLabel sx={{ '& .MuiStepLabel-label': { color: 'white', fontSize: '1.1rem' } }}>
                  Enter Request Token
                </StepLabel>
                <StepContent>
                  <Typography
                    variant="body1"
                    sx={{ mb: 3, color: 'rgba(255, 255, 255, 0.8)' }}
                  >
                    Paste the request token from the redirect URL to complete authentication.
                  </Typography>

                  <TextField
                    fullWidth
                    label="Request Token"
                    value={requestToken}
                    onChange={(e) => setRequestToken(e.target.value)}
                    placeholder="Enter the request_token from the URL"
                    sx={{
                      mb: 3,
                      '& .MuiInputBase-input': { color: 'white' },
                      '& .MuiInputLabel-root': { color: 'rgba(255, 255, 255, 0.7)' },
                      '& .MuiOutlinedInput-root': {
                        '& fieldset': { borderColor: 'rgba(255, 255, 255, 0.3)' },
                        '&:hover fieldset': { borderColor: 'rgba(255, 255, 255, 0.5)' },
                      },
                    }}
                  />

                  <Button
                    variant="contained"
                    size="large"
                    onClick={handleTokenSubmit}
                    disabled={tokenMutation.isLoading || !requestToken.trim()}
                    sx={{
                      py: 1.5,
                      px: 4,
                      background: 'linear-gradient(135deg, #10B981 0%, #059669 100%)',
                      fontSize: '1rem',
                      fontWeight: 600,
                      '&:hover': {
                        background: 'linear-gradient(135deg, #059669 0%, #047857 100%)',
                      },
                    }}
                  >
                    {tokenMutation.isLoading ? (
                      <>
                        <CircularProgress size={20} color="inherit" sx={{ mr: 1 }} />
                        Connecting...
                      </>
                    ) : (
                      <>
                        <CheckCircleIcon sx={{ mr: 1 }} />
                        Connect to Zerodha
                      </>
                    )}
                  </Button>
                </StepContent>
              </Step>
            </Stepper>

            {/* Success State */}
            {activeStep >= steps.length && (
              <Box sx={{ mt: 4, textAlign: 'center' }}>
                <CheckCircleIcon sx={{ fontSize: 64, color: '#10B981', mb: 2 }} />
                <Typography variant="h5" sx={{ color: '#10B981', mb: 1, fontWeight: 600 }}>
                  Successfully Connected!
                </Typography>
                <Typography variant="body1" sx={{ color: 'rgba(255, 255, 255, 0.8)' }}>
                  Your Zerodha account is now connected. The page will refresh automatically.
                </Typography>
              </Box>
            )}
          </CardContent>
        </Card>
      </Box>
    </motion.div>
  );
};

export default ZerodhaConnectionFlow;