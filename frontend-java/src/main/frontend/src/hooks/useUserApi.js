// frontend-java/src/main/frontend/src/hooks/useUserApi.js - User Authentication API Hooks
import { useQuery, useMutation, useQueryClient } from 'react-query';
import axios from 'axios';
import toast from 'react-hot-toast';
import { useUser } from '../contexts/UserContext';

// Configure axios defaults
axios.defaults.baseURL = 'http://localhost:8002/api';
axios.defaults.timeout = 30000;

// Add request interceptor to include auth token
axios.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor to handle auth errors
axios.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid - logout user
      localStorage.removeItem('auth_token');
      localStorage.removeItem('user_data');
      window.location.reload();
    }
    return Promise.reject(error);
  }
);

// User Management API functions
const userApi = {
  // Authentication
  register: (userData) => 
    axios.post('/register', userData).then(res => res.data),
  
  login: (credentials) => 
    axios.post('/login', credentials).then(res => res.data),
  
  getCurrentUser: () => 
    axios.get('/users/me').then(res => res.data),

  // Zerodha Authentication (user-specific)
  getAuthStatus: () => 
    axios.get('/auth-status').then(res => res.data),
  
  getZerodhaLoginUrl: () => 
    axios.get('/zerodha-login-url').then(res => res.data),
  
  exchangeZerodhaToken: (tokenData) => 
    axios.post('/exchange-token', tokenData).then(res => res.data),
  
  autoAuthenticateZerodha: () => 
    axios.post('/auto-authenticate').then(res => res.data),

  // Investment APIs (user-specific)
  getInvestmentStatus: () => 
    axios.get('/investment/status').then(res => res.data),
  
  getPortfolioStatus: () => 
    axios.get('/investment/portfolio-status').then(res => res.data),
  
  getSystemOrders: () => 
    axios.get('/investment/system-orders').then(res => res.data),
  
  getCsvStocks: () => 
    axios.get('/investment/csv-stocks').then(res => res.data),
  
  getLiveOrders: () => 
    axios.get('/investment/live-orders').then(res => res.data),
  
  getFailedOrders: () => 
    axios.get('/investment/failed-orders').then(res => res.data),
  
  getOrdersWithRetries: () => 
    axios.get('/investment/orders-with-retries').then(res => res.data),
  
  getMonitoringStatus: () => 
    axios.get('/investment/monitoring-status').then(res => res.data),

  // Health check
  getHealth: () => 
    axios.get('/api/health').then(res => res.data),

  // Investment requirements (user-specific)
  getInvestmentRequirements: () => 
    axios.get('/investment/requirements').then(res => res.data),

  // Order monitoring APIs
  startOrderMonitoring: () => 
    axios.post('/investment/start-monitoring').then(res => res.data),
  
  stopOrderMonitoring: () => 
    axios.post('/investment/stop-monitoring').then(res => res.data),
  
  updateOrderStatusFromZerodha: (zerodhaOrderId = null) => 
    axios.post('/investment/update-order-status', { zerodha_order_id: zerodhaOrderId }).then(res => res.data)
};

// === USER MANAGEMENT HOOKS ===

export const useRegisterMutation = () => {
  return useMutation(userApi.register, {
    onSuccess: (data) => {
      console.log('Registration success response:', data);
      if (data.success) {
        toast.success(data.message);
      } else {
        console.error('Registration failed (success=false):', data);
        toast.error(data.message || 'Registration failed');
      }
    },
    onError: (error) => {
      console.error('Registration error:', error);
      console.error('Error response:', error.response?.data);
      console.error('Error status:', error.response?.status);
      
      const message = error.response?.data?.detail || error.response?.data?.message || error.message || 'Registration failed';
      toast.error(`Registration failed: ${message}`);
    },
  });
};

export const useLoginMutation = () => {
  return useMutation(userApi.login, {
    onSuccess: (data) => {
      if (data.success) {
        toast.success(data.message);
      } else {
        toast.error(data.message || 'Login failed');
      }
    },
    onError: (error) => {
      const message = error.response?.data?.detail || 'Login failed';
      toast.error(message);
    },
  });
};

