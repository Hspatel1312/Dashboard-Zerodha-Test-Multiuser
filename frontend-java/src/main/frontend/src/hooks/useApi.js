import { useQuery, useMutation, useQueryClient } from 'react-query';
import axios from 'axios';
import toast from 'react-hot-toast';

// Configure axios defaults
axios.defaults.baseURL = 'http://localhost:8000/api';
axios.defaults.timeout = 30000;

// API functions
const api = {
  // Auth endpoints
  getAuthStatus: () => axios.get('/auth-status').then(res => res.data),
  getZerodhaLoginUrl: () => axios.get('/zerodha-login-url').then(res => res.data),
  exchangeToken: (requestToken) => 
    axios.post('/exchange-token', { request_token: requestToken }).then(res => res.data),
  autoAuthenticate: () => axios.post('/auto-authenticate').then(res => res.data),

  // Investment endpoints
  getInvestmentStatus: () => axios.get('/investment/status').then(res => res.data),
  getInvestmentRequirements: () => axios.get('/investment/requirements').then(res => res.data),
  calculateInvestmentPlan: (amount) => {
    console.log('API: Sending calculate investment plan request:', { investment_amount: amount });
    return axios.post('/investment/calculate-plan', { investment_amount: amount }, {
      headers: {
        'Content-Type': 'application/json',
      }
    }).then(res => {
      console.log('API: Calculate investment plan response:', res.data);
      return res.data;
    }).catch(error => {
      console.error('API: Calculate investment plan error:', error);
      console.error('API: Error response data:', error.response?.data);
      console.error('API: Error response status:', error.response?.status);
      console.error('API: Error response headers:', error.response?.headers);
      throw error;
    });
  },
  executeInitialInvestment: (amount) => 
    axios.post('/investment/execute-initial', { investment_amount: amount }).then(res => res.data),

  // Portfolio endpoints
  getPortfolioStatus: () => axios.get('/investment/portfolio-status').then(res => res.data),
  getSystemOrders: () => axios.get('/investment/system-orders').then(res => res.data),

  // Stocks endpoints
  getCsvStocks: () => axios.get('/investment/csv-stocks').then(res => res.data),
  forceCsvRefresh: () => axios.post('/investment/force-csv-refresh').then(res => res.data),

  // Rebalancing endpoints
  calculateRebalancing: (additionalInvestment = 0) => 
    axios.post('/investment/calculate-rebalancing', { additional_investment: additionalInvestment }).then(res => res.data),
  executeRebalancing: (additionalInvestment = 0) => 
    axios.post('/investment/execute-rebalancing', { additional_investment: additionalInvestment }).then(res => res.data),

  // Health endpoint
  getHealthStatus: () => axios.get('/health').then(res => res.data),

  // Failed orders and retry endpoints
  getFailedOrders: () => axios.get('/investment/failed-orders').then(res => res.data),
  getOrdersWithRetries: () => axios.get('/investment/orders-with-retries').then(res => res.data),
  retryFailedOrders: (orderIds = null) => 
    axios.post('/investment/retry-orders', { order_ids: orderIds }).then(res => res.data),

  // Live orders endpoints
  getLiveOrders: () => axios.get('/investment/live-orders').then(res => res.data),
  getLiveOrderStatus: (orderId) => axios.get(`/investment/live-orders/${orderId}/status`).then(res => res.data),
  updateLiveOrderStatus: (orderId) => axios.post(`/investment/live-orders/${orderId}/update`).then(res => res.data),
  startLiveMonitoring: () => axios.post('/investment/live-orders/start-monitoring').then(res => res.data),
  stopLiveMonitoring: () => axios.post('/investment/live-orders/stop-monitoring').then(res => res.data),
  executeLiveOrders: (data) => axios.post('/investment/execute-live-orders', data).then(res => res.data),
};

// Custom hooks for queries
export const useAuthStatus = () => {
  return useQuery(
    'authStatus',
    api.getAuthStatus,
    {
      refetchInterval: 30000, // Refetch every 30 seconds
      staleTime: 15000, // Consider stale after 15 seconds
      retry: 2,
      onError: (error) => {
        console.error('Auth status check failed:', error);
      },
    }
  );
};

