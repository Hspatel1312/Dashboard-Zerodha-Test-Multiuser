import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  Chip,
  Alert,
  Grid,
  Avatar,
  IconButton,
  Tooltip,
  LinearProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Paper,
} from '@mui/material';
import {
  TrendingUp as OrderIcon,
  Refresh as RefreshIcon,
  PlayArrow as StartIcon,
  Stop as StopIcon,
  Visibility as ViewIcon,
  CheckCircle as CompleteIcon,
  Cancel as CancelIcon,
  Pending as PendingIcon,
  Error as ErrorIcon,
  AttachMoney as MoneyIcon,
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import toast from 'react-hot-toast';

const LiveOrderTracker = () => {
  const [liveOrders, setLiveOrders] = useState([]);
  const [orderSummary, setOrderSummary] = useState({});
  const [monitoringActive, setMonitoringActive] = useState(false);
  const [loading, setLoading] = useState(false);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);

  useEffect(() => {
    fetchLiveOrders();
    
    // Auto-refresh every 10 seconds if monitoring is active
    const interval = setInterval(() => {
      if (autoRefresh && monitoringActive) {
        fetchLiveOrders();
      }
    }, 10000);

    return () => clearInterval(interval);
  }, [autoRefresh, monitoringActive]);

  const fetchLiveOrders = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/investment/live-orders');
      const data = await response.json();
      
      if (data.success) {
        setLiveOrders(data.data.orders);
        setOrderSummary(data.data.summary);
        setMonitoringActive(data.data.monitoring_active);
      } else {
        toast.error('Failed to fetch live orders');
      }
    } catch (error) {
      console.error('Error fetching live orders:', error);
      toast.error('Error fetching live orders');
    } finally {
      setLoading(false);
    }
  };

  const startMonitoring = async () => {
    try {
      const response = await fetch('/api/investment/live-orders/start-monitoring', {
        method: 'POST'
      });
      const data = await response.json();
      
      if (data.success) {
        setMonitoringActive(true);
        toast.success('Live order monitoring started');
        fetchLiveOrders();
      } else {
        toast.error('Failed to start monitoring');
      }
    } catch (error) {
      console.error('Error starting monitoring:', error);
      toast.error('Error starting monitoring');
    }
  };

  const stopMonitoring = async () => {
    try {
      const response = await fetch('/api/investment/live-orders/stop-monitoring', {
        method: 'POST'
      });
      const data = await response.json();
      
      if (data.success) {
        setMonitoringActive(false);
        toast.success('Live order monitoring stopped');
      } else {
        toast.error('Failed to stop monitoring');
      }
    } catch (error) {
      console.error('Error stopping monitoring:', error);
      toast.error('Error stopping monitoring');
    }
  };

  const updateOrderStatus = async (orderId) => {
    try {
      const response = await fetch(`/api/investment/live-orders/${orderId}/update`, {
        method: 'POST'
      });
      const data = await response.json();
      
      if (data.success) {
        toast.success('Order status updated');
        fetchLiveOrders();
      } else {
        toast.error('Failed to update order status');
      }
    } catch (error) {
      console.error('Error updating order status:', error);
      toast.error('Error updating order status');
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'COMPLETE':
        return <CompleteIcon sx={{ color: '#10B981' }} />;
      case 'CANCELLED':
      case 'REJECTED':
        return <CancelIcon sx={{ color: '#EF4444' }} />;
      case 'FAILED_TO_PLACE':
        return <ErrorIcon sx={{ color: '#EF4444' }} />;
      case 'OPEN':
      case 'TRIGGER PENDING':
      case 'PLACED':
        return <PendingIcon sx={{ color: '#F59E0B' }} />;
      default:
        return <PendingIcon sx={{ color: '#6B7280' }} />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'COMPLETE':
        return '#10B981';
      case 'CANCELLED':
      case 'REJECTED':
      case 'FAILED_TO_PLACE':
        return '#EF4444';
      case 'OPEN':
      case 'TRIGGER PENDING':
      case 'PLACED':
        return '#F59E0B';
      default:
        return '#6B7280';
    }
  };

  const formatCurrency = (amount) => {
    if (!amount) return 'N/A';
    return `₹${amount.toFixed(2)}`;
  };

  const formatDateTime = (dateString) => {
    if (!dateString) return 'N/A';
    try {
      return new Date(dateString).toLocaleString('en-IN', {
        day: '2-digit',
        month: 'short',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return 'Invalid Date';
    }
  };

  const showOrderDetails = (order) => {
    setSelectedOrder(order);
    setDetailsOpen(true);
  };

  return (
    <Box sx={{ p: 3 }}>
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
              <OrderIcon sx={{ fontSize: 28 }} />
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
                Live Order Tracker
              </Typography>
              <Typography variant="h6" sx={{ color: 'rgba(255, 255, 255, 0.8)' }}>
                Real-time order execution monitoring
              </Typography>
            </Box>
          </Box>
          
          <Box sx={{ display: 'flex', gap: 2 }}>
            <Tooltip title={monitoringActive ? "Stop Monitoring" : "Start Monitoring"}>
              <Button
                variant={monitoringActive ? "outlined" : "contained"}
                startIcon={monitoringActive ? <StopIcon /> : <StartIcon />}
                onClick={monitoringActive ? stopMonitoring : startMonitoring}
                sx={{
                  borderColor: monitoringActive ? '#EF4444' : '#10B981',
                  color: monitoringActive ? '#EF4444' : '#10B981',
                  background: monitoringActive ? 'transparent' : 'rgba(16, 185, 129, 0.1)',
                  '&:hover': {
                    borderColor: monitoringActive ? '#EF4444' : '#10B981',
                    background: monitoringActive ? 'rgba(239, 68, 68, 0.1)' : 'rgba(16, 185, 129, 0.2)',
                  },
                }}
              >
                {monitoringActive ? 'Stop Monitoring' : 'Start Monitoring'}
              </Button>
            </Tooltip>
            <Tooltip title="Refresh Orders">
              <IconButton
                onClick={fetchLiveOrders}
                disabled={loading}
                sx={{
                  background: 'rgba(255, 255, 255, 0.1)',
                  '&:hover': { background: 'rgba(255, 255, 255, 0.2)' },
                }}
              >
                <RefreshIcon />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>

        {/* Status Indicator */}
        {monitoringActive && (
          <Box sx={{ mb: 3 }}>
            <Alert
              severity="info"
              sx={{
                background: 'rgba(0, 122, 255, 0.1)',
                border: '1px solid rgba(0, 122, 255, 0.3)',
                color: 'rgba(255, 255, 255, 0.9)',
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Typography variant="body2">
                  Live monitoring active - Orders are being checked every 10 seconds
                </Typography>
                <LinearProgress
                  sx={{
                    width: 100,
                    height: 4,
                    borderRadius: 2,
                    backgroundColor: 'rgba(255, 255, 255, 0.2)',
                    '& .MuiLinearProgress-bar': {
                      backgroundColor: '#007AFF',
                    },
                  }}
                />
              </Box>
            </Alert>
          </Box>
        )}

        {/* Summary Cards */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} md={3}>
            <Card sx={{ background: 'linear-gradient(135deg, #007AFF 0%, #5856D6 100%)', color: 'white' }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <OrderIcon sx={{ fontSize: 40 }} />
                  <Box>
                    <Typography variant="h6" sx={{ fontWeight: 600 }}>Total Orders</Typography>
                    <Typography variant="h4" sx={{ fontWeight: 700 }}>
                      {orderSummary.total_orders || 0}
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={3}>
            <Card sx={{ background: 'linear-gradient(135deg, #10B981 0%, #059669 100%)', color: 'white' }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <CompleteIcon sx={{ fontSize: 40 }} />
                  <Box>
                    <Typography variant="h6" sx={{ fontWeight: 600 }}>Completed</Typography>
                    <Typography variant="h4" sx={{ fontWeight: 700 }}>
                      {orderSummary.completed || 0}
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={3}>
            <Card sx={{ background: 'linear-gradient(135deg, #F59E0B 0%, #F97316 100%)', color: 'white' }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <PendingIcon sx={{ fontSize: 40 }} />
                  <Box>
                    <Typography variant="h6" sx={{ fontWeight: 600 }}>Pending</Typography>
                    <Typography variant="h4" sx={{ fontWeight: 700 }}>
                      {orderSummary.pending || 0}
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={3}>
            <Card sx={{ background: 'rgba(28, 28, 30, 0.8)', border: '1px solid rgba(255, 255, 255, 0.1)', color: 'white' }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <MoneyIcon sx={{ fontSize: 40 }} />
                  <Box>
                    <Typography variant="h6" sx={{ fontWeight: 600 }}>Total Value</Typography>
                    <Typography variant="h6" sx={{ fontWeight: 700 }}>
                      {formatCurrency(orderSummary.total_value)}
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Orders Table */}
        <Card sx={{ background: 'rgba(28, 28, 30, 0.8)', border: '1px solid rgba(255, 255, 255, 0.1)' }}>
          <CardContent sx={{ p: 0 }}>
            {loading && <LinearProgress />}
            
            {liveOrders.length > 0 ? (
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow sx={{ '& .MuiTableCell-head': { borderBottom: '1px solid rgba(255, 255, 255, 0.1)' } }}>
                      <TableCell sx={{ color: 'rgba(255, 255, 255, 0.9)', fontWeight: 600 }}>Status</TableCell>
                      <TableCell sx={{ color: 'rgba(255, 255, 255, 0.9)', fontWeight: 600 }}>Symbol</TableCell>
                      <TableCell sx={{ color: 'rgba(255, 255, 255, 0.9)', fontWeight: 600 }}>Action</TableCell>
                      <TableCell sx={{ color: 'rgba(255, 255, 255, 0.9)', fontWeight: 600 }} align="right">Quantity</TableCell>
                      <TableCell sx={{ color: 'rgba(255, 255, 255, 0.9)', fontWeight: 600 }} align="right">Price</TableCell>
                      <TableCell sx={{ color: 'rgba(255, 255, 255, 0.9)', fontWeight: 600 }}>Order ID</TableCell>
                      <TableCell sx={{ color: 'rgba(255, 255, 255, 0.9)', fontWeight: 600 }}>Placed</TableCell>
                      <TableCell sx={{ color: 'rgba(255, 255, 255, 0.9)', fontWeight: 600 }}>Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {liveOrders.map((order, index) => (
                      <TableRow
                        key={index}
                        sx={{
                          '& .MuiTableCell-body': {
                            borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
                            color: 'rgba(255, 255, 255, 0.9)',
                          },
                          '&:hover': { background: 'rgba(255, 255, 255, 0.02)' },
                        }}
                      >
                        <TableCell>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            {getStatusIcon(order.status)}
                            <Chip
                              label={order.status}
                              size="small"
                              sx={{
                                background: `rgba(${getStatusColor(order.status)
                                  .replace('#', '')
                                  .match(/.{2}/g)
                                  .map(hex => parseInt(hex, 16))
                                  .join(', ')}, 0.2)`,
                                color: getStatusColor(order.status),
                                border: `1px solid ${getStatusColor(order.status)}40`,
                              }}
                            />
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body1" sx={{ fontWeight: 600 }}>
                            {order.symbol}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={order.action}
                            size="small"
                            sx={{
                              background: order.action === 'BUY' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)',
                              color: order.action === 'BUY' ? '#10B981' : '#EF4444',
                            }}
                          />
                        </TableCell>
                        <TableCell align="right">
                          <Typography variant="body1" sx={{ fontWeight: 600 }}>
                            {order.shares}
                          </Typography>
                        </TableCell>
                        <TableCell align="right">
                          <Typography variant="body1">
                            {formatCurrency(order.price)}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                            {order.zerodha_order_id || 'N/A'}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" sx={{ color: 'rgba(255, 255, 255, 0.6)' }}>
                            {formatDateTime(order.placed_time)}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Box sx={{ display: 'flex', gap: 1 }}>
                            <Tooltip title="View Details">
                              <IconButton
                                size="small"
                                onClick={() => showOrderDetails(order)}
                                sx={{ color: 'rgba(255, 255, 255, 0.7)' }}
                              >
                                <ViewIcon />
                              </IconButton>
                            </Tooltip>
                            {order.zerodha_order_id && (
                              <Tooltip title="Update Status">
                                <IconButton
                                  size="small"
                                  onClick={() => updateOrderStatus(order.zerodha_order_id)}
                                  sx={{ color: 'rgba(255, 255, 255, 0.7)' }}
                                >
                                  <RefreshIcon />
                                </IconButton>
                              </Tooltip>
                            )}
                          </Box>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            ) : (
              <Box sx={{ p: 4, textAlign: 'center' }}>
                <OrderIcon sx={{ fontSize: 64, color: 'rgba(255, 255, 255, 0.3)', mb: 2 }} />
                <Typography variant="h6" sx={{ mb: 1 }}>No Live Orders</Typography>
                <Typography variant="body2" sx={{ color: 'rgba(255, 255, 255, 0.6)' }}>
                  No live orders have been placed yet.
                </Typography>
              </Box>
            )}
          </CardContent>
        </Card>
      </motion.div>

      {/* Order Details Dialog */}
      <Dialog
        open={detailsOpen}
        onClose={() => setDetailsOpen(false)}
        maxWidth="md"
        fullWidth
        PaperProps={{
          sx: {
            background: 'rgba(28, 28, 30, 0.95)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            color: 'white',
          },
        }}
      >
        <DialogTitle>Order Details</DialogTitle>
        <DialogContent>
          {selectedOrder && (
            <Box sx={{ mt: 2 }}>
              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <Paper sx={{ p: 2, background: 'rgba(255, 255, 255, 0.05)' }}>
                    <Typography variant="h6" sx={{ mb: 2 }}>Basic Information</Typography>
                    <Typography><strong>Symbol:</strong> {selectedOrder.symbol}</Typography>
                    <Typography><strong>Action:</strong> {selectedOrder.action}</Typography>
                    <Typography><strong>Quantity:</strong> {selectedOrder.shares}</Typography>
                    <Typography><strong>Price:</strong> {formatCurrency(selectedOrder.price)}</Typography>
                    <Typography><strong>Order Type:</strong> {selectedOrder.order_type}</Typography>
                  </Paper>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Paper sx={{ p: 2, background: 'rgba(255, 255, 255, 0.05)' }}>
                    <Typography variant="h6" sx={{ mb: 2 }}>Status Information</Typography>
                    <Typography><strong>Status:</strong> {selectedOrder.status}</Typography>
                    <Typography><strong>Zerodha Order ID:</strong> {selectedOrder.zerodha_order_id || 'N/A'}</Typography>
                    <Typography><strong>Placed Time:</strong> {formatDateTime(selectedOrder.placed_time)}</Typography>
                    <Typography><strong>Last Checked:</strong> {formatDateTime(selectedOrder.last_checked)}</Typography>
                  </Paper>
                </Grid>
                {selectedOrder.execution_details && (
                  <Grid item xs={12}>
                    <Paper sx={{ p: 2, background: 'rgba(255, 255, 255, 0.05)' }}>
                      <Typography variant="h6" sx={{ mb: 2 }}>Execution Details</Typography>
                      <Typography><strong>Filled Quantity:</strong> {selectedOrder.execution_details.filled_quantity}</Typography>
                      <Typography><strong>Pending Quantity:</strong> {selectedOrder.execution_details.pending_quantity}</Typography>
                      <Typography><strong>Average Price:</strong> {formatCurrency(selectedOrder.execution_details.average_price)}</Typography>
                      <Typography><strong>Status Message:</strong> {selectedOrder.execution_details.status_message}</Typography>
                    </Paper>
                  </Grid>
                )}
              </Grid>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailsOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default LiveOrderTracker;