export const useCurrentUser = () => {
  const { isAuthenticated } = useUser();
  
  return useQuery(
    'currentUser',
    userApi.getCurrentUser,
    {
      enabled: isAuthenticated(),
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5 minutes
      onError: (error) => {
        if (error.response?.status !== 401) {
          console.error('Failed to fetch current user:', error);
        }
      },
    }
  );
};

// === ZERODHA AUTHENTICATION HOOKS (USER-SPECIFIC) ===

export const useUserAuthStatus = () => {
  const { isAuthenticated } = useUser();
  
  return useQuery(
    'userAuthStatus',
    userApi.getAuthStatus,
    {
      enabled: isAuthenticated(),
      refetchInterval: 60000, // Refetch every minute (reduced from 15s)
      staleTime: 30000, // Consider stale after 30 seconds
      cacheTime: 60000, // Keep in cache for 1 minute
      retry: 2,
      refetchOnMount: true, // Always refetch when component mounts
      refetchOnWindowFocus: true, // Refetch when window gains focus
      onSuccess: (data) => {
        console.log('Auth status updated:', data?.authenticated ? 'Connected' : 'Not Connected', data);
      },
      onError: (error) => {
        if (error.response?.status !== 401) {
          console.error('Auth status check failed:', error);
        }
      },
    }
  );
};

export const useZerodhaLoginUrlQuery = () => {
  const { isAuthenticated } = useUser();
  
  return useQuery(
    'zerodhaLoginUrl',
    userApi.getZerodhaLoginUrl,
    {
      enabled: false, // Only fetch when explicitly requested
      staleTime: 5 * 60 * 1000, // 5 minutes
      retry: 1,
    }
  );
};

export const useZerodhaTokenExchangeMutation = () => {
  const queryClient = useQueryClient();
  
  return useMutation(userApi.exchangeZerodhaToken, {
    onSuccess: (data) => {
      if (data.success) {
        toast.success(`Zerodha connected successfully! Profile: ${data.profile_name}`);
        // Invalidate auth status to trigger refetch
        queryClient.invalidateQueries('userAuthStatus');
        queryClient.invalidateQueries('investmentStatus');
        queryClient.invalidateQueries('portfolioStatus');
      } else {
        toast.error(data.error || 'Zerodha authentication failed');
      }
    },
    onError: (error) => {
      const message = error.response?.data?.detail || 'Zerodha authentication failed';
      toast.error(message);
    },
  });
};

export const useAutoAuthenticateZerodhaMutation = () => {
  const queryClient = useQueryClient();
  
  return useMutation(userApi.autoAuthenticateZerodha, {
    onSuccess: (data) => {
      if (data.success) {
        toast.success(`Auto-authentication successful! Profile: ${data.profile_name}`);
        // Invalidate auth status to trigger refetch
        queryClient.invalidateQueries('userAuthStatus');
        queryClient.invalidateQueries('investmentStatus');
        queryClient.invalidateQueries('portfolioStatus');
      } else {
        toast.error(data.error || 'Auto-authentication failed');
      }
    },
    onError: (error) => {
      const message = error.response?.data?.error || 'Auto-authentication failed';
      toast.error(message);
    },
  });
};

// === INVESTMENT HOOKS (USER-SPECIFIC) ===

export const useUserInvestmentStatus = () => {
  const { isAuthenticated } = useUser();
  const authStatus = useUserAuthStatus();
  
  return useQuery(
    ['userInvestmentStatus', 'v3'], // Add version to force cache invalidation
    userApi.getInvestmentStatus,
    {
      enabled: true, // Temporarily force query to always run for debugging
      refetchInterval: 30000, // Refetch every 30 seconds (reduced from 5s)
      staleTime: 10000, // Consider stale after 10 seconds
      cacheTime: 30000, // Keep in cache for 30 seconds
      retry: 2,
      onError: (error) => {
        console.error('Investment status fetch failed:', error);
      },
    }
  );
};