export const useInvestmentStatus = () => {
  return useQuery(
    'investmentStatus',
    api.getInvestmentStatus,
    {
      staleTime: 60000, // 1 minute
      retry: 1,
      onError: (error) => {
        toast.error('Failed to load investment status');
      },
    }
  );
};

export const useInvestmentRequirements = () => {
  return useQuery(
    'investmentRequirements',
    api.getInvestmentRequirements,
    {
      staleTime: 300000, // 5 minutes
      retry: 1,
      onError: (error) => {
        toast.error('Failed to load investment requirements');
      },
    }
  );
};

export const usePortfolioStatus = () => {
  return useQuery(
    'portfolioStatus',
    api.getPortfolioStatus,
    {
      staleTime: 30000, // 30 seconds
      retry: 1,
      onError: (error) => {
        toast.error('Failed to load portfolio status');
      },
    }
  );
};

export const useSystemOrders = () => {
  return useQuery(
    'systemOrders',
    api.getSystemOrders,
    {
      staleTime: 60000, // 1 minute
      retry: 1,
      onError: (error) => {
        toast.error('Failed to load system orders');
      },
    }
  );
};

export const useCsvStocks = () => {
  return useQuery(
    'csvStocks',
    api.getCsvStocks,
    {
      staleTime: 300000, // 5 minutes
      retry: 1,
      onError: (error) => {
        toast.error('Failed to load CSV stocks');
      },
    }
  );
};

export const useHealthStatus = () => {
  return useQuery(
    'healthStatus',
    api.getHealthStatus,
    {
      refetchInterval: 60000, // Refetch every minute
      staleTime: 30000, // 30 seconds
      retry: 2,
      onError: (error) => {
        console.error('Health check failed:', error);
      },
    }
  );
};

// Custom hooks for mutations
export const useZerodhaLoginMutation = () => {
  return useMutation(api.getZerodhaLoginUrl, {
    onSuccess: (data) => {
      if (data.success) {
        toast.success('Login URL generated successfully');
      } else {
        toast.error(data.error || 'Failed to generate login URL');
      }
    },
    onError: () => {
      toast.error('Failed to generate login URL');
    },
  });
};

export const useTokenExchangeMutation = () => {
  const queryClient = useQueryClient();
  
  return useMutation(api.exchangeToken, {
    onSuccess: (data) => {
      if (data.success) {
        toast.success(`Welcome ${data.profile_name}! Successfully authenticated.`);
        // Invalidate auth status to trigger refetch
        queryClient.invalidateQueries('authStatus');
        queryClient.invalidateQueries('investmentStatus');
      } else {
        toast.error(data.error || 'Token exchange failed');
      }
    },
    onError: () => {
      toast.error('Token exchange failed');
    },
  });
};

export const useAutoAuthenticateMutation = () => {
  const queryClient = useQueryClient();
  
  return useMutation(api.autoAuthenticate, {
    onSuccess: (data) => {
      if (data.success) {
        toast.success(`Welcome ${data.profile_name}! Automatic authentication successful.`);
        // Invalidate auth status to trigger refetch
        queryClient.invalidateQueries('authStatus');
        queryClient.invalidateQueries('investmentStatus');
      } else {
        toast.error(data.error || 'Automatic authentication failed');
      }
    },
    onError: () => {
      toast.error('Automatic authentication failed');
    },
  });
};

export const useCalculateInvestmentPlanMutation = () => {
  return useMutation(api.calculateInvestmentPlan, {
    onSuccess: (data) => {
      console.log('Investment plan calculation success:', data);
      if (data.success) {
        toast.success('Investment plan calculated successfully');
      } else {
        toast.error(data.error || 'Failed to calculate investment plan');
      }
    },
    onError: (error) => {
      console.error('Investment plan calculation mutation error:', error);
      console.error('Error response:', error.response);
      
      let errorMessage = 'Failed to calculate investment plan';
      if (error?.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      } else if (error?.response?.data?.message) {
        errorMessage = error.response.data.message;
      } else if (error?.message) {
        errorMessage = error.message;
      }
      
      toast.error(`Error: ${errorMessage}`);
    },
  });
};

