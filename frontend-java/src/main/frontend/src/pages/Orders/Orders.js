import React, { useState, useEffect } from 'react';
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
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TablePagination,
  Tooltip,
  Avatar,
} from '@mui/material';
import {
  Timeline as TimelineIcon,
  Refresh as RefreshIcon,
  DeleteSweep as DeleteSweepIcon,
  TrendingUp as BuyIcon,
  TrendingDown as SellIcon,
  Info as InfoIcon,
  Replay as RetryIcon,
  Error as FailedIcon,
  CheckCircle as SuccessIcon,
  PlayArrow as StartIcon,
  Sync as SyncIcon,
  Stop as StopIcon,
  Visibility as ViewIcon,
  Cancel as CancelIcon,
  Pending as PendingIcon,
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import toast from 'react-hot-toast';

// Components
import LoadingScreen from '../../components/UI/LoadingScreen';

// Hooks
import { 
  useSystemOrders, 
  useResetSystemOrdersMutation, 
  useFailedOrders, 
  useRetryFailedOrdersMutation,
  useLiveOrders,
  useUpdateLiveOrderStatusMutation,
  useMonitoringStatus
} from '../../hooks/useApi';

const Orders = () => {
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);
  const [resetDialogOpen, setResetDialogOpen] = useState(false);

  const { data: systemOrders, isLoading: ordersLoading, refetch: refetchOrders } = useSystemOrders();
  const { data: failedOrdersData, isLoading: failedOrdersLoading, refetch: refetchFailedOrders } = useFailedOrders();
  const { data: liveOrdersData, isLoading: liveOrdersLoading, refetch: refetchLiveOrders } = useLiveOrders();
  const { data: monitoringStatus } = useMonitoringStatus();
  const resetOrdersMutation = useResetSystemOrdersMutation();
  const retryOrdersMutation = useRetryFailedOrdersMutation();
  const updateOrderStatusMutation = useUpdateLiveOrderStatusMutation();

  const orders = systemOrders?.data?.orders || [];
  const failedOrders = failedOrdersData?.data?.failed_orders || [];
  const canRetryAll = failedOrdersData?.data?.can_retry_all || false;
  const liveOrders = liveOrdersData?.data?.orders || [];
  const orderSummary = liveOrdersData?.data?.summary || {};
  const monitoringActive = monitoringStatus?.data?.monitoring_active || false;
  const pendingOrdersCount = monitoringStatus?.data?.pending_orders_count || 0;
  const monitoringStatusMessage = monitoringStatus?.data?.status_message || 'Checking monitoring status...';



  const handleUpdateOrderStatus = (orderId) => {
    updateOrderStatusMutation.mutate(orderId, {
      onSuccess: () => {
        refetchLiveOrders();
      }
    });
  };

  // Combine system orders with live order details
  const getCombinedOrders = () => {
    return orders.map(systemOrder => {
      // Find matching live order by zerodha_order_id or system order details
      const matchingLiveOrder = liveOrders.find(liveOrder => 
        liveOrder.zerodha_order_id === systemOrder.zerodha_order_id ||
        (liveOrder.system_order_id === systemOrder.order_id) ||
        (liveOrder.symbol === systemOrder.symbol && 
         liveOrder.action === systemOrder.action && 
         liveOrder.shares === systemOrder.shares)
      );

      // Determine the display status based on live order status if available
      let displayStatus = systemOrder.status;
      let statusMessage = systemOrder.failure_reason;
      
      if (matchingLiveOrder) {
        // Use live order status if available
        if (matchingLiveOrder.status === 'COMPLETE') {
          displayStatus = 'COMPLETE';
        } else if (matchingLiveOrder.status === 'REJECTED') {
          displayStatus = 'FAILED';
          statusMessage = matchingLiveOrder.execution_details?.status_message || matchingLiveOrder.error || 'Order rejected by Zerodha';
        } else if (matchingLiveOrder.status === 'CANCELLED') {
          displayStatus = 'FAILED';
          statusMessage = 'Order cancelled';
        } else if (matchingLiveOrder.status === 'FAILED_TO_PLACE') {
          displayStatus = 'FAILED';
          statusMessage = matchingLiveOrder.error || 'Failed to place order';
        } else if (matchingLiveOrder.status === 'OPEN') {
          displayStatus = 'OPEN';
          statusMessage = 'Order placed and waiting for execution';
        } else {
          displayStatus = matchingLiveOrder.status;
        }
      }

      // Check if this order can be retried (from failed orders data)
      const failedOrder = failedOrders.find(fo => fo.order_id === systemOrder.order_id);
      const canRetry = failedOrder?.can_retry || (displayStatus === 'FAILED' && !systemOrder.status?.includes('MAX_RETRIES'));

      return {
        ...systemOrder,
        liveOrderDetails: matchingLiveOrder,
        displayStatus: displayStatus,
        zerodhaOrderId: matchingLiveOrder?.zerodha_order_id || systemOrder.zerodha_order_id,
        executionDetails: matchingLiveOrder?.execution_details,
        liveStatus: matchingLiveOrder?.status,
        filledQuantity: matchingLiveOrder?.execution_details?.filled_quantity || 0,
        averagePrice: matchingLiveOrder?.execution_details?.average_price || systemOrder.price,
        statusMessage: statusMessage,
        can_retry: canRetry
      };
    });
  };

  const handleRetryOrder = (orderId) => {
    retryOrdersMutation.mutate([orderId], {
      onSuccess: () => {
        refetchOrders();
        refetchFailedOrders();
      }
    });
  };

  const handleRetryAllOrders = () => {
    retryOrdersMutation.mutate(null, { // null means retry all
      onSuccess: () => {
        refetchOrders();
        refetchFailedOrders();
      }
    });
  };

  const handleResetOrders = () => {
    resetOrdersMutation.mutate(undefined, {
      onSuccess: () => {
        setResetDialogOpen(false);
        refetchOrders();
      }
    });
  };


  const formatDate = (dateString) => {
    try {
      if (!dateString) return 'Invalid Date';
      const date = new Date(dateString);
      if (isNaN(date.getTime())) return 'Invalid Date';
      return date.toLocaleString('en-IN', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
      });
    } catch (error) {
      return 'Invalid Date';
    }
  };

  const getActionColor = (action) => {
    return action?.toLowerCase() === 'buy' ? '#10B981' : '#EF4444';
  };

  const getActionIcon = (action) => {
    return action?.toLowerCase() === 'buy' ? <BuyIcon /> : <SellIcon />;
  };

  // Loading state
  if (ordersLoading) {
    return <LoadingScreen message="Loading orders..." />;
  }

  // Pagination
  const combinedOrders = getCombinedOrders();
  const paginatedOrders = combinedOrders.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage);

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
              <TimelineIcon sx={{ fontSize: 28 }} />
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
                Order Management
              </Typography>
              <Typography variant="h6" sx={{ color: 'rgba(255, 255, 255, 0.8)' }}>
                Live order execution and real-time monitoring on Zerodha
              </Typography>
            </Box>
          </Box>
          
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
            {/* Monitoring Status Indicator */}
            <Box sx={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: 1, 
              px: 2, 
              py: 1, 
              borderRadius: 2,
              background: monitoringActive 
                ? 'linear-gradient(135deg, #10B981 0%, #059669 100%)'
                : 'rgba(255, 255, 255, 0.1)',
              border: '1px solid rgba(255, 255, 255, 0.1)'
            }}>
              <Box sx={{
                width: 8,
                height: 8,
                borderRadius: '50%',
                backgroundColor: monitoringActive ? '#fff' : '#9CA3AF',
                animation: monitoringActive ? 'pulse 2s infinite' : 'none',
                '@keyframes pulse': {
                  '0%, 100%': { opacity: 1 },
                  '50%': { opacity: 0.5 }
                }
              }} />
              <Typography variant="body2" sx={{ 
                color: monitoringActive ? '#fff' : 'rgba(255, 255, 255, 0.8)',
                fontWeight: 500 
              }}>
                {monitoringActive 
                  ? `Monitoring ${pendingOrdersCount} orders`
                  : 'Auto-monitoring ready'
                }
              </Typography>
            </Box>
            
            {failedOrders.length > 0 && canRetryAll && (
              <Tooltip title="Retry All Failed Orders">
                <Button
                  variant="contained"
                  startIcon={<RetryIcon />}
                  onClick={handleRetryAllOrders}
                  disabled={retryOrdersMutation.isLoading}
                  sx={{
                    background: 'linear-gradient(135deg, #FF9500 0%, #FF6B00 100%)',
                    color: 'white',
                    '&:hover': {
                      background: 'linear-gradient(135deg, #FF6B00 0%, #FF4500 100%)',
                    },
                  }}
                >
                  {retryOrdersMutation.isLoading ? 'Retrying...' : `Retry All (${failedOrders.length})`}
                </Button>
              </Tooltip>
            )}
            <Tooltip title="Reset All Orders (Testing)">
              <Button
                variant="outlined"
                startIcon={<DeleteSweepIcon />}
                onClick={() => setResetDialogOpen(true)}
                sx={{
                  borderColor: '#EF4444',
                  color: '#EF4444',
                  '&:hover': {
                    borderColor: '#EF4444',
                    background: 'rgba(239, 68, 68, 0.1)',
                  },
                }}
              >
                Reset Orders
              </Button>
            </Tooltip>
          </Box>
        </Box>

        {/* Summary Cards */}
        <Box sx={{ display: 'flex', gap: 2, mb: 4 }}>
          <Card
            sx={{
              flex: 1,
              background: 'linear-gradient(135deg, #007AFF 0%, #5856D6 100%)',
              color: 'white',
            }}
          >
            <CardContent sx={{ py: 2 }}>
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Total Orders
              </Typography>
              <Typography variant="h4" sx={{ fontWeight: 700 }}>
                {orders.length}
              </Typography>
            </CardContent>
          </Card>

          <Card
            sx={{
              flex: 1,
              background: 'linear-gradient(135deg, #10B981 0%, #059669 100%)',
              color: 'white',
            }}
          >
            <CardContent sx={{ py: 2 }}>
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Executed Orders
              </Typography>
              <Typography variant="h4" sx={{ fontWeight: 700 }}>
                {getCombinedOrders().filter(order => order.displayStatus === 'COMPLETE' || order.displayStatus === 'OPEN').length}
              </Typography>
            </CardContent>
          </Card>

          <Card
            sx={{
              flex: 1,
              background: 'linear-gradient(135deg, #EF4444 0%, #DC2626 100%)',
              color: 'white',
            }}
          >
            <CardContent sx={{ py: 2 }}>
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Failed Orders
              </Typography>
              <Typography variant="h4" sx={{ fontWeight: 700 }}>
                {getCombinedOrders().filter(order => order.displayStatus === 'FAILED' || order.status === 'FAILED_MAX_RETRIES').length}
              </Typography>
            </CardContent>
          </Card>
        </Box>

        {/* Orders Table */}
        <Card
          sx={{
            background: 'rgba(28, 28, 30, 0.8)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
          }}
        >
          <CardContent sx={{ p: 0 }}>
            {orders.length > 0 ? (
              <>
                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow sx={{ '& .MuiTableCell-head': { borderBottom: '1px solid rgba(255, 255, 255, 0.1)' } }}>
                        <TableCell sx={{ color: 'rgba(255, 255, 255, 0.9)', fontWeight: 600 }}>
                          Action
                        </TableCell>
                        <TableCell sx={{ color: 'rgba(255, 255, 255, 0.9)', fontWeight: 600 }}>
                          Symbol
                        </TableCell>
                        <TableCell sx={{ color: 'rgba(255, 255, 255, 0.9)', fontWeight: 600 }} align="right">
                          Quantity
                        </TableCell>
                        <TableCell sx={{ color: 'rgba(255, 255, 255, 0.9)', fontWeight: 600 }} align="right">
                          Target Price
                        </TableCell>
                        <TableCell sx={{ color: 'rgba(255, 255, 255, 0.9)', fontWeight: 600 }} align="right">
                          Executed Price
                        </TableCell>
                        <TableCell sx={{ color: 'rgba(255, 255, 255, 0.9)', fontWeight: 600 }} align="right">
                          Filled/Total
                        </TableCell>
                        <TableCell sx={{ color: 'rgba(255, 255, 255, 0.9)', fontWeight: 600 }}>
                          Status
                        </TableCell>
                        <TableCell sx={{ color: 'rgba(255, 255, 255, 0.9)', fontWeight: 600 }}>
                          Zerodha Order ID
                        </TableCell>
                        <TableCell sx={{ color: 'rgba(255, 255, 255, 0.9)', fontWeight: 600 }}>
                          Actions
                        </TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {paginatedOrders.map((order, index) => (
                        <TableRow
                          key={index}
                          sx={{
                            '& .MuiTableCell-body': {
                              borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
                              color: 'rgba(255, 255, 255, 0.9)',
                            },
                            '&:hover': {
                              background: 'rgba(255, 255, 255, 0.02)',
                            },
                          }}
                        >
                          <TableCell>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <Avatar
                                sx={{
                                  width: 32,
                                  height: 32,
                                  background: getActionColor(order.action),
                                }}
                              >
                                {getActionIcon(order.action)}
                              </Avatar>
                              <Chip
                                label={order.action?.toUpperCase() || 'N/A'}
                                size="small"
                                sx={{
                                  background: `${getActionColor(order.action)}20`,
                                  color: getActionColor(order.action),
                                  border: `1px solid ${getActionColor(order.action)}40`,
                                  fontWeight: 600,
                                }}
                              />
                            </Box>
                          </TableCell>
                          <TableCell>
                            <Typography variant="body1" sx={{ fontWeight: 600 }}>
                              {order.symbol || 'N/A'}
                            </Typography>
                          </TableCell>
                          <TableCell align="right">
                            <Typography variant="body1" sx={{ fontWeight: 500 }}>
                              {(order.shares || order.quantity || 0).toLocaleString()}
                            </Typography>
                          </TableCell>
                          <TableCell align="right">
                            <Typography variant="body1" sx={{ fontWeight: 500 }}>
                              ₹{(order.price || 0).toFixed(2)}
                            </Typography>
                          </TableCell>
                          <TableCell align="right">
                            <Typography variant="body1" sx={{ fontWeight: 500, color: order.averagePrice !== order.price ? '#10B981' : 'inherit' }}>
                              {order.averagePrice ? `₹${order.averagePrice.toFixed(2)}` : 'Pending'}
                            </Typography>
                          </TableCell>
                          <TableCell align="right">
                            <Typography variant="body1" sx={{ fontWeight: 500 }}>
                              {order.filledQuantity || 0}/{order.shares || order.quantity || 0}
                            </Typography>
                            {order.filledQuantity > 0 && order.filledQuantity < (order.shares || order.quantity) && (
                              <Typography variant="caption" sx={{ color: '#F59E0B', display: 'block' }}>
                                Partial Fill
                              </Typography>
                            )}
                          </TableCell>
                          <TableCell>
                            {order.displayStatus === 'FAILED' ? (
                              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                                <Chip
                                  icon={<FailedIcon />}
                                  label="FAILED"
                                  size="small"
                                  sx={{
                                    background: 'rgba(239, 68, 68, 0.2)',
                                    color: '#EF4444',
                                    border: '1px solid rgba(239, 68, 68, 0.4)',
                                  }}
                                />
                                {order.statusMessage && (
                                  <Typography variant="caption" sx={{ color: 'rgba(255, 255, 255, 0.6)', fontSize: '0.7rem' }}>
                                    {order.statusMessage}
                                  </Typography>
                                )}
                              </Box>
                            ) : order.status === 'FAILED_MAX_RETRIES' ? (
                              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                                <Chip
                                  icon={<FailedIcon />}
                                  label="MAX RETRIES"
                                  size="small"
                                  sx={{
                                    background: 'rgba(156, 163, 175, 0.2)',
                                    color: '#9CA3AF',
                                    border: '1px solid rgba(156, 163, 175, 0.4)',
                                  }}
                                />
                                {order.statusMessage && (
                                  <Typography variant="caption" sx={{ color: 'rgba(255, 255, 255, 0.6)', fontSize: '0.7rem' }}>
                                    {order.statusMessage}
                                  </Typography>
                                )}
                              </Box>
                            ) : order.displayStatus === 'COMPLETE' ? (
                              <Chip
                                icon={<SuccessIcon />}
                                label="COMPLETE"
                                size="small"
                                sx={{
                                  background: 'rgba(16, 185, 129, 0.2)',
                                  color: '#10B981',
                                  border: '1px solid rgba(16, 185, 129, 0.4)',
                                }}
                              />
                            ) : order.displayStatus === 'OPEN' ? (
                              <Chip
                                icon={<PendingIcon />}
                                label="OPEN"
                                size="small"
                                sx={{
                                  background: 'rgba(245, 158, 11, 0.2)',
                                  color: '#F59E0B',
                                  border: '1px solid rgba(245, 158, 11, 0.4)',
                                }}
                              />
                            ) : order.displayStatus === 'LIVE_PLACED' ? (
                              <Chip
                                icon={<PendingIcon />}
                                label="PLACED"
                                size="small"
                                sx={{
                                  background: 'rgba(59, 130, 246, 0.2)',
                                  color: '#3B82F6',
                                  border: '1px solid rgba(59, 130, 246, 0.4)',
                                }}
                              />
                            ) : (
                              <Chip
                                icon={<SuccessIcon />}
                                label={order.displayStatus || 'EXECUTED'}
                                size="small"
                                sx={{
                                  background: 'rgba(16, 185, 129, 0.2)',
                                  color: '#10B981',
                                  border: '1px solid rgba(16, 185, 129, 0.4)',
                                }}
                              />
                            )}
                            {order.statusMessage && (
                              <Typography variant="caption" sx={{ color: 'rgba(255, 255, 255, 0.6)', fontSize: '0.7rem', display: 'block', mt: 0.5 }}>
                                {order.statusMessage}
                              </Typography>
                            )}
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2" sx={{ fontFamily: 'monospace', color: 'rgba(255, 255, 255, 0.8)' }}>
                              {order.zerodhaOrderId || 'N/A'}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Box sx={{ display: 'flex', gap: 1 }}>
                              {order.displayStatus === 'FAILED' && order.can_retry && (
                                <Tooltip title={`Retry order for ${order.symbol}`}>
                                  <IconButton
                                    size="small"
                                    onClick={() => handleRetryOrder(order.order_id)}
                                    disabled={retryOrdersMutation.isLoading}
                                    sx={{
                                      background: 'rgba(255, 149, 0, 0.2)',
                                      color: '#FF9500',
                                      border: '1px solid rgba(255, 149, 0, 0.4)',
                                      '&:hover': {
                                        background: 'rgba(255, 149, 0, 0.3)',
                                      },
                                    }}
                                  >
                                    <RetryIcon fontSize="small" />
                                  </IconButton>
                                </Tooltip>
                              )}
                              {order.zerodhaOrderId && (
                                <Tooltip title="Update order status">
                                  <IconButton
                                    size="small"
                                    onClick={() => handleUpdateOrderStatus(order.zerodhaOrderId)}
                                    disabled={updateOrderStatusMutation.isLoading}
                                    sx={{
                                      background: 'rgba(59, 130, 246, 0.2)',
                                      color: '#3B82F6',
                                      border: '1px solid rgba(59, 130, 246, 0.4)',
                                      '&:hover': {
                                        background: 'rgba(59, 130, 246, 0.3)',
                                      },
                                    }}
                                  >
                                    <RefreshIcon fontSize="small" />
                                  </IconButton>
                                </Tooltip>
                              )}
                              {!order.status || order.status === 'FAILED_MAX_RETRIES' ? (
                                <Typography variant="caption" sx={{ color: 'rgba(255, 255, 255, 0.5)', alignSelf: 'center' }}>
                                  {order.status === 'FAILED_MAX_RETRIES' ? 'Max retries' : '-'}
                                </Typography>
                              ) : null}
                            </Box>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>

                <TablePagination
                  component="div"
                  count={combinedOrders.length}
                  page={page}
                  onPageChange={(event, newPage) => setPage(newPage)}
                  rowsPerPage={rowsPerPage}
                  onRowsPerPageChange={(event) => {
                    setRowsPerPage(parseInt(event.target.value, 10));
                    setPage(0);
                  }}
                  sx={{
                    color: 'rgba(255, 255, 255, 0.7)',
                    borderTop: '1px solid rgba(255, 255, 255, 0.1)',
                    '& .MuiSelect-icon': {
                      color: 'rgba(255, 255, 255, 0.7)',
                    },
                  }}
                />
              </>
            ) : (
              <Box sx={{ p: 4, textAlign: 'center' }}>
                <TimelineIcon sx={{ fontSize: 64, color: 'rgba(255, 255, 255, 0.3)', mb: 2 }} />
                <Typography variant="h6" sx={{ mb: 1 }}>
                  No Orders Found
                </Typography>
                <Typography variant="body2" sx={{ color: 'rgba(255, 255, 255, 0.6)' }}>
                  Orders will appear here after you execute investments or rebalancing operations.
                </Typography>
              </Box>
            )}
          </CardContent>
        </Card>
      </motion.div>

      {/* Reset Confirmation Dialog */}
      <Dialog
        open={resetDialogOpen}
        onClose={() => setResetDialogOpen(false)}
        PaperProps={{
          sx: {
            background: 'rgba(28, 28, 30, 0.95)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            color: 'white',
          },
        }}
      >
        <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <DeleteSweepIcon sx={{ color: '#EF4444' }} />
          Reset All Orders
        </DialogTitle>
        <DialogContent>
          <Alert severity="warning" sx={{ mb: 2 }}>
            This action will permanently delete all order records. This is intended for testing purposes only.
          </Alert>
          <Typography>
            Are you sure you want to reset all orders? This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setResetDialogOpen(false)}>
            Cancel
          </Button>
          <Button
            variant="contained"
            onClick={handleResetOrders}
            disabled={resetOrdersMutation.isLoading}
            sx={{
              background: 'linear-gradient(135deg, #EF4444 0%, #DC2626 100%)',
            }}
          >
            {resetOrdersMutation.isLoading ? 'Resetting...' : 'Reset Orders'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default Orders;