export const useUserInvestmentRequirements = () => {
  const { isAuthenticated } = useUser();
  const authStatus = useUserAuthStatus();
  
  return useQuery(
    'userInvestmentRequirements',
    userApi.getInvestmentRequirements,
    {
      enabled: isAuthenticated() && authStatus.data?.authenticated,
      refetchInterval: 60000, // Refetch every minute
      staleTime: 30000, // Consider stale after 30 seconds
      retry: 2,
      onError: (error) => {
        console.error('Investment requirements fetch failed:', error);
      },
    }
  );
};

export const useUserPortfolioStatus = () => {
  const { isAuthenticated } = useUser();
  const authStatus = useUserAuthStatus();
  
  return useQuery(
    'userPortfolioStatus',
    userApi.getPortfolioStatus,
    {
      enabled: isAuthenticated() && authStatus.data?.authenticated,
      refetchInterval: 30000, // Refetch every 30 seconds
      staleTime: 15000, // Consider stale after 15 seconds
      retry: 2,
      onError: (error) => {
        console.error('Portfolio status fetch failed:', error);
      },
    }
  );
};

export const useUserSystemOrders = () => {
  const { isAuthenticated } = useUser();
  const authStatus = useUserAuthStatus();
  
  return useQuery(
    'userSystemOrders',
    userApi.getSystemOrders,
    {
      enabled: isAuthenticated() && authStatus.data?.authenticated,
      refetchInterval: 30000, // Refetch every 30 seconds
      staleTime: 15000, // Consider stale after 15 seconds
      retry: 2,
      onError: (error) => {
        console.error('System orders fetch failed:', error);
      },
    }
  );
};

export const useUserCsvStocks = () => {
  const { isAuthenticated } = useUser();
  const authStatus = useUserAuthStatus();
  
  return useQuery(
    'userCsvStocks',
    userApi.getCsvStocks,
    {
      enabled: isAuthenticated() && authStatus.data?.authenticated,
      refetchInterval: 60000, // Refetch every minute (stocks data)
      staleTime: 30000, // Consider stale after 30 seconds
      retry: 2,
      onError: (error) => {
        console.error('CSV stocks fetch failed:', error);
      },
    }
  );
};

export const useUserLiveOrders = () => {
  const { isAuthenticated } = useUser();
  const authStatus = useUserAuthStatus();
  
  return useQuery(
    'userLiveOrders',
    userApi.getLiveOrders,
    {
      enabled: isAuthenticated() && authStatus.data?.authenticated,
      refetchInterval: 30000, // Refetch every 30 seconds (reduced from 10s)
      staleTime: 15000, // Consider stale after 15 seconds
      retry: 2,
      onError: (error) => {
        console.error('Live orders fetch failed:', error);
      },
    }
  );
};

export const useUserFailedOrders = () => {
  const { isAuthenticated } = useUser();
  const authStatus = useUserAuthStatus();
  
  return useQuery(
    'userFailedOrders',
    userApi.getFailedOrders,
    {
      enabled: isAuthenticated() && authStatus.data?.authenticated,
      refetchInterval: 30000, // Refetch every 30 seconds
      staleTime: 15000, // Consider stale after 15 seconds
      retry: 2,
      onError: (error) => {
        console.error('Failed orders fetch failed:', error);
      },
    }
  );
};

export const useUserOrdersWithRetries = () => {
  const { isAuthenticated } = useUser();
  const authStatus = useUserAuthStatus();
  
  return useQuery(
    'userOrdersWithRetries',
    userApi.getOrdersWithRetries,
    {
      enabled: isAuthenticated() && authStatus.data?.authenticated,
      refetchInterval: 30000, // Refetch every 30 seconds
      staleTime: 15000, // Consider stale after 15 seconds
      retry: 2,
      onError: (error) => {
        console.error('Orders with retries fetch failed:', error);
      },
    }
  );
};

export const useUserMonitoringStatus = () => {
  const { isAuthenticated } = useUser();
  const authStatus = useUserAuthStatus();
  
  return useQuery(
    'userMonitoringStatus',
    userApi.getMonitoringStatus,
    {
      enabled: isAuthenticated() && authStatus.data?.authenticated,
      refetchInterval: 60000, // Refetch every minute (reduced from 15s)
      staleTime: 30000, // Consider stale after 30 seconds
      retry: 2,
      onError: (error) => {
        console.error('Monitoring status fetch failed:', error);
      },
    }
  );
};