export const useExecuteInitialInvestmentMutation = () => {
  const queryClient = useQueryClient();
  
  return useMutation(api.executeInitialInvestment, {
    onSuccess: (data) => {
      if (data.success) {
        toast.success('Initial investment executed successfully!');
        // Invalidate related queries
        queryClient.invalidateQueries('investmentStatus');
        queryClient.invalidateQueries('portfolioStatus');
        queryClient.invalidateQueries('systemOrders');
      } else {
        toast.error(data.error || 'Failed to execute investment');
      }
    },
    onError: () => {
      toast.error('Failed to execute investment');
    },
  });
};

export const useForceCsvRefreshMutation = () => {
  const queryClient = useQueryClient();
  
  return useMutation(api.forceCsvRefresh, {
    onSuccess: (data) => {
      if (data.success) {
        const message = data.data?.csv_changed 
          ? 'CSV refreshed - changes detected!' 
          : 'CSV refreshed - no changes';
        toast.success(message);
        // Invalidate related queries
        queryClient.invalidateQueries('csvStocks');
        queryClient.invalidateQueries('investmentStatus');
      } else {
        toast.error(data.error || 'Failed to refresh CSV');
      }
    },
    onError: () => {
      toast.error('Failed to refresh CSV');
    },
  });
};

export const useCalculateRebalancingMutation = () => {
  return useMutation(api.calculateRebalancing, {
    onSuccess: (data) => {
      if (data.success) {
        toast.success('Rebalancing plan calculated successfully');
      } else {
        toast.error(data.error || 'Failed to calculate rebalancing plan');
      }
    },
    onError: (error) => {
      console.error('Rebalancing calculation error:', error);
      let errorMessage = 'Failed to calculate rebalancing plan';
      if (error?.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      }
      toast.error(errorMessage);
    },
  });
};

export const useExecuteRebalancingMutation = () => {
  const queryClient = useQueryClient();
  
  return useMutation(api.executeRebalancing, {
    onSuccess: (data) => {
      console.log('Execute rebalancing mutation success:', data);
      // Invalidate related queries
      queryClient.invalidateQueries('investmentStatus');
      queryClient.invalidateQueries('portfolioStatus');
      queryClient.invalidateQueries('systemOrders');
      // Don't show toast here - let the component handle it
    },
    onError: (error) => {
      console.error('Execute rebalancing mutation error:', error);
      console.error('Error response:', error.response);
      // Don't show toast here - let the component handle it
    },
  });
};

export const useResetSystemOrdersMutation = () => {
  const queryClient = useQueryClient();
  
  return useMutation(() => axios.post('/investment/reset-orders').then(res => res.data), {
    onSuccess: (data) => {
      if (data.success) {
        toast.success('System orders reset successfully!');
        // Invalidate related queries
        queryClient.invalidateQueries('systemOrders');
        queryClient.invalidateQueries('portfolioStatus');
        queryClient.invalidateQueries('investmentStatus');
      } else {
        toast.error(data.error || 'Failed to reset system orders');
      }
    },
    onError: () => {
      toast.error('Failed to reset system orders');
    },
  });
};

export const useFailedOrders = () => {
  return useQuery(
    'failedOrders',
    api.getFailedOrders,
    {
      refetchInterval: 10000, // Refetch every 10 seconds
      staleTime: 5000, // Consider stale after 5 seconds
      retry: 1,
      onError: (error) => {
        console.error('Failed orders fetch failed:', error);
      },
    }
  );
};

export const useOrdersWithRetries = () => {
  return useQuery(
    'ordersWithRetries',
    api.getOrdersWithRetries,
    {
      refetchInterval: 15000, // Refetch every 15 seconds
      staleTime: 10000, // Consider stale after 10 seconds
      retry: 1,
      onError: (error) => {
        console.error('Orders with retries fetch failed:', error);
      },
    }
  );
};

export const useRetryFailedOrdersMutation = () => {
  const queryClient = useQueryClient();
  
  return useMutation(api.retryFailedOrders, {
    onSuccess: (data) => {
      if (data.success) {
        const { successful_retries, failed_retries, retried_count } = data.data;
        
        if (successful_retries > 0 && failed_retries === 0) {
          toast.success(`🎉 All ${successful_retries} orders retried successfully!`);
        } else if (successful_retries > 0 && failed_retries > 0) {
          toast.success(`✅ ${successful_retries} orders succeeded, ❌ ${failed_retries} failed`);
        } else if (failed_retries > 0) {
          toast.error(`❌ All ${failed_retries} retry attempts failed`);
        } else {
          toast.info('No orders to retry');
        }
        
        // Invalidate related queries to refresh the UI
        queryClient.invalidateQueries('failedOrders');
        queryClient.invalidateQueries('systemOrders');
        queryClient.invalidateQueries('portfolioStatus');
      } else {
        toast.error(data.error || 'Failed to retry orders');
      }
    },
    onError: (error) => {
      console.error('Retry orders error:', error);
      toast.error('Failed to retry orders');
    },
  });
};

