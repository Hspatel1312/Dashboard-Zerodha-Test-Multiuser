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
  useRetryFailedOrdersMutation 
} from '../../hooks/useApi';

const Orders = () => {
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);
  const [resetDialogOpen, setResetDialogOpen] = useState(false);

  const { data: systemOrders, isLoading: ordersLoading, refetch: refetchOrders } = useSystemOrders();
  const { data: failedOrdersData, isLoading: failedOrdersLoading, refetch: refetchFailedOrders } = useFailedOrders();
  const resetOrdersMutation = useResetSystemOrdersMutation();
  const retryOrdersMutation = useRetryFailedOrdersMutation();

  const orders = systemOrders?.data?.orders || [];
  const failedOrders = failedOrdersData?.data?.failed_orders || [];
  const canRetryAll = failedOrdersData?.data?.can_retry_all || false;

  const handleRefresh = () => {
    refetchOrders();
    refetchFailedOrders();
    toast.success('Orders refreshed');
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
  const paginatedOrders = orders.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage);

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
                Track all your investment orders
              </Typography>
            </Box>
          </Box>
          
          <Box sx={{ display: 'flex', gap: 2 }}>
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
            <Tooltip title="Refresh Orders">
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
                {orders.filter(order => order.status !== 'FAILED' && order.status !== 'FAILED_MAX_RETRIES').length}
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
                {orders.filter(order => order.status === 'FAILED' || order.status === 'FAILED_MAX_RETRIES').length}
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
                          Price
                        </TableCell>
                        <TableCell sx={{ color: 'rgba(255, 255, 255, 0.9)', fontWeight: 600 }} align="right">
                          Total Value
                        </TableCell>
                        <TableCell sx={{ color: 'rgba(255, 255, 255, 0.9)', fontWeight: 600 }}>
                          Date & Time
                        </TableCell>
                        <TableCell sx={{ color: 'rgba(255, 255, 255, 0.9)', fontWeight: 600 }}>
                          Status
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
                            <Typography variant="body1" sx={{ fontWeight: 600 }}>
                              ₹{((order.shares || order.quantity || 0) * (order.price || 0)).toLocaleString()}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2" sx={{ color: 'rgba(255, 255, 255, 0.8)' }}>
                              {formatDate(order.execution_time || order.date)}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            {order.status === 'FAILED' ? (
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
                                {order.failure_reason && (
                                  <Typography variant="caption" sx={{ color: 'rgba(255, 255, 255, 0.6)', fontSize: '0.7rem' }}>
                                    {order.failure_reason}
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
                                {order.failure_reason && (
                                  <Typography variant="caption" sx={{ color: 'rgba(255, 255, 255, 0.6)', fontSize: '0.7rem' }}>
                                    {order.failure_reason}
                                  </Typography>
                                )}
                              </Box>
                            ) : (
                              <Chip
                                icon={<SuccessIcon />}
                                label={order.status || 'EXECUTED'}
                                size="small"
                                sx={{
                                  background: 'rgba(16, 185, 129, 0.2)',
                                  color: '#10B981',
                                  border: '1px solid rgba(16, 185, 129, 0.4)',
                                }}
                              />
                            )}
                          </TableCell>
                          <TableCell>
                            {order.status === 'FAILED' && order.can_retry ? (
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
                            ) : order.status === 'FAILED_MAX_RETRIES' ? (
                              <Typography variant="caption" sx={{ color: 'rgba(255, 255, 255, 0.5)' }}>
                                Cannot retry
                              </Typography>
                            ) : (
                              <Typography variant="caption" sx={{ color: 'rgba(255, 255, 255, 0.5)' }}>
                                -
                              </Typography>
                            )}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>

                <TablePagination
                  component="div"
                  count={orders.length}
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