// === USER-SPECIFIC INVESTMENT MUTATIONS ===

export const useUserCalculateInvestmentPlanMutation = () => {
  const queryClient = useQueryClient();
  
  return useMutation(
    (investmentAmount) => axios.post('/investment/calculate-plan', { investment_amount: investmentAmount }).then(res => res.data),
    {
      onSuccess: (data) => {
        if (data.success) {
          toast.success('Investment plan calculated successfully');
        } else {
          toast.error(data.error || 'Failed to calculate investment plan');
        }
      },
      onError: (error) => {
        const message = error.response?.data?.detail || error.response?.data?.error || 'Failed to calculate investment plan';
        toast.error(message);
      },
    }
  );
};

export const useUserExecuteInitialInvestmentMutation = () => {
  const queryClient = useQueryClient();
  
  return useMutation(
    (investmentAmount) => axios.post('/investment/execute-initial', { investment_amount: investmentAmount }).then(res => res.data),
    {
      onSuccess: (data) => {
        if (data.success) {
          toast.success('Initial investment executed successfully!');
          queryClient.invalidateQueries('userInvestmentStatus');
          queryClient.invalidateQueries('userPortfolioStatus');
          queryClient.invalidateQueries('userSystemOrders');
        } else {
          toast.error(data.error || 'Failed to execute initial investment');
        }
      },
      onError: (error) => {
        const message = error.response?.data?.detail || error.response?.data?.error || 'Failed to execute initial investment';
        toast.error(message);
      },
    }
  );
};

export const useUserCalculateRebalancingMutation = () => {
  const queryClient = useQueryClient();
  
  return useMutation(
    (additionalInvestment = 0) => axios.post('/investment/calculate-rebalancing', { additional_investment: additionalInvestment }).then(res => res.data),
    {
      onSuccess: (data) => {
        if (data.success) {
          toast.success('Rebalancing plan calculated successfully');
        } else {
          toast.error(data.error || 'Failed to calculate rebalancing');
        }
      },
      onError: (error) => {
        const message = error.response?.data?.detail || error.response?.data?.error || 'Failed to calculate rebalancing';
        toast.error(message);
      },
    }
  );
};

export const useUserExecuteRebalancingMutation = () => {
  const queryClient = useQueryClient();
  
  return useMutation(
    (additionalInvestment = 0) => axios.post('/investment/execute-rebalancing', { additional_investment: additionalInvestment }).then(res => res.data),
    {
      onSuccess: (data) => {
        if (data.success) {
          toast.success('Rebalancing executed successfully!');
          queryClient.invalidateQueries('userInvestmentStatus');
          queryClient.invalidateQueries('userPortfolioStatus');
        } else {
          toast.error(data.error || 'Failed to execute rebalancing');
        }
      },
      onError: (error) => {
        const message = error.response?.data?.detail || error.response?.data?.error || 'Failed to execute rebalancing';
        toast.error(message);
      },
    }
  );
};

export const useUserForceCsvRefreshMutation = () => {
  const queryClient = useQueryClient();
  
  return useMutation(
    () => axios.post('/investment/force-csv-refresh').then(res => res.data),
    {
      onSuccess: (data) => {
        if (data.success) {
          toast.success('CSV data refreshed successfully');
          queryClient.invalidateQueries('userCsvStocks');
        } else {
          toast.error(data.error || 'Failed to refresh CSV data');
        }
      },
      onError: (error) => {
        const message = error.response?.data?.detail || error.response?.data?.error || 'Failed to refresh CSV data';
        toast.error(message);
      },
    }
  );
};

export const useUserRetryFailedOrdersMutation = () => {
  const queryClient = useQueryClient();
  
  return useMutation(
    (orderIds) => axios.post('/investment/retry-orders', { order_ids: orderIds }).then(res => res.data),
    {
      onSuccess: (data) => {
        if (data.success) {
          toast.success('Failed orders retried successfully');
          queryClient.invalidateQueries('userFailedOrders');
          queryClient.invalidateQueries('userLiveOrders');
        } else {
          toast.error(data.error || 'Failed to retry orders');
        }
      },
      onError: (error) => {
        const message = error.response?.data?.detail || error.response?.data?.error || 'Failed to retry orders';
        toast.error(message);
      },
    }
  );
};

