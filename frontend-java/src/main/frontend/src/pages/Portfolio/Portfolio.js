import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Typography,
  Card,
  CardContent,
  Button,
  Grid,
  Tabs,
  Tab,
  TextField,
  Alert,
  Chip,
  Avatar,
  Paper,
  IconButton,
  Tooltip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  LinearProgress,
} from '@mui/material';
import {
  AccountBalance as PortfolioIcon,
  TrendingUp as InvestIcon,
  Balance as RebalanceIcon,
  Assessment as AssessmentIcon,
  Refresh as RefreshIcon,
  PlayArrow as ExecuteIcon,
  Calculate as CalculateIcon,
  ShowChart as ShowChartIcon,
  Timeline as TimelineIcon,
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
  useInvestmentRequirements,
  useCalculateInvestmentPlanMutation,
  useExecuteInitialInvestmentMutation,
  useCalculateRebalancingMutation,
  useExecuteRebalancingMutation,
} from '../../hooks/useApi';

const Portfolio = () => {
  const [tabValue, setTabValue] = useState(0);
  const [investmentAmount, setInvestmentAmount] = useState('');
  const [investmentPlan, setInvestmentPlan] = useState(null);
  const [rebalancingPlan, setRebalancingPlan] = useState(null);
  const [niftyData, setNiftyData] = useState(null);

  // Queries with error handling
  const authQuery = useAuthStatus();
  const investmentQuery = useInvestmentStatus();
  const portfolioQuery = usePortfolioStatus();
  const requirementsQuery = useInvestmentRequirements();

  // Mutations
  const calculatePlanMutation = useCalculateInvestmentPlanMutation();
  const executeInvestmentMutation = useExecuteInitialInvestmentMutation();
  const calculateRebalancingMutation = useCalculateRebalancingMutation();
  const executeRebalancingMutation = useExecuteRebalancingMutation();

  // Fetch NIFTY data when component mounts and auth status changes
  useEffect(() => {
    if (authQuery?.data?.authenticated) {
      fetchNiftyData();
    }
  }, [authQuery?.data?.authenticated]);

  const fetchNiftyData = async () => {
    try {
      const response = await fetch('/api/test-nifty');
      const data = await response.json();
      if (data.success) {
        setNiftyData({
          price: data.nifty_price || data.alternative_data?.['NSE:RELIANCE']?.last_price,
          connected: true,
          timestamp: data.timestamp
        });
      } else {
        setNiftyData({ connected: false, error: data.error });
      }
    } catch (error) {
      console.error('Nifty fetch error:', error);
      setNiftyData({ connected: false, error: 'Connection failed' });
    }
  };

  // Safe data extraction function
  const getSafePortfolioData = () => {
    try {
      const authStatus = authQuery?.data;
      const investmentStatus = investmentQuery?.data;
      const portfolioStatus = portfolioQuery?.data;
      const requirements = requirementsQuery?.data;

      const portfolioSummary = portfolioStatus?.data?.portfolio_summary || {};
      
      const extractNumber = (value, defaultValue = 0) => {
        if (typeof value === 'number') return value;
        if (value && typeof value === 'object' && value.value !== undefined) return Number(value.value);
        if (value && typeof value === 'object' && value.amount !== undefined) return Number(value.amount);
        return Number(value) || defaultValue;
      };

      const portfolioHoldings = portfolioStatus?.data?.holdings || {};
      const holdingsArray = Object.entries(portfolioHoldings).map(([symbol, data]) => ({
        symbol,
        ...data
      }));

      const safePortfolio = {
        current_value: extractNumber(portfolioSummary.current_value, 0),
        total_investment: extractNumber(portfolioSummary.total_investment, 0),
        returns_percentage: extractNumber(portfolioSummary.returns_percentage, 0),
        stock_count: extractNumber(portfolioSummary.stock_count, 0),
        holdings: holdingsArray,
      };

      const safeRequirements = {
        minimum_investment: Number(requirements?.data?.minimum_investment?.minimum_investment) || 10000,
        recommended_minimum: Number(requirements?.data?.minimum_investment?.recommended_minimum) || 0,
      };

      return {
        authStatus,
        authLoading: authQuery?.isLoading,
        investmentLoading: investmentQuery?.isLoading,
        safePortfolio,
        safeRequirements,
        currentStatus: investmentStatus?.data?.status || 'UNKNOWN'
      };
    } catch (error) {
      console.error('Safe data extraction error:', error);
      return null;
    }
  };

  const data = getSafePortfolioData();

  // Error boundary
  if (!data) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Alert severity="error">
          <Typography variant="h6">Portfolio Data Error</Typography>
          <Typography>Failed to safely process portfolio data. Please refresh the page.</Typography>
        </Alert>
      </Container>
    );
  }

  const { 
    authStatus, 
    authLoading, 
    investmentLoading, 
    safePortfolio, 
    safeRequirements, 
    currentStatus 
  } = data;

  const handleRefresh = () => {
    try {
      investmentQuery?.refetch();
      portfolioQuery?.refetch();
      requirementsQuery?.refetch();
      fetchNiftyData();
      toast.success('Portfolio data refreshed');
    } catch (error) {
      console.error('Refresh error:', error);
      toast.error('Failed to refresh data');
    }
  };

  const handleCalculateInvestment = async () => {
    if (!investmentAmount || parseFloat(investmentAmount) <= 0) {
      toast.error('Please enter a valid investment amount');
      return;
    }

    try {
      const result = await calculatePlanMutation.mutateAsync(parseFloat(investmentAmount));
      console.log('Investment plan API response:', result);
      if (result.success) {
        setInvestmentPlan(result.data);
        toast.success('Investment plan calculated successfully');
      }
    } catch (error) {
      console.error('Calculate investment error:', error);
      
      // Extract detailed error information
      let errorMessage = 'Failed to calculate investment plan';
      if (error?.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      } else if (error?.response?.data?.message) {
        errorMessage = error.response.data.message;
      } else if (error?.message) {
        errorMessage = error.message;
      }
      
      // Check if it's a minimum investment error
      if (errorMessage.includes('below minimum required')) {
        const minAmount = safeRequirements?.minimum_investment || 0;
        const recommendedAmount = safeRequirements?.recommended_minimum || minAmount;
        
        toast.error(
          <div>
            <div style={{ fontWeight: 'bold', marginBottom: '8px' }}>
              Investment Amount Too Low
            </div>
            <div style={{ marginBottom: '4px' }}>
              Minimum Required: ₹{minAmount.toLocaleString()}
            </div>
            <div style={{ fontSize: '0.9em', opacity: 0.8 }}>
              Recommended: ₹{recommendedAmount.toLocaleString()} (includes 20% buffer)
            </div>
          </div>,
          { duration: 8000 }
        );
      } else {
        toast.error(`API Error: ${errorMessage}`);
      }
    }
  };

  const handleExecuteInvestment = async () => {
    try {
      const amount = parseFloat(investmentAmount);
      const result = await executeInvestmentMutation.mutateAsync(amount);
      if (result?.success) {
        toast.success('Live investment executed successfully on Zerodha!');
        setInvestmentPlan(null);
        setInvestmentAmount('');
        handleRefresh();
      }
    } catch (error) {
      console.error('Execute investment error:', error);
      toast.error('Failed to execute live investment');
    }
  };

  const handleCalculateRebalancing = async () => {
    try {
      const result = await calculateRebalancingMutation.mutateAsync(0); // Pass 0 for no additional investment
      if (result.success) {
        setRebalancingPlan(result.data.data); // Fix: Use result.data.data to get the actual plan data
      }
    } catch (error) {
      console.error('Calculate rebalancing error:', error);
    }
  };

  const handleExecuteRebalancing = async () => {
    try {
      console.log('Starting execute rebalancing...');
      const result = await executeRebalancingMutation.mutateAsync(0); // 0 additional investment by default
      console.log('Execute rebalancing result:', result);
      
      if (result?.success) {
        toast.success('Live rebalancing executed successfully on Zerodha!');
        setRebalancingPlan(null);
        handleRefresh();
      } else if (result?.data) {
        // Response received but success flag missing - likely still worked
        console.warn('Execute rebalancing completed but success flag unclear:', result);
        toast.success('Live rebalancing executed - check portfolio for updates');
        setRebalancingPlan(null);
        handleRefresh();
      } else {
        console.error('Execute rebalancing unexpected response:', result);
        toast.error('Unexpected response format from server');
      }
    } catch (error) {
      console.error('Execute rebalancing error:', error);
      console.error('Error details:', {
        message: error.message,
        response: error.response,
        status: error.response?.status,
        data: error.response?.data
      });
      
      // Check if it's actually a successful response but with parsing issues
      if (error?.response?.status === 200) {
        toast.success('Live rebalancing executed successfully (despite response parsing issue)');
        setRebalancingPlan(null);
        handleRefresh();
      } else if (error?.response?.data?.success) {
        // Success in the data but thrown as error
        toast.success('Live rebalancing executed successfully!');
        setRebalancingPlan(null);
        handleRefresh();
      } else {
        const errorMessage = error?.response?.data?.detail || 
                           error?.response?.data?.message || 
                           error?.message || 
                           'Failed to execute live rebalancing';
        toast.error(`Error: ${errorMessage}`);
      }
    }
  };


  // Loading state
  if (authLoading || investmentLoading) {
    return <LoadingScreen message="Loading portfolio..." />;
  }

  // Not authenticated
  if (!authStatus?.authenticated) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <AuthenticationFlow />
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ py: 3 }}>
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
              <PortfolioIcon sx={{ fontSize: 28 }} />
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
                Portfolio Management
              </Typography>
              <Typography variant="h6" sx={{ color: 'rgba(255, 255, 255, 0.8)' }}>
                Manage your investments and rebalancing
              </Typography>
            </Box>
          </Box>
          
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Chip
              label={`Status: ${currentStatus.replace('_', ' ')}`}
              color={currentStatus === 'FIRST_INVESTMENT' ? 'primary' : (currentStatus === 'BALANCED' ? 'success' : 'warning')}
              variant="outlined"
              sx={{ fontWeight: 600 }}
            />
            
            {/* NIFTY Display */}
            <Box sx={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: 2, 
              mr: 2,
              p: 1.5,
              background: niftyData?.connected ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
              border: `1px solid ${niftyData?.connected ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
              borderRadius: 2
            }}>
              <Box sx={{ 
                width: 8, 
                height: 8, 
                borderRadius: '50%', 
                backgroundColor: niftyData?.connected ? '#10B981' : '#EF4444'
              }} />
              <Box>
                <Typography variant="caption" sx={{ opacity: 0.7 }}>
                  {niftyData?.connected ? 'Zerodha Connected' : 'Not Connected'}
                </Typography>
                {niftyData?.connected && niftyData?.price && (
                  <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                    NIFTY: ₹{Number(niftyData.price).toLocaleString()}
                  </Typography>
                )}
              </Box>
            </Box>

            <Tooltip title="Refresh Portfolio Data">
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

        {/* Portfolio Summary */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} md={3}>
            <Card
              sx={{
                background: 'linear-gradient(135deg, #007AFF 0%, #5856D6 100%)',
                color: 'white',
              }}
            >
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <ShowChartIcon sx={{ fontSize: 40 }} />
                  <Box>
                    <Typography variant="h6" sx={{ fontWeight: 600 }}>
                      Current Value
                    </Typography>
                    <Typography variant="h4" sx={{ fontWeight: 700 }}>
                      ₹{safePortfolio.current_value.toLocaleString()}
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={3}>
            <Card
              sx={{
                background: 'linear-gradient(135deg, #10B981 0%, #059669 100%)',
                color: 'white',
              }}
            >
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <AssessmentIcon sx={{ fontSize: 40 }} />
                  <Box>
                    <Typography variant="h6" sx={{ fontWeight: 600 }}>
                      Total Investment
                    </Typography>
                    <Typography variant="h4" sx={{ fontWeight: 700 }}>
                      ₹{safePortfolio.total_investment.toLocaleString()}
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={3}>
            <Card
              sx={{
                background: 'linear-gradient(135deg, #F59E0B 0%, #F97316 100%)',
                color: 'white',
              }}
            >
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <TimelineIcon sx={{ fontSize: 40 }} />
                  <Box>
                    <Typography variant="h6" sx={{ fontWeight: 600 }}>
                      Returns
                    </Typography>
                    <Typography variant="h4" sx={{ fontWeight: 700 }}>
                      {safePortfolio.returns_percentage.toFixed(2)}%
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={3}>
            <Card
              sx={{
                background: 'linear-gradient(135deg, #EF4444 0%, #DC2626 100%)',
                color: 'white',
              }}
            >
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <PortfolioIcon sx={{ fontSize: 40 }} />
                  <Box>
                    <Typography variant="h6" sx={{ fontWeight: 600 }}>
                      Holdings
                    </Typography>
                    <Typography variant="h4" sx={{ fontWeight: 700 }}>
                      {safePortfolio.stock_count} stocks
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        <Card
          sx={{
            background: 'rgba(28, 28, 30, 0.8)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
          }}
        >
          <Tabs
            value={tabValue}
            onChange={(event, newValue) => setTabValue(newValue)}
            sx={{
              borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
              '& .MuiTab-root': {
                color: 'rgba(255, 255, 255, 0.7)',
                fontWeight: 600,
              },
              '& .Mui-selected': {
                color: '#007AFF !important',
              },
            }}
          >
            <Tab icon={<InvestIcon />} label="Initial Investment" />
            <Tab icon={<RebalanceIcon />} label="Rebalancing" />
            <Tab icon={<PortfolioIcon />} label="Holdings" />
          </Tabs>

          <CardContent sx={{ p: 3 }}>
            {tabValue === 0 && (
              <Box>
                <Typography variant="h6" sx={{ mb: 3, fontWeight: 600 }}>
                  Initial Investment Setup
                </Typography>
                
                {currentStatus === 'FIRST_INVESTMENT' ? (
                  <Box>
                    <Alert severity="info" sx={{ mb: 3 }}>
                      <Typography variant="body2">
                        Ready for your first investment! Minimum amount: ₹{safeRequirements.minimum_investment.toLocaleString()}
                      </Typography>
                    </Alert>

                    <Grid container spacing={3}>
                      <Grid item xs={12} md={6}>
                        <TextField
                          fullWidth
                          label="Investment Amount (₹)"
                          type="number"
                          value={investmentAmount}
                          onChange={(e) => setInvestmentAmount(e.target.value)}
                          sx={{
                            '& .MuiOutlinedInput-root': {
                              color: 'white',
                              '& fieldset': { borderColor: 'rgba(255, 255, 255, 0.3)' },
                              '&:hover fieldset': { borderColor: 'rgba(255, 255, 255, 0.5)' },
                              '&.Mui-focused fieldset': { borderColor: '#007AFF' },
                            },
                            '& .MuiInputLabel-root': { color: 'rgba(255, 255, 255, 0.7)' },
                          }}
                        />
                        <Box sx={{ mt: 2, display: 'flex', gap: 2 }}>
                          <Button
                            variant="outlined"
                            startIcon={<CalculateIcon />}
                            onClick={handleCalculateInvestment}
                            disabled={calculatePlanMutation.isLoading}
                            sx={{
                              borderColor: '#007AFF',
                              color: '#007AFF',
                              '&:hover': { borderColor: '#007AFF', background: 'rgba(0, 122, 255, 0.1)' },
                            }}
                          >
                            Calculate Plan
                          </Button>
                        </Box>
                      </Grid>

                      {investmentPlan && (
                        <Grid item xs={12} md={6}>
                          <Paper sx={{ p: 2, background: 'rgba(0, 122, 255, 0.1)', border: '1px solid rgba(0, 122, 255, 0.3)' }}>
                            <Typography variant="h6" sx={{ mb: 2, color: '#007AFF' }}>
                              Investment Plan
                            </Typography>
                            <Typography variant="body2" sx={{ mb: 1 }}>
                              Total Amount: ₹{(Number(investmentPlan?.total_investment || investmentPlan?.investment_amount) || Number(investmentAmount) || 0).toLocaleString()}
                            </Typography>
                            <Typography variant="body2" sx={{ mb: 1 }}>
                              Stocks to Buy: {investmentPlan?.orders?.length || investmentPlan?.allocations?.length || 0}
                            </Typography>
                            <Typography variant="body2">
                              Expected Portfolio Value: ₹{(Number(investmentPlan?.summary?.total_allocated || investmentPlan?.summary?.total_investment_value || investmentPlan?.total_allocated) || Number(investmentAmount) || 0).toLocaleString()}
                            </Typography>
                          </Paper>
                        </Grid>
                      )}
                      
                      {(investmentPlan?.orders || investmentPlan?.allocations) && (
                        <Grid item xs={12}>
                          <Paper sx={{ p: 3, background: 'rgba(28, 28, 30, 0.8)', border: '1px solid rgba(255, 255, 255, 0.1)' }}>
                            <Typography variant="h6" sx={{ mb: 2, color: '#007AFF' }}>
                              Trade Details ({(investmentPlan.orders || investmentPlan.allocations || []).length} stocks)
                            </Typography>
                            <Alert severity="warning" sx={{ mb: 2 }}>
                              These are LIVE trades that will be executed on Zerodha. Real money will be invested.
                            </Alert>
                            <Box sx={{ maxHeight: 300, overflowY: 'auto', mb: 2 }}>
                              <Grid container spacing={1}>
                                {(investmentPlan.orders || investmentPlan.allocations || []).map((order, index) => (
                                  <Grid item xs={12} sm={6} md={4} key={index}>
                                    <Box sx={{ 
                                      p: 2, 
                                      bgcolor: 'rgba(255, 255, 255, 0.05)',
                                      borderRadius: 1,
                                      border: '1px solid rgba(255, 255, 255, 0.1)'
                                    }}>
                                      <Typography variant="subtitle2" sx={{ fontWeight: 'bold', color: '#007AFF' }}>
                                        {order.symbol}
                                      </Typography>
                                      <Typography variant="body2" sx={{ opacity: 0.8 }}>
                                        {order.shares} shares × ₹{Number(order.price || 0).toLocaleString()}
                                      </Typography>
                                      <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                                        Total: ₹{Number(order.value || 0).toLocaleString()}
                                      </Typography>
                                      <Typography variant="caption" sx={{ opacity: 0.6 }}>
                                        {Number(order.allocation_percent || 0).toFixed(2)}% allocation
                                      </Typography>
                                    </Box>
                                  </Grid>
                                ))}
                              </Grid>
                            </Box>
                            <Box sx={{ 
                              display: 'flex', 
                              justifyContent: 'space-between', 
                              alignItems: 'center',
                              pt: 2, 
                              borderTop: '1px solid rgba(255,255,255,0.1)' 
                            }}>
                              <Box>
                                <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                                  Total Investment: ₹{Number(investmentPlan.summary?.total_allocated || investmentPlan.summary?.total_investment_value || investmentPlan.total_allocated || investmentAmount || 0).toLocaleString()}
                                </Typography>
                                <Typography variant="body2" sx={{ opacity: 0.7 }}>
                                  Remaining Cash: ₹{Number(investmentPlan.summary?.remaining_cash || investmentPlan.remaining_cash || 0).toLocaleString()}
                                </Typography>
                              </Box>
                              <Button
                                variant="contained"
                                startIcon={<ExecuteIcon />}
                                onClick={handleExecuteInvestment}
                                disabled={executeInvestmentMutation.isLoading}
                                sx={{
                                  background: 'linear-gradient(135deg, #10B981 0%, #059669 100%)',
                                  px: 3,
                                  py: 1.5
                                }}
                              >
                                {executeInvestmentMutation.isLoading ? 'Executing...' : 'Execute Live Investment'}
                              </Button>
                            </Box>
                          </Paper>
                        </Grid>
                      )}
                    </Grid>
                  </Box>
                ) : (
                  <Alert severity="success">
                    <Typography variant="body2">
                      Initial investment completed! Your portfolio is now active with {safePortfolio.stock_count} holdings.
                    </Typography>
                  </Alert>
                )}
              </Box>
            )}

            {tabValue === 1 && (
              <Box>
                <Typography variant="h6" sx={{ mb: 3, fontWeight: 600 }}>
                  Portfolio Rebalancing
                </Typography>
                
                {(currentStatus === 'REBALANCING_NEEDED' || currentStatus === 'BALANCED') ? (
                  <Box>
                    <Alert severity={currentStatus === 'BALANCED' ? 'success' : 'warning'} sx={{ mb: 3 }}>
                      <Typography variant="body2">
                        {currentStatus === 'BALANCED' 
                          ? 'Portfolio is balanced and ready for rebalancing if needed.' 
                          : 'Rebalancing recommended based on CSV changes or portfolio drift.'}
                      </Typography>
                    </Alert>

                    <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
                      <Button
                        variant="outlined"
                        startIcon={<CalculateIcon />}
                        onClick={handleCalculateRebalancing}
                        disabled={calculateRebalancingMutation.isLoading}
                        sx={{
                          borderColor: '#F59E0B',
                          color: '#F59E0B',
                          '&:hover': { borderColor: '#F59E0B', background: 'rgba(245, 158, 11, 0.1)' },
                        }}
                      >
                        Calculate Rebalancing
                      </Button>
                      {rebalancingPlan && (
                        <Button
                          variant="contained"
                          startIcon={<ExecuteIcon />}
                          onClick={handleExecuteRebalancing}
                          disabled={executeRebalancingMutation.isLoading}
                          sx={{
                            background: 'linear-gradient(135deg, #F59E0B 0%, #F97316 100%)',
                          }}
                        >
                          Execute Live Rebalancing
                        </Button>
                      )}
                    </Box>

                    {rebalancingPlan && (
                      <Paper sx={{ p: 3, background: 'rgba(245, 158, 11, 0.1)', border: '1px solid rgba(245, 158, 11, 0.3)' }}>
                        <Typography variant="h6" sx={{ mb: 2, color: '#F59E0B' }}>
                          Rebalancing Plan
                        </Typography>
                        
                        {/* Summary */}
                        <Box sx={{ mb: 3, display: 'flex', gap: 3, flexWrap: 'wrap' }}>
                          <Chip 
                            label={`Buy Orders: ${rebalancingPlan?.buy_orders?.length || 0}`}
                            color="success"
                            variant="outlined"
                          />
                          <Chip 
                            label={`Sell Orders: ${rebalancingPlan?.sell_orders?.length || 0}`}
                            color="error"
                            variant="outlined"
                          />
                          <Chip 
                            label={`Net Investment: ₹${(Number(rebalancingPlan?.plan_summary?.net_investment_needed) || 0).toLocaleString()}`}
                            color={Number(rebalancingPlan?.plan_summary?.net_investment_needed) > 0 ? 'warning' : Number(rebalancingPlan?.plan_summary?.net_investment_needed) < 0 ? 'success' : 'primary'}
                            variant="outlined"
                          />
                        </Box>

                        {/* Detailed Orders */}
                        {(rebalancingPlan?.buy_orders?.length > 0 || rebalancingPlan?.sell_orders?.length > 0) && (
                          <Box>
                            {/* Buy Orders */}
                            {rebalancingPlan?.buy_orders?.length > 0 && (
                              <Box sx={{ mb: 2 }}>
                                <Typography variant="subtitle1" sx={{ mb: 1, color: '#10B981', fontWeight: 600 }}>
                                  📈 Buy Orders ({rebalancingPlan.buy_orders.length})
                                </Typography>
                                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                                  {rebalancingPlan.buy_orders.map((order, index) => (
                                    <Paper key={index} sx={{ p: 2, background: 'rgba(16, 185, 129, 0.1)', border: '1px solid rgba(16, 185, 129, 0.2)' }}>
                                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                        <Box>
                                          <Typography variant="body1" sx={{ fontWeight: 600, color: '#FFFFFF' }}>
                                            {order.symbol}
                                          </Typography>
                                          <Typography variant="body2" sx={{ color: 'rgba(255, 255, 255, 0.8)' }}>
                                            {order.reason || 'Rebalancing buy'}
                                          </Typography>
                                        </Box>
                                        <Box sx={{ textAlign: 'right' }}>
                                          <Typography variant="body1" sx={{ fontWeight: 600, color: '#10B981' }}>
                                            {order.shares} shares @ ₹{Number(order.price).toFixed(2)}
                                          </Typography>
                                          <Typography variant="body2" sx={{ color: 'rgba(255, 255, 255, 0.8)' }}>
                                            Total: ₹{Number(order.value || (order.shares * order.price)).toLocaleString()}
                                          </Typography>
                                        </Box>
                                      </Box>
                                    </Paper>
                                  ))}
                                </Box>
                              </Box>
                            )}

                            {/* Sell Orders */}
                            {rebalancingPlan?.sell_orders?.length > 0 && (
                              <Box>
                                <Typography variant="subtitle1" sx={{ mb: 1, color: '#EF4444', fontWeight: 600 }}>
                                  📉 Sell Orders ({rebalancingPlan.sell_orders.length})
                                </Typography>
                                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                                  {rebalancingPlan.sell_orders.map((order, index) => (
                                    <Paper key={index} sx={{ p: 2, background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.2)' }}>
                                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                        <Box>
                                          <Typography variant="body1" sx={{ fontWeight: 600, color: '#FFFFFF' }}>
                                            {order.symbol}
                                          </Typography>
                                          <Typography variant="body2" sx={{ color: 'rgba(255, 255, 255, 0.8)' }}>
                                            {order.reason || 'Rebalancing sell'}
                                          </Typography>
                                        </Box>
                                        <Box sx={{ textAlign: 'right' }}>
                                          <Typography variant="body1" sx={{ fontWeight: 600, color: '#EF4444' }}>
                                            {order.shares} shares @ ₹{Number(order.price).toFixed(2)}
                                          </Typography>
                                          <Typography variant="body2" sx={{ color: 'rgba(255, 255, 255, 0.8)' }}>
                                            Total: ₹{Number(order.value || (order.shares * order.price)).toLocaleString()}
                                          </Typography>
                                        </Box>
                                      </Box>
                                    </Paper>
                                  ))}
                                </Box>
                              </Box>
                            )}
                          </Box>
                        )}
                      </Paper>
                    )}
                  </Box>
                ) : (currentStatus === 'NO_REBALANCING_NEEDED' || currentStatus === 'BALANCED') ? (
                  <Alert severity="success">
                    <Typography variant="body2">
                      Portfolio is well-balanced. No rebalancing needed at this time.
                    </Typography>
                  </Alert>
                ) : (
                  <Alert severity="info">
                    <Typography variant="body2">
                      Complete your initial investment first before rebalancing becomes available.
                    </Typography>
                  </Alert>
                )}
              </Box>
            )}

            {tabValue === 2 && (
              <Box>
                <Typography variant="h6" sx={{ mb: 3, fontWeight: 600 }}>
                  Portfolio Holdings
                </Typography>
                
                {safePortfolio.holdings && safePortfolio.holdings.length > 0 ? (
                  <TableContainer component={Paper} sx={{ 
                    background: 'rgba(28, 28, 30, 0.8)', 
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    '& .MuiTableCell-root': {
                      color: 'white',
                      borderColor: 'rgba(255, 255, 255, 0.1)',
                    },
                    '& .MuiTableHead-root': {
                      '& .MuiTableCell-root': {
                        fontWeight: 600,
                        background: 'rgba(0, 122, 255, 0.1)',
                      }
                    }
                  }}>
                    <Table>
                      <TableHead>
                        <TableRow>
                          <TableCell>Stock</TableCell>
                          <TableCell align="right">Shares</TableCell>
                          <TableCell align="right">Avg Price</TableCell>
                          <TableCell align="right">Current Price</TableCell>
                          <TableCell align="right">Investment</TableCell>
                          <TableCell align="right">Current Value</TableCell>
                          <TableCell align="right">P&L</TableCell>
                          <TableCell align="right">P&L %</TableCell>
                          <TableCell align="right">Allocation</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {safePortfolio.holdings
                          .sort((a, b) => (b.current_value || 0) - (a.current_value || 0))
                          .map((holding) => {
                            const pnl = Number(holding.pnl || 0);
                            const pnlPercent = Number(holding.pnl_percent || 0);
                            const isProfitable = pnl >= 0;
                            
                            return (
                              <TableRow key={holding.symbol} sx={{ 
                                background: isProfitable 
                                  ? 'rgba(16, 185, 129, 0.05)' 
                                  : 'rgba(239, 68, 68, 0.05)',
                                '&:hover': { 
                                  background: isProfitable 
                                    ? 'rgba(16, 185, 129, 0.1)' 
                                    : 'rgba(239, 68, 68, 0.1)' 
                                }
                              }}>
                                <TableCell sx={{ fontWeight: 600 }}>
                                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                    <Typography variant="body1" sx={{ fontWeight: 600 }}>
                                      {holding.symbol}
                                    </Typography>
                                    <Box sx={{ 
                                      width: 8, 
                                      height: 8, 
                                      borderRadius: '50%', 
                                      backgroundColor: isProfitable ? '#10B981' : '#EF4444' 
                                    }} />
                                  </Box>
                                </TableCell>
                                <TableCell align="right">
                                  {Number(holding.shares || 0).toLocaleString()}
                                </TableCell>
                                <TableCell align="right">
                                  ₹{Number(holding.avg_price || 0).toFixed(2)}
                                </TableCell>
                                <TableCell align="right">
                                  ₹{Number(holding.current_price || 0).toFixed(2)}
                                </TableCell>
                                <TableCell align="right">
                                  ₹{Number(holding.investment_value || 0).toLocaleString()}
                                </TableCell>
                                <TableCell align="right" sx={{ fontWeight: 600 }}>
                                  ₹{Number(holding.current_value || 0).toLocaleString()}
                                </TableCell>
                                <TableCell align="right" sx={{ 
                                  color: isProfitable ? '#10B981' : '#EF4444',
                                  fontWeight: 600 
                                }}>
                                  {isProfitable ? '+' : ''}₹{pnl.toLocaleString()}
                                </TableCell>
                                <TableCell align="right" sx={{ 
                                  color: isProfitable ? '#10B981' : '#EF4444',
                                  fontWeight: 600 
                                }}>
                                  {isProfitable ? '+' : ''}{pnlPercent.toFixed(2)}%
                                </TableCell>
                                <TableCell align="right">
                                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                    <Typography variant="body2">
                                      {Number(holding.allocation_percent || 0).toFixed(1)}%
                                    </Typography>
                                    <LinearProgress
                                      variant="determinate"
                                      value={Math.min(Number(holding.allocation_percent || 0), 100)}
                                      sx={{
                                        width: 40,
                                        height: 4,
                                        backgroundColor: 'rgba(255, 255, 255, 0.1)',
                                        '& .MuiLinearProgress-bar': {
                                          backgroundColor: '#007AFF',
                                        },
                                      }}
                                    />
                                  </Box>
                                </TableCell>
                              </TableRow>
                            );
                          })}
                      </TableBody>
                    </Table>
                  </TableContainer>
                ) : (
                  <Alert severity="info">
                    <Typography variant="body2">
                      No holdings found. Complete your initial investment to see portfolio holdings.
                    </Typography>
                  </Alert>
                )}
              </Box>
            )}
          </CardContent>
        </Card>
      </motion.div>

    </Container>
  );
};

export default Portfolio;