// Live Orders hooks
export const useLiveOrders = () => {
  return useQuery(
    'liveOrders',
    api.getLiveOrders,
    {
      refetchInterval: 10000, // Refetch every 10 seconds
      staleTime: 5000, // Consider stale after 5 seconds
      retry: 1,
      onError: (error) => {
        console.error('Live orders fetch failed:', error);
      },
    }
  );
};

export const useMonitoringStatus = () => {
  return useQuery(
    'monitoringStatus',
    () => axios.get('/investment/monitoring-status'),
    {
      refetchInterval: 30000, // Refetch every 30 seconds
      staleTime: 10000, // Consider stale after 10 seconds
      retry: 1,
      onError: (error) => {
        console.error('Monitoring status fetch failed:', error);
      },
    }
  );
};

export const useExecuteLiveOrdersMutation = () => {
  const queryClient = useQueryClient();
  
  return useMutation(api.executeLiveOrders, {
    onSuccess: (data) => {
      if (data.success) {
        const { orders_executed, orders_failed, total_orders } = data.data;
        
        if (orders_executed > 0 && orders_failed === 0) {
          toast.success(`🎉 All ${orders_executed} orders placed successfully!`);
        } else if (orders_executed > 0 && orders_failed > 0) {
          toast.success(`✅ ${orders_executed} orders placed, ❌ ${orders_failed} failed`);
        } else if (orders_failed > 0) {
          toast.error(`❌ All ${orders_failed} orders failed to place`);
        } else {
          toast.info('No orders to execute');
        }
        
        // Invalidate related queries to refresh the UI
        queryClient.invalidateQueries('liveOrders');
        queryClient.invalidateQueries('systemOrders');
        queryClient.invalidateQueries('portfolioStatus');
      } else {
        toast.error(data.message || 'Failed to execute live orders');
      }
    },
    onError: (error) => {
      console.error('Execute live orders error:', error);
      toast.error('Failed to execute live orders');
    },
  });
};

export const useStartLiveMonitoringMutation = () => {
  const queryClient = useQueryClient();
  
  return useMutation(api.startLiveMonitoring, {
    onSuccess: (data) => {
      if (data.success) {
        toast.success('📡 Live monitoring started');
        queryClient.invalidateQueries('liveOrders');
      } else {
        toast.error('Failed to start monitoring');
      }
    },
    onError: () => {
      toast.error('Failed to start monitoring');
    },
  });
};

export const useStopLiveMonitoringMutation = () => {
  const queryClient = useQueryClient();
  
  return useMutation(api.stopLiveMonitoring, {
    onSuccess: (data) => {
      if (data.success) {
        toast.success('⏹️ Live monitoring stopped');
        queryClient.invalidateQueries('liveOrders');
      } else {
        toast.error('Failed to stop monitoring');
      }
    },
    onError: () => {
      toast.error('Failed to stop monitoring');
    },
  });
};

export const useUpdateLiveOrderStatusMutation = () => {
  const queryClient = useQueryClient();
  
  return useMutation(api.updateLiveOrderStatus, {
    onSuccess: (data) => {
      if (data.success) {
        toast.success('Order status updated');
        queryClient.invalidateQueries('liveOrders');
      } else {
        toast.error('Failed to update order status');
      }
    },
    onError: () => {
      toast.error('Failed to update order status');
    },
  });
};

export const useSyncLiveOrderStatusMutation = () => {
  const queryClient = useQueryClient();
  
  return useMutation(() => axios.post('/investment/sync-live-order-status'), {
    onSuccess: (data) => {
      if (data?.data?.success) {
        queryClient.invalidateQueries('systemOrders');
        queryClient.invalidateQueries('failedOrders');
        queryClient.invalidateQueries('liveOrders');
      }
    },
    onError: (error) => {
      console.error('Failed to sync live order status:', error);
    },
  });
};

export default api;