export const useUserResetSystemOrdersMutation = () => {
  const queryClient = useQueryClient();
  
  return useMutation(() => axios.post('/investment/reset-orders').then(res => res.data), {
    onSuccess: (data) => {
      if (data.success) {
        toast.success('System orders reset successfully!');
        // Invalidate related queries
        queryClient.invalidateQueries('userSystemOrders');
        queryClient.invalidateQueries('userPortfolioStatus');
        queryClient.invalidateQueries('userInvestmentStatus');
      } else {
        toast.error(data.error || 'Failed to reset system orders');
      }
    },
    onError: (error) => {
      const message = error.response?.data?.detail || error.response?.data?.error || 'Failed to reset system orders';
      toast.error(message);
    },
  });
};

export const useUserUpdateLiveOrderStatusMutation = () => {
  const queryClient = useQueryClient();
  
  return useMutation(
    (orderData) => axios.post('/investment/update-order-status', orderData).then(res => res.data),
    {
      onSuccess: (data) => {
        if (data.success) {
          toast.success('Order status updated');
          queryClient.invalidateQueries('userLiveOrders');
        } else {
          toast.error('Failed to update order status');
        }
      },
      onError: (error) => {
        const message = error.response?.data?.detail || error.response?.data?.error || 'Failed to update order status';
        toast.error(message);
      },
    }
  );
};

// === ORDER MONITORING HOOKS ===

export const useStartOrderMonitoringMutation = () => {
  const queryClient = useQueryClient();
  
  return useMutation(userApi.startOrderMonitoring, {
    onSuccess: (data) => {
      if (data.success) {
        toast.success('Order monitoring started successfully!');
        queryClient.invalidateQueries('userMonitoringStatus');
        queryClient.invalidateQueries('userLiveOrders');
      } else {
        toast.error(data.error || 'Failed to start order monitoring');
      }
    },
    onError: (error) => {
      const message = error.response?.data?.detail || error.response?.data?.error || 'Failed to start order monitoring';
      toast.error(message);
    },
  });
};

export const useStopOrderMonitoringMutation = () => {
  const queryClient = useQueryClient();
  
  return useMutation(userApi.stopOrderMonitoring, {
    onSuccess: (data) => {
      if (data.success) {
        toast.success('Order monitoring stopped successfully');
        queryClient.invalidateQueries('userMonitoringStatus');
      } else {
        toast.error(data.error || 'Failed to stop order monitoring');
      }
    },
    onError: (error) => {
      const message = error.response?.data?.detail || error.response?.data?.error || 'Failed to stop order monitoring';
      toast.error(message);
    },
  });
};

export const useUpdateOrderStatusFromZerodhaMutation = () => {
  const queryClient = useQueryClient();
  
  return useMutation(userApi.updateOrderStatusFromZerodha, {
    onSuccess: (data) => {
      if (data.success && data.result?.success) {
        const result = data.result;
        if (result.updated_count !== undefined) {
          toast.success(`Updated ${result.updated_count} orders from Zerodha`);
        } else {
          toast.success('Order status updated from Zerodha');
        }
        // Refresh all order-related queries
        queryClient.invalidateQueries('userLiveOrders');
        queryClient.invalidateQueries('userSystemOrders');
        queryClient.invalidateQueries('userFailedOrders');
        queryClient.invalidateQueries('userMonitoringStatus');
      } else {
        toast.error(data.result?.error || data.error || 'Failed to update order status');
      }
    },
    onError: (error) => {
      const message = error.response?.data?.detail || error.response?.data?.error || 'Failed to update order status from Zerodha';
      toast.error(message);
    },
  });
};

// === HEALTH CHECK ===

export const useHealthStatus = () => {
  return useQuery(
    'healthStatus',
    userApi.getHealth,
    {
      refetchInterval: 60000, // Refetch every minute
      staleTime: 30000, // Consider stale after 30 seconds
      retry: 1,
      onError: (error) => {
        console.error('Health check failed:', error);
      },
    }
  );
};