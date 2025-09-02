import React, { useState } from 'react';
import {
  Box,
  Container,
  Typography,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Button,
  Alert,
  Collapse,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  TrendingUp as BuyIcon,
  TrendingDown as SellIcon,
  Replay as RetryIcon,
  ExpandMore as ExpandIcon,
  ExpandLess as CollapseIcon,
  CheckCircle as CompleteIcon,
  Cancel as FailedIcon,
  Pending as PendingIcon,
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import toast from 'react-hot-toast';

// Hooks
import { 
  useUserOrdersWithRetries as useOrders,
  useUserRetryFailedOrdersMutation as useRetryOrderMutation,
  useUpdateOrderStatusFromZerodhaMutation as useUpdateStatusMutation,
} from '../../hooks/useUserApi';

const Orders = () => {
  const [expandedOrders, setExpandedOrders] = useState(new Set());
  
  const { data: ordersData, isLoading, refetch } = useOrders();
  const retryOrderMutation = useRetryOrderMutation();
  const updateStatusMutation = useUpdateStatusMutation();

  const orders = ordersData?.data?.orders_with_retry_history || [];

  // Toggle order expansion to show sub-orders (retries)
  const toggleOrder = (orderId) => {
    const newExpanded = new Set(expandedOrders);
    if (newExpanded.has(orderId)) {
      newExpanded.delete(orderId);
    } else {
      newExpanded.add(orderId);
    }
    setExpandedOrders(newExpanded);
  };

  // Retry a specific failed order
  const handleRetryOrder = (orderId) => {
    retryOrderMutation.mutate([orderId], {
      onSuccess: (data) => {
        if (data.success) {
          toast.success(`Order ${orderId} retry initiated`);
          refetch(); // Refresh orders to show the new retry
        } else {
          toast.error(data.message || 'Retry failed');
        }
      },
      onError: () => {
        toast.error('Failed to retry order');
      }
    });
  };

  // Update order status from Zerodha
  const handleUpdateStatus = (zerodhaOrderId = null) => {
    updateStatusMutation.mutate(zerodhaOrderId, {
      onSuccess: () => {
        toast.success('Order statuses updated');
        refetch();
      },
      onError: () => {
        toast.error('Failed to update status');
      }
    });
  };

  // Get status chip color and icon
  const getStatusChip = (status) => {
    const statusUpper = status?.toUpperCase();
    
    switch (statusUpper) {
      case 'COMPLETE':
        return { color: 'success', icon: <CompleteIcon />, label: 'Complete' };
      case 'REJECTED':
      case 'CANCELLED':
      case 'FAILED':
        return { color: 'error', icon: <FailedIcon />, label: statusUpper };
      case 'OPEN':
      case 'TRIGGER PENDING':
      case 'PENDING':
        return { color: 'warning', icon: <PendingIcon />, label: statusUpper };
      default:
        return { color: 'default', icon: <PendingIcon />, label: status || 'Unknown' };
    }
  };

  const getStatusMessage = (orderData) => {
    const order = orderData.main_order;
    const status = orderData.latest_status?.toUpperCase();
    const sessionType = order.session_type;
    
    switch (status) {
      case 'PENDING':
        if (sessionType === 'REBALANCING') {
          if (order.action === 'SELL') {
            return `Waiting to sell ${order.shares} shares (stock removed from CSV)`;
          } else if (order.action === 'BUY') {
            return `Waiting to buy ${order.shares} shares (new stock in CSV)`;
          }
        } else if (sessionType === 'INITIAL_INVESTMENT') {
          return `Waiting to ${order.action.toLowerCase()} ${order.shares} shares`;
        }
        return 'Order waiting to be placed on Zerodha';
      case 'OPEN':
        return 'Order placed on Zerodha, waiting for market execution';
      case 'TRIGGER PENDING':
        return 'Order placed with trigger condition, waiting for trigger';
      case 'COMPLETE':
      case 'EXECUTED':
        return `Successfully ${order.action.toLowerCase() === 'buy' ? 'bought' : 'sold'} ${order.shares} shares`;
      case 'REJECTED':
        return 'Order rejected by Zerodha - check funds/limits';
      case 'CANCELLED':
        return 'Order was cancelled';
      case 'FAILED':
        return 'Order failed to execute - may retry automatically';
      case 'FAILED_MAX_RETRIES':
        return 'Order failed after maximum retry attempts';
      default:
        return status ? `Order status: ${status}` : 'Status unknown';
    }
  };

  if (isLoading) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Typography>Loading orders...</Typography>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        {/* Header */}
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Typography variant="h4" fontWeight="bold" color="white">
            Orders
          </Typography>
          <Box display="flex" gap={2}>
            <Button
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={() => refetch()}
              disabled={isLoading}
            >
              Refresh
            </Button>
            <Button
              variant="contained"
              startIcon={<RefreshIcon />}
              onClick={() => handleUpdateStatus()}
              disabled={updateStatusMutation.isLoading}
              sx={{
                background: 'linear-gradient(135deg, #10B981 0%, #059669 100%)',
                '&:hover': {
                  background: 'linear-gradient(135deg, #059669 0%, #047857 100%)',
                }
              }}
            >
              {updateStatusMutation.isLoading ? 'Syncing...' : 'Sync from Zerodha'}
            </Button>
          </Box>
        </Box>

        {/* Orders Summary */}
        <Card sx={{ mb: 3, backgroundColor: 'rgba(255, 255, 255, 0.05)' }}>
          <CardContent>
            <Typography variant="h6" color="white" gutterBottom>
              Orders Summary
            </Typography>
            <Box display="flex" gap={4}>
              <Typography color="rgba(255, 255, 255, 0.7)">
                Total Orders: <strong style={{ color: 'white' }}>{orders.length}</strong>
              </Typography>
              <Typography color="rgba(255, 255, 255, 0.7)">
                Failed Orders: <strong style={{ color: '#ef4444' }}>
                  {orders.filter(order => {
                    const latestStatus = order.latest_status;
                    return ['REJECTED', 'CANCELLED', 'FAILED', 'FAILED_MAX_RETRIES'].includes(latestStatus?.toUpperCase());
                  }).length}
                </strong>
              </Typography>
            </Box>
          </CardContent>
        </Card>

        {/* Orders Table */}
        <Card sx={{ backgroundColor: 'rgba(255, 255, 255, 0.05)' }}>
          <CardContent>
            {orders.length === 0 ? (
              <Alert severity="info" sx={{ backgroundColor: 'rgba(33, 150, 243, 0.1)' }}>
                No orders found. Place your first investment to see orders here.
              </Alert>
            ) : (
              <TableContainer component={Paper} sx={{ backgroundColor: 'transparent' }}>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>Symbol</TableCell>
                      <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>Type</TableCell>
                      <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>Quantity</TableCell>
                      <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>Price</TableCell>
                      <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>Status</TableCell>
                      <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>Zerodha ID</TableCell>
                      <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>Actions</TableCell>
                      <TableCell sx={{ color: 'white', fontWeight: 'bold' }}></TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {orders.map((orderData) => {
                      const order = orderData.main_order;
                      const hasRetries = orderData.has_retries && orderData.retry_history.length > 0;
                      const latestRetry = hasRetries ? orderData.retry_history[orderData.retry_history.length - 1] : null;
                      const isExpanded = expandedOrders.has(order.order_id);
                      const isFailed = ['REJECTED', 'CANCELLED', 'FAILED', 'FAILED_MAX_RETRIES'].includes(orderData.latest_status?.toUpperCase());
                      const statusChip = getStatusChip(orderData.latest_status);

                      // Get the latest zerodha order ID (from retries or main order)
                      const latestZerodhaId = latestRetry?.zerodha_order_id || 'Not Sent';

                      return (
                        <React.Fragment key={order.order_id}>
                          {/* Main Order Row */}
                          <TableRow sx={{ backgroundColor: hasRetries ? 'rgba(255, 255, 255, 0.02)' : 'transparent' }}>
                            <TableCell sx={{ color: 'white' }}>
                              <Box display="flex" alignItems="center" gap={1}>
                                {order.action === 'BUY' ? (
                                  <BuyIcon sx={{ color: '#10B981', fontSize: 20 }} />
                                ) : (
                                  <SellIcon sx={{ color: '#ef4444', fontSize: 20 }} />
                                )}
                                {order.symbol}
                              </Box>
                            </TableCell>
                            <TableCell sx={{ color: 'white' }}>{order.action}</TableCell>
                            <TableCell sx={{ color: 'white' }}>{order.shares}</TableCell>
                            <TableCell sx={{ color: 'white' }}>₹{order.price?.toFixed(2) || 'N/A'}</TableCell>
                            <TableCell>
                              <Box>
                                <Chip
                                  icon={statusChip.icon}
                                  label={statusChip.label}
                                  color={statusChip.color}
                                  size="small"
                                />
                                <Typography 
                                  variant="caption" 
                                  sx={{ 
                                    color: 'rgba(255, 255, 255, 0.7)', 
                                    display: 'block', 
                                    mt: 0.5,
                                    fontSize: '0.75rem',
                                    lineHeight: 1.2
                                  }}
                                >
                                  {getStatusMessage(orderData)}
                                </Typography>
                              </Box>
                            </TableCell>
                            <TableCell sx={{ color: 'rgba(255, 255, 255, 0.7)' }}>
                              {latestZerodhaId}
                            </TableCell>
                            <TableCell>
                              {isFailed && (
                                <Button
                                  size="small"
                                  variant="outlined"
                                  color="warning"
                                  startIcon={<RetryIcon />}
                                  onClick={() => handleRetryOrder(order.order_id)}
                                  disabled={retryOrderMutation.isLoading}
                                >
                                  Retry
                                </Button>
                              )}
                            </TableCell>
                            <TableCell>
                              {hasRetries && (
                                <IconButton
                                  size="small"
                                  onClick={() => toggleOrder(order.order_id)}
                                  sx={{ color: 'white' }}
                                >
                                  {isExpanded ? <CollapseIcon /> : <ExpandIcon />}
                                </IconButton>
                              )}
                              {hasRetries && (
                                <Typography variant="caption" sx={{ color: 'rgba(255, 255, 255, 0.7)', ml: 1 }}>
                                  {orderData.retry_history.length} retries
                                </Typography>
                              )}
                            </TableCell>
                          </TableRow>

                          {/* Sub-orders (Retries) */}
                          {hasRetries && (
                            <TableRow>
                              <TableCell colSpan={8} sx={{ p: 0, border: 0 }}>
                                <Collapse in={isExpanded}>
                                  <Box sx={{ p: 2, backgroundColor: 'rgba(255, 255, 255, 0.02)' }}>
                                    <Typography variant="subtitle2" sx={{ color: 'white', mb: 2 }}>
                                      Retry History:
                                    </Typography>
                                    {orderData.retry_history.map((retry, index) => {
                                      const retryStatusChip = getStatusChip(retry.status);
                                      return (
                                        <Box 
                                          key={`${order.order_id}-retry-${index}`}
                                          display="flex" 
                                          alignItems="center" 
                                          gap={2} 
                                          sx={{ 
                                            p: 1, 
                                            mb: 1, 
                                            backgroundColor: 'rgba(255, 255, 255, 0.03)',
                                            borderRadius: 1,
                                            border: index === orderData.retry_history.length - 1 ? '1px solid #10B981' : 'none'
                                          }}
                                        >
                                          <Typography variant="body2" sx={{ color: 'rgba(255, 255, 255, 0.7)' }}>
                                            Retry #{retry.retry_number}
                                          </Typography>
                                          <Chip
                                            icon={retryStatusChip.icon}
                                            label={retryStatusChip.label}
                                            color={retryStatusChip.color}
                                            size="small"
                                          />
                                          <Typography variant="body2" sx={{ color: 'rgba(255, 255, 255, 0.7)' }}>
                                            Zerodha ID: {retry.zerodha_order_id || 'Not Sent'}
                                          </Typography>
                                          <Typography variant="body2" sx={{ color: 'rgba(255, 255, 255, 0.7)' }}>
                                            Time: {new Date(retry.retry_time).toLocaleString()}
                                          </Typography>
                                          {retry.failure_reason && (
                                            <Typography variant="body2" sx={{ color: '#ef4444' }}>
                                              Reason: {retry.failure_reason}
                                            </Typography>
                                          )}
                                          {index === orderData.retry_history.length - 1 && (
                                            <Chip label="Latest" size="small" color="primary" />
                                          )}
                                        </Box>
                                      );
                                    })}
                                  </Box>
                                </Collapse>
                              </TableCell>
                            </TableRow>
                          )}
                        </React.Fragment>
                      );
                    })}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </CardContent>
        </Card>
      </motion.div>
    </Container>
  );
};

export default Orders;