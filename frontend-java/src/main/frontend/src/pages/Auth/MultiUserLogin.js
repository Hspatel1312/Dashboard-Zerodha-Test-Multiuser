// frontend-java/src/main/frontend/src/pages/Auth/MultiUserLogin.js - Multi-User Login & Registration
import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Tabs,
  Tab,
  TextField,
  Button,
  Typography,
  Alert,
  Grid,
  Divider,
  CircularProgress,
  InputAdornment,
  IconButton,
  FormControl,
  InputLabel,
  Select,
  MenuItem
} from '@mui/material';
import {
  Visibility,
  VisibilityOff,
  PersonAdd as RegisterIcon,
  Login as LoginIcon,
  AccountBalance as InvestmentIcon
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import toast from 'react-hot-toast';
import { useUser } from '../../contexts/UserContext';
import { useRegisterMutation, useLoginMutation } from '../../hooks/useUserApi';

const MultiUserLogin = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const { login } = useUser();

  // Login form state
  const [loginData, setLoginData] = useState({
    username: '',
    password: ''
  });

  // Registration form state
  const [registerData, setRegisterData] = useState({
    username: '',
    email: '',
    full_name: '',
    password: '',
    confirmPassword: '',
    zerodha_api_key: '',
    zerodha_api_secret: '',
    role: 'user'
  });

  const registerMutation = useRegisterMutation();
  const loginMutation = useLoginMutation();

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  const handleLoginSubmit = async (e) => {
    e.preventDefault();
    
    if (!loginData.username || !loginData.password) {
      return;
    }

    try {
      const response = await loginMutation.mutateAsync(loginData);
      if (response.success) {
        login(response.user, response.token);
      }
    } catch (error) {
      // Error handled by mutation
    }
  };

  const handleRegisterSubmit = async (e) => {
    e.preventDefault();
    
    console.log('Registration form data:', registerData);
    
    // Validation
    if (!registerData.username || !registerData.email || !registerData.full_name || 
        !registerData.password || !registerData.zerodha_api_key || 
        !registerData.zerodha_api_secret) {
      console.error('Registration validation failed - missing required fields');
      toast.error('Please fill in all required fields');
      return;
    }

    if (registerData.password !== registerData.confirmPassword) {
      console.error('Registration validation failed - passwords do not match');
      toast.error('Passwords do not match');
      return;
    }

    try {
      const { confirmPassword, ...submitData } = registerData;
      console.log('Submitting registration data:', submitData);
      
      const response = await registerMutation.mutateAsync(submitData);
      console.log('Registration response received:', response);
      
      if (response.success) {
        console.log('Registration successful, logging in user');
        login(response.user, response.token);
      }
    } catch (error) {
      console.error('Registration submission error:', error);
      // Error handled by mutation
    }
  };

  const handleLoginChange = (field) => (e) => {
    setLoginData(prev => ({
      ...prev,
      [field]: e.target.value
    }));
  };

  const handleRegisterChange = (field) => (e) => {
    setRegisterData(prev => ({
      ...prev,
      [field]: e.target.value
    }));
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #000000 0%, #111111 100%)',
        p: 2
      }}
    >
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <Card
          sx={{
            maxWidth: 500,
            width: '100%',
            background: 'rgba(255, 255, 255, 0.05)',
            backdropFilter: 'blur(10px)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: 4,
            overflow: 'hidden'
          }}
        >
          {/* Header */}
          <Box
            sx={{
              p: 3,
              pb: 2,
              textAlign: 'center',
              background: 'linear-gradient(135deg, #10B981 0%, #059669 100%)',
            }}
          >
            <InvestmentIcon sx={{ fontSize: 48, mb: 1 }} />
            <Typography variant="h4" fontWeight="bold" color="white">
              Investment Dashboard
            </Typography>
            <Typography variant="subtitle1" color="rgba(255, 255, 255, 0.8)">
              Multi-User Portfolio Rebalancing
            </Typography>
          </Box>

          <CardContent sx={{ p: 0 }}>
            {/* Tabs */}
            <Tabs
              value={activeTab}
              onChange={handleTabChange}
              sx={{
                '& .MuiTab-root': {
                  color: 'rgba(255, 255, 255, 0.7)',
                  fontWeight: 600,
                  minWidth: '50%'
                },
                '& .Mui-selected': {
                  color: '#10B981',
                },
                '& .MuiTabs-indicator': {
                  backgroundColor: '#10B981',
                },
                borderBottom: '1px solid rgba(255, 255, 255, 0.1)'
              }}
              centered
            >
              <Tab 
                label="Login" 
                icon={<LoginIcon />} 
                iconPosition="start"
              />
              <Tab 
                label="Register" 
                icon={<RegisterIcon />} 
                iconPosition="start"
              />
            </Tabs>

            {/* Login Form */}
            {activeTab === 0 && (
              <Box sx={{ p: 3 }}>
                <form onSubmit={handleLoginSubmit}>
                  <TextField
                    fullWidth
                    label="Username"
                    value={loginData.username}
                    onChange={handleLoginChange('username')}
                    margin="normal"
                    required
                    autoComplete="username"
                    sx={{ mb: 2 }}
                    InputProps={{
                      sx: { color: 'white' }
                    }}
                    InputLabelProps={{
                      sx: { color: 'rgba(255, 255, 255, 0.7)' }
                    }}
                  />
                  
                  <TextField
                    fullWidth
                    label="Password"
                    type={showPassword ? 'text' : 'password'}
                    value={loginData.password}
                    onChange={handleLoginChange('password')}
                    margin="normal"
                    required
                    autoComplete="current-password"
                    sx={{ mb: 3 }}
                    InputProps={{
                      sx: { color: 'white' },
                      endAdornment: (
                        <InputAdornment position="end">
                          <IconButton
                            onClick={() => setShowPassword(!showPassword)}
                            sx={{ color: 'rgba(255, 255, 255, 0.7)' }}
                          >
                            {showPassword ? <VisibilityOff /> : <Visibility />}
                          </IconButton>
                        </InputAdornment>
                      )
                    }}
                    InputLabelProps={{
                      sx: { color: 'rgba(255, 255, 255, 0.7)' }
                    }}
                  />

                  <Button
                    type="submit"
                    fullWidth
                    variant="contained"
                    size="large"
                    disabled={loginMutation.isLoading}
                    sx={{
                      mt: 2,
                      py: 1.5,
                      background: 'linear-gradient(135deg, #10B981 0%, #059669 100%)',
                      '&:hover': {
                        background: 'linear-gradient(135deg, #059669 0%, #047857 100%)',
                      },
                      '&:disabled': {
                        background: 'rgba(255, 255, 255, 0.1)',
                      }
                    }}
                  >
                    {loginMutation.isLoading ? (
                      <CircularProgress size={24} />
                    ) : (
                      'Login'
                    )}
                  </Button>
                </form>
              </Box>
            )}

            {/* Registration Form */}
            {activeTab === 1 && (
              <Box sx={{ p: 3 }}>
                {/* DEBUG INFO - REMOVE AFTER TESTING */}
                <Alert severity="success" sx={{ mb: 2, backgroundColor: 'rgba(76, 175, 80, 0.1)' }}>
                  <Typography variant="body2" color="white">
                    ✅ NEW MULTI-USER REGISTRATION (API Key/Secret) - Version 3.0
                  </Typography>
                </Alert>
                
                <form onSubmit={handleRegisterSubmit}>
                  <Grid container spacing={2}>
                    {/* Basic Info */}
                    <Grid item xs={12}>
                      <Typography variant="h6" color="white" gutterBottom>
                        Basic Information
                      </Typography>
                      <Divider sx={{ borderColor: 'rgba(255, 255, 255, 0.1)', mb: 2 }} />
                    </Grid>

                    <Grid item xs={12} sm={6}>
                      <TextField
                        fullWidth
                        label="Username"
                        value={registerData.username}
                        onChange={handleRegisterChange('username')}
                        required
                        sx={{ 
                          '& .MuiInputBase-input': { color: 'white' },
                          '& .MuiInputLabel-root': { color: 'rgba(255, 255, 255, 0.7)' }
                        }}
                      />
                    </Grid>

                    <Grid item xs={12} sm={6}>
                      <TextField
                        fullWidth
                        label="Full Name"
                        value={registerData.full_name}
                        onChange={handleRegisterChange('full_name')}
                        required
                        sx={{ 
                          '& .MuiInputBase-input': { color: 'white' },
                          '& .MuiInputLabel-root': { color: 'rgba(255, 255, 255, 0.7)' }
                        }}
                      />
                    </Grid>

                    <Grid item xs={12}>
                      <TextField
                        fullWidth
                        label="Email"
                        type="email"
                        value={registerData.email}
                        onChange={handleRegisterChange('email')}
                        required
                        sx={{ 
                          '& .MuiInputBase-input': { color: 'white' },
                          '& .MuiInputLabel-root': { color: 'rgba(255, 255, 255, 0.7)' }
                        }}
                      />
                    </Grid>

                    <Grid item xs={12} sm={6}>
                      <TextField
                        fullWidth
                        label="Password"
                        type={showPassword ? 'text' : 'password'}
                        value={registerData.password}
                        onChange={handleRegisterChange('password')}
                        required
                        InputProps={{
                          sx: { color: 'white' },
                          endAdornment: (
                            <InputAdornment position="end">
                              <IconButton
                                onClick={() => setShowPassword(!showPassword)}
                                sx={{ color: 'rgba(255, 255, 255, 0.7)' }}
                              >
                                {showPassword ? <VisibilityOff /> : <Visibility />}
                              </IconButton>
                            </InputAdornment>
                          )
                        }}
                        InputLabelProps={{
                          sx: { color: 'rgba(255, 255, 255, 0.7)' }
                        }}
                      />
                    </Grid>

                    <Grid item xs={12} sm={6}>
                      <TextField
                        fullWidth
                        label="Confirm Password"
                        type={showConfirmPassword ? 'text' : 'password'}
                        value={registerData.confirmPassword}
                        onChange={handleRegisterChange('confirmPassword')}
                        required
                        error={registerData.password !== registerData.confirmPassword && registerData.confirmPassword !== ''}
                        helperText={
                          registerData.password !== registerData.confirmPassword && registerData.confirmPassword !== '' 
                            ? 'Passwords do not match' 
                            : ''
                        }
                        InputProps={{
                          sx: { color: 'white' },
                          endAdornment: (
                            <InputAdornment position="end">
                              <IconButton
                                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                                sx={{ color: 'rgba(255, 255, 255, 0.7)' }}
                              >
                                {showConfirmPassword ? <VisibilityOff /> : <Visibility />}
                              </IconButton>
                            </InputAdornment>
                          )
                        }}
                        InputLabelProps={{
                          sx: { color: 'rgba(255, 255, 255, 0.7)' }
                        }}
                      />
                    </Grid>

                    {/* Zerodha API Credentials */}
                    <Grid item xs={12}>
                      <Typography variant="h6" color="white" gutterBottom sx={{ mt: 2 }}>
                        Zerodha API Credentials
                      </Typography>
                      <Divider sx={{ borderColor: 'rgba(255, 255, 255, 0.1)', mb: 2 }} />
                    </Grid>

                    <Grid item xs={12}>
                      <TextField
                        fullWidth
                        label="Zerodha API Key"
                        value={registerData.zerodha_api_key}
                        onChange={handleRegisterChange('zerodha_api_key')}
                        required
                        helperText="Your API Key from Zerodha Kite Connect (e.g., abc123xyz456)"
                        sx={{ 
                          '& .MuiInputBase-input': { color: 'white' },
                          '& .MuiInputLabel-root': { color: 'rgba(255, 255, 255, 0.7)' },
                          '& .MuiFormHelperText-root': { color: 'rgba(255, 255, 255, 0.5)' }
                        }}
                      />
                    </Grid>

                    <Grid item xs={12}>
                      <TextField
                        fullWidth
                        label="Zerodha API Secret"
                        type="password"
                        value={registerData.zerodha_api_secret}
                        onChange={handleRegisterChange('zerodha_api_secret')}
                        required
                        helperText="Your API Secret from Zerodha Kite Connect"
                        sx={{ 
                          '& .MuiInputBase-input': { color: 'white' },
                          '& .MuiInputLabel-root': { color: 'rgba(255, 255, 255, 0.7)' },
                          '& .MuiFormHelperText-root': { color: 'rgba(255, 255, 255, 0.5)' }
                        }}
                      />
                    </Grid>

                    <Grid item xs={12}>
                      <Alert 
                        severity="info" 
                        sx={{ 
                          mt: 2,
                          backgroundColor: 'rgba(33, 150, 243, 0.1)',
                          color: 'white',
                          '& .MuiAlert-icon': { color: '#2196F3' }
                        }}
                      >
                        Get your API credentials from <strong>developers.zerodha.com</strong>. Your API key and secret are encrypted and stored securely. Each user has their own separate Zerodha API connection and portfolio data.
                      </Alert>
                    </Grid>
                  </Grid>

                  <Button
                    type="submit"
                    fullWidth
                    variant="contained"
                    size="large"
                    disabled={registerMutation.isLoading}
                    sx={{
                      mt: 3,
                      py: 1.5,
                      background: 'linear-gradient(135deg, #10B981 0%, #059669 100%)',
                      '&:hover': {
                        background: 'linear-gradient(135deg, #059669 0%, #047857 100%)',
                      },
                      '&:disabled': {
                        background: 'rgba(255, 255, 255, 0.1)',
                      }
                    }}
                  >
                    {registerMutation.isLoading ? (
                      <CircularProgress size={24} />
                    ) : (
                      'Create Account'
                    )}
                  </Button>
                </form>
              </Box>
            )}
          </CardContent>
        </Card>
      </motion.div>
    </Box>
  );
};

export default MultiUserLogin;