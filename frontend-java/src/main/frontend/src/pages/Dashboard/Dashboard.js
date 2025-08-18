import React, { useState } from 'react';
import {
  Box,
  Container,
  Grid,
  Typography,
  Card,
  CardContent,
  Button,
  Paper,
  Chip,
  Avatar,
  IconButton,
  Tooltip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Alert,
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  AccountBalance as AccountBalanceIcon,
  ShowChart as ShowChartIcon,
  Refresh as RefreshIcon,
  Timeline as TimelineIcon,
  Assessment as AssessmentIcon,
  Storage as StorageIcon,
  Person as PersonIcon,
  AccountBalance as PortfolioIcon,
  Analytics as AnalyticsIcon,
  DataObject as DataObjectIcon,
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import toast from 'react-hot-toast';

// Components
import LoadingScreen from '../../components/UI/LoadingScreen';
import AuthenticationFlow from '../../components/Auth/AuthenticationFlow';

// Hooks
import { 
  useAuthStatus, 
  useInvestmentStatus, 
  usePortfolioStatus,
  useCsvStocks,
  useSystemOrders,
} from '../../hooks/useApi';

const Dashboard = () => {
  
  const { data: authStatus, isLoading: authLoading } = useAuthStatus();
  const { data: investmentStatus, isLoading: investmentLoading, refetch: refetchInvestment } = useInvestmentStatus();
  const { data: portfolioStatus, isLoading: portfolioLoading, refetch: refetchPortfolio } = usePortfolioStatus();
  const { data: csvStocks, isLoading: csvLoading, refetch: refetchCsv } = useCsvStocks();
  const { data: systemOrders, isLoading: ordersLoading, refetch: refetchOrders } = useSystemOrders();

  const handleRefresh = () => {
    refetchInvestment();
    refetchPortfolio();
    refetchCsv();
    refetchOrders();
    toast.success('Data refreshed');
  };

  // Loading state
  if (authLoading || investmentLoading) {
    return <LoadingScreen message="Loading dashboard..." />;
  }

  // Not authenticated
  if (!authStatus?.authenticated) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <AuthenticationFlow />
      </Container>
    );
  }

  const portfolio = portfolioStatus?.data?.portfolio_summary || {};
  const csvData = csvStocks?.data;
  const orders = systemOrders?.data?.orders || [];

  return (
    <Container maxWidth="xl" sx={{ py: 3 }}>
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Avatar
              sx={{
                background: 'linear-gradient(135deg, #007AFF 0%, #5856D6 100%)',
                width: 56,
                height: 56,
              }}
            >
              <PersonIcon sx={{ fontSize: 28 }} />
            </Avatar>
            <Box>
              <Typography
                variant="h4"
                sx={{
                  fontWeight: 700,
                  background: 'linear-gradient(135deg, #007AFF 0%, #5856D6 50%, #FF2D92 100%)',
                  backgroundClip: 'text',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                }}
              >
                Investment Dashboard
              </Typography>
              <Typography variant="h6" sx={{ color: 'rgba(255, 255, 255, 0.8)' }}>
                Welcome back, {authStatus?.profile_name || 'Investor'}
              </Typography>
            </Box>
          </Box>
          
          <Box sx={{ display: 'flex', gap: 2 }}>
            <Chip
              label="Connected to Zerodha"
              color="success"
              variant="outlined"
              sx={{ 
                borderColor: '#10B981',
                color: '#10B981',
                fontWeight: 600,
              }}
            />
            <Tooltip title="Refresh All Data">
              <IconButton
                onClick={handleRefresh}
                sx={{
                  background: 'rgba(255, 255, 255, 0.1)',
                  backdropFilter: 'blur(10px)',
                  '&:hover': {
                    background: 'rgba(255, 255, 255, 0.2)',
                    transform: 'rotate(180deg)',
                  },
                  transition: 'all 0.3s ease',
                }}
              >
                <RefreshIcon />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>

        {/* Quick Stats */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} lg={3}>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
            >
              <Card
                sx={{
                  background: 'linear-gradient(135deg, #007AFF 0%, #5856D6 100%)',
                  color: 'white',
                  height: '100%',
                  minHeight: 140,
                  position: 'relative',
                  overflow: 'hidden',
                  '&::before': {
                    content: '""',
                    position: 'absolute',
                    top: 0,
                    right: 0,
                    width: '60px',
                    height: '60px',
                    background: 'rgba(255,255,255,0.1)',
                    borderRadius: '50%',
                    transform: 'translate(20px, -20px)',
                  },
                  '&:hover': {
                    transform: 'translateY(-4px)',
                    boxShadow: '0 12px 24px rgba(0, 122, 255, 0.3)',
                  },
                  transition: 'all 0.3s ease',
                }}
              >
                <CardContent sx={{ p: 3 }}>
                  <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <AccountBalanceIcon sx={{ fontSize: 28, opacity: 0.9 }} />
                      <Typography 
                        variant="subtitle1" 
                        sx={{ 
                          fontWeight: 600,
                          ml: 1,
                          fontSize: { xs: '0.9rem', sm: '1rem' },
                          lineHeight: 1.2
                        }}
                      >
                        Portfolio Value
                      </Typography>
                    </Box>
                    <Typography 
                      variant="h4" 
                      sx={{ 
                        fontWeight: 700,
                        fontSize: { xs: '1.5rem', sm: '1.8rem', md: '2rem' },
                        lineHeight: 1.1,
                        wordBreak: 'break-word'
                      }}
                    >
                      ₹{(portfolio.current_value || 0).toLocaleString()}
                    </Typography>
                  </Box>
                </CardContent>
              </Card>
            </motion.div>
          </Grid>

          <Grid item xs={12} sm={6} lg={3}>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
            >
              <Card
                sx={{
                  background: 'linear-gradient(135deg, #10B981 0%, #059669 100%)',
                  color: 'white',
                  height: '100%',
                  minHeight: 140,
                  position: 'relative',
                  overflow: 'hidden',
                  '&::before': {
                    content: '""',
                    position: 'absolute',
                    top: 0,
                    right: 0,
                    width: '60px',
                    height: '60px',
                    background: 'rgba(255,255,255,0.1)',
                    borderRadius: '50%',
                    transform: 'translate(20px, -20px)',
                  },
                  '&:hover': {
                    transform: 'translateY(-4px)',
                    boxShadow: '0 12px 24px rgba(16, 185, 129, 0.3)',
                  },
                  transition: 'all 0.3s ease',
                }}
              >
                <CardContent sx={{ p: 3 }}>
                  <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <TrendingUpIcon sx={{ fontSize: 28, opacity: 0.9 }} />
                      <Typography 
                        variant="subtitle1" 
                        sx={{ 
                          fontWeight: 600,
                          ml: 1,
                          fontSize: { xs: '0.9rem', sm: '1rem' },
                          lineHeight: 1.2
                        }}
                      >
                        Total Returns
                      </Typography>
                    </Box>
                    <Typography 
                      variant="h4" 
                      sx={{ 
                        fontWeight: 700,
                        fontSize: { xs: '1.5rem', sm: '1.8rem', md: '2rem' },
                        lineHeight: 1.1,
                        color: (portfolio.returns_percentage || 0) >= 0 ? '#E8F5E8' : '#FFE8E8'
                      }}
                    >
                      {(portfolio.returns_percentage || 0) >= 0 ? '+' : ''}{(portfolio.returns_percentage || 0).toFixed(2)}%
                    </Typography>
                  </Box>
                </CardContent>
              </Card>
            </motion.div>
          </Grid>

          <Grid item xs={12} sm={6} lg={3}>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.3 }}
            >
              <Card
                sx={{
                  background: 'linear-gradient(135deg, #FF2D92 0%, #FF6B6B 100%)',
                  color: 'white',
                  height: '100%',
                  minHeight: 140,
                  position: 'relative',
                  overflow: 'hidden',
                  '&::before': {
                    content: '""',
                    position: 'absolute',
                    top: 0,
                    right: 0,
                    width: '60px',
                    height: '60px',
                    background: 'rgba(255,255,255,0.1)',
                    borderRadius: '50%',
                    transform: 'translate(20px, -20px)',
                  },
                  '&:hover': {
                    transform: 'translateY(-4px)',
                    boxShadow: '0 12px 24px rgba(255, 45, 146, 0.3)',
                  },
                  transition: 'all 0.3s ease',
                }}
              >
                <CardContent sx={{ p: 3 }}>
                  <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <ShowChartIcon sx={{ fontSize: 28, opacity: 0.9 }} />
                      <Typography 
                        variant="subtitle1" 
                        sx={{ 
                          fontWeight: 600,
                          ml: 1,
                          fontSize: { xs: '0.9rem', sm: '1rem' },
                          lineHeight: 1.2
                        }}
                      >
                        Total Investment
                      </Typography>
                    </Box>
                    <Typography 
                      variant="h4" 
                      sx={{ 
                        fontWeight: 700,
                        fontSize: { xs: '1.5rem', sm: '1.8rem', md: '2rem' },
                        lineHeight: 1.1,
                        wordBreak: 'break-word'
                      }}
                    >
                      ₹{(portfolio.total_investment || 0).toLocaleString()}
                    </Typography>
                  </Box>
                </CardContent>
              </Card>
            </motion.div>
          </Grid>

          <Grid item xs={12} sm={6} lg={3}>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.4 }}
            >
              <Card
                sx={{
                  background: 'linear-gradient(135deg, #F59E0B 0%, #F97316 100%)',
                  color: 'white',
                  height: '100%',
                  minHeight: 140,
                  position: 'relative',
                  overflow: 'hidden',
                  '&::before': {
                    content: '""',
                    position: 'absolute',
                    top: 0,
                    right: 0,
                    width: '60px',
                    height: '60px',
                    background: 'rgba(255,255,255,0.1)',
                    borderRadius: '50%',
                    transform: 'translate(20px, -20px)',
                  },
                  '&:hover': {
                    transform: 'translateY(-4px)',
                    boxShadow: '0 12px 24px rgba(245, 158, 11, 0.3)',
                  },
                  transition: 'all 0.3s ease',
                }}
              >
                <CardContent sx={{ p: 3 }}>
                  <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <PortfolioIcon sx={{ fontSize: 28, opacity: 0.9 }} />
                      <Typography 
                        variant="subtitle1" 
                        sx={{ 
                          fontWeight: 600,
                          ml: 1,
                          fontSize: { xs: '0.9rem', sm: '1rem' },
                          lineHeight: 1.2
                        }}
                      >
                        Holdings
                      </Typography>
                    </Box>
                    <Typography 
                      variant="h4" 
                      sx={{ 
                        fontWeight: 700,
                        fontSize: { xs: '1.5rem', sm: '1.8rem', md: '2rem' },
                        lineHeight: 1.1
                      }}
                    >
                      {portfolio.stock_count || 0}
                    </Typography>
                    <Typography 
                      variant="caption" 
                      sx={{ 
                        fontSize: '0.75rem',
                        opacity: 0.8,
                        mt: 0.5
                      }}
                    >
                      stocks
                    </Typography>
                  </Box>
                </CardContent>
              </Card>
            </motion.div>
          </Grid>
        </Grid>

        {/* Recent Activity Summary */}
        <Grid container spacing={3}>
          <Grid item xs={12} lg={6}>
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6, delay: 0.5 }}
            >
              <Card
                sx={{
                  background: 'rgba(28, 28, 30, 0.8)',
                  backdropFilter: 'blur(20px)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  height: '100%',
                  minHeight: 300,
                  '&:hover': {
                    border: '1px solid rgba(0, 122, 255, 0.3)',
                    transform: 'translateY(-2px)',
                  },
                  transition: 'all 0.3s ease',
                }}
              >
                <CardContent sx={{ p: 3 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                    <Box
                      sx={{
                        p: 1.5,
                        borderRadius: 2,
                        background: 'linear-gradient(135deg, rgba(0, 122, 255, 0.1) 0%, rgba(88, 86, 214, 0.1) 100%)',
                        border: '1px solid rgba(0, 122, 255, 0.2)',
                        mr: 2
                      }}
                    >
                      <TimelineIcon sx={{ color: '#007AFF', fontSize: 24 }} />
                    </Box>
                    <Typography 
                      variant="h6" 
                      sx={{ 
                        fontWeight: 700,
                        fontSize: { xs: '1.1rem', sm: '1.25rem' },
                        color: '#FFFFFF'
                      }}
                    >
                      Recent Orders
                    </Typography>
                  </Box>
                  {ordersLoading ? (
                    <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', py: 4 }}>
                      <Typography sx={{ color: 'rgba(255, 255, 255, 0.6)' }}>Loading orders...</Typography>
                    </Box>
                  ) : orders.length > 0 ? (
                    <Box sx={{ mt: 1 }}>
                      {orders.slice(0, 4).map((order, index) => (
                        <Box 
                          key={index} 
                          sx={{ 
                            p: 2, 
                            mb: 1.5,
                            borderRadius: 2,
                            background: 'rgba(255, 255, 255, 0.03)',
                            border: '1px solid rgba(255, 255, 255, 0.06)',
                            '&:hover': {
                              background: 'rgba(255, 255, 255, 0.05)',
                              border: '1px solid rgba(255, 255, 255, 0.1)',
                            },
                            transition: 'all 0.2s ease',
                          }}
                        >
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <Box>
                              <Typography 
                                variant="body1" 
                                sx={{ 
                                  fontWeight: 600,
                                  fontSize: '0.95rem',
                                  color: '#FFFFFF',
                                  mb: 0.5
                                }}
                              >
                                {order.action} {order.shares || order.quantity || 0} {order.symbol}
                              </Typography>
                              <Typography 
                                variant="body2" 
                                sx={{ 
                                  fontSize: '0.85rem',
                                  color: 'rgba(255, 255, 255, 0.7)'
                                }}
                              >
                                ₹{Number(order.price || 0).toLocaleString()}
                              </Typography>
                            </Box>
                            <Chip 
                              label={order.action || 'BUY'} 
                              size="small"
                              sx={{
                                background: order.action === 'SELL' ? 'rgba(239, 68, 68, 0.2)' : 'rgba(16, 185, 129, 0.2)',
                                color: order.action === 'SELL' ? '#EF4444' : '#10B981',
                                border: `1px solid ${order.action === 'SELL' ? 'rgba(239, 68, 68, 0.3)' : 'rgba(16, 185, 129, 0.3)'}`,
                                fontWeight: 600,
                                fontSize: '0.75rem'
                              }}
                            />
                          </Box>
                        </Box>
                      ))}
                    </Box>
                  ) : (
                    <Box sx={{ 
                      display: 'flex', 
                      flexDirection: 'column', 
                      alignItems: 'center', 
                      justifyContent: 'center',
                      py: 4,
                      textAlign: 'center'
                    }}>
                      <DataObjectIcon sx={{ fontSize: 48, color: 'rgba(255, 255, 255, 0.3)', mb: 2 }} />
                      <Typography variant="body1" sx={{ color: 'rgba(255, 255, 255, 0.7)', fontWeight: 500 }}>
                        No Recent Orders
                      </Typography>
                      <Typography variant="body2" sx={{ color: 'rgba(255, 255, 255, 0.5)', mt: 0.5 }}>
                        Your order history will appear here
                      </Typography>
                    </Box>
                  )}
                </CardContent>
              </Card>
            </motion.div>
          </Grid>

          <Grid item xs={12} lg={6}>
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6, delay: 0.6 }}
            >
              <Card
                sx={{
                  background: 'rgba(28, 28, 30, 0.8)',
                  backdropFilter: 'blur(20px)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  height: '100%',
                  minHeight: 300,
                  '&:hover': {
                    border: '1px solid rgba(16, 185, 129, 0.3)',
                    transform: 'translateY(-2px)',
                  },
                  transition: 'all 0.3s ease',
                }}
              >
                <CardContent sx={{ p: 3 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                    <Box
                      sx={{
                        p: 1.5,
                        borderRadius: 2,
                        background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(5, 150, 105, 0.1) 100%)',
                        border: '1px solid rgba(16, 185, 129, 0.2)',
                        mr: 2
                      }}
                    >
                      <AssessmentIcon sx={{ color: '#10B981', fontSize: 24 }} />
                    </Box>
                    <Typography 
                      variant="h6" 
                      sx={{ 
                        fontWeight: 700,
                        fontSize: { xs: '1.1rem', sm: '1.25rem' },
                        color: '#FFFFFF'
                      }}
                    >
                      System Status
                    </Typography>
                  </Box>
                  
                  <Box sx={{ mt: 2 }}>
                    <Box sx={{ 
                      p: 2.5, 
                      mb: 2,
                      borderRadius: 2,
                      background: authStatus?.authenticated ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                      border: `1px solid ${authStatus?.authenticated ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)'}`,
                    }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <Box>
                          <Typography variant="body1" sx={{ fontWeight: 600, color: '#FFFFFF', mb: 0.5 }}>
                            Zerodha Connection
                          </Typography>
                          <Typography variant="body2" sx={{ color: 'rgba(255, 255, 255, 0.7)' }}>
                            Trading platform status
                          </Typography>
                        </Box>
                        <Chip 
                          label={authStatus?.authenticated ? 'Connected' : 'Disconnected'}
                          size="small"
                          sx={{
                            background: authStatus?.authenticated ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)',
                            color: authStatus?.authenticated ? '#10B981' : '#EF4444',
                            border: `1px solid ${authStatus?.authenticated ? 'rgba(16, 185, 129, 0.4)' : 'rgba(239, 68, 68, 0.4)'}`,
                            fontWeight: 600
                          }}
                        />
                      </Box>
                    </Box>
                    
                    <Box sx={{ 
                      p: 2.5, 
                      mb: 2,
                      borderRadius: 2,
                      background: csvData?.csv_info ? 'rgba(16, 185, 129, 0.1)' : 'rgba(245, 158, 11, 0.1)',
                      border: `1px solid ${csvData?.csv_info ? 'rgba(16, 185, 129, 0.2)' : 'rgba(245, 158, 11, 0.2)'}`,
                    }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <Box>
                          <Typography variant="body1" sx={{ fontWeight: 600, color: '#FFFFFF', mb: 0.5 }}>
                            CSV Data
                          </Typography>
                          <Typography variant="body2" sx={{ color: 'rgba(255, 255, 255, 0.7)' }}>
                            Stock allocation data
                          </Typography>
                        </Box>
                        <Chip 
                          label={csvData?.csv_info ? 'Available' : 'Loading'}
                          size="small"
                          sx={{
                            background: csvData?.csv_info ? 'rgba(16, 185, 129, 0.2)' : 'rgba(245, 158, 11, 0.2)',
                            color: csvData?.csv_info ? '#10B981' : '#F59E0B',
                            border: `1px solid ${csvData?.csv_info ? 'rgba(16, 185, 129, 0.4)' : 'rgba(245, 158, 11, 0.4)'}`,
                            fontWeight: 600
                          }}
                        />
                      </Box>
                    </Box>
                    
                    <Box sx={{ 
                      p: 2.5,
                      borderRadius: 2,
                      background: 'rgba(0, 122, 255, 0.1)',
                      border: '1px solid rgba(0, 122, 255, 0.2)',
                    }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <Box>
                          <Typography variant="body1" sx={{ fontWeight: 600, color: '#FFFFFF', mb: 0.5 }}>
                            Active Portfolio
                          </Typography>
                          <Typography variant="body2" sx={{ color: 'rgba(255, 255, 255, 0.7)' }}>
                            Currently held positions
                          </Typography>
                        </Box>
                        <Box sx={{ textAlign: 'right' }}>
                          <Typography variant="h6" sx={{ fontWeight: 700, color: '#007AFF' }}>
                            {portfolio.stock_count || 0}
                          </Typography>
                          <Typography variant="caption" sx={{ color: 'rgba(255, 255, 255, 0.6)' }}>
                            stocks
                          </Typography>
                        </Box>
                      </Box>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </motion.div>
          </Grid>
        </Grid>
      </motion.div>
    </Container>
  );
};

export default Dashboard;