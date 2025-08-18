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
  IconButton,
  Button,
  Alert,
  TablePagination,
  Tooltip,
  Avatar,
  TextField,
  InputAdornment,
  Chip,
  Grid,
} from '@mui/material';
import {
  TrendingUp as StocksIcon,
  Refresh as RefreshIcon,
  Search as SearchIcon,
  TrendingUp as UpIcon,
  TrendingDown as DownIcon,
  TrendingFlat as FlatIcon,
  Storage as StorageIcon,
  Analytics as AnalyticsIcon,
  Assessment as AssessmentIcon,
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import toast from 'react-hot-toast';

// Components
import LoadingScreen from '../../components/UI/LoadingScreen';

// Hooks
import { useCsvStocks, useForceCsvRefreshMutation } from '../../hooks/useApi';

const Stocks = () => {
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);
  const [searchTerm, setSearchTerm] = useState('');

  const { data: csvStocks, isLoading: csvLoading, refetch: refetchCsv } = useCsvStocks();
  const forceCsvRefreshMutation = useForceCsvRefreshMutation();

  const csvData = csvStocks?.data;
  const stocks = csvData?.stocks || [];

  const handleRefresh = () => {
    refetchCsv();
    toast.success('Stocks data refreshed');
  };

  const handleForceRefresh = () => {
    forceCsvRefreshMutation.mutate(undefined, {
      onSuccess: () => {
        refetchCsv();
        toast.success('CSV data forcefully refreshed');
      },
      onError: () => {
        toast.error('Failed to refresh CSV data');
      }
    });
  };

  const formatPrice = (price) => {
    if (typeof price === 'number') {
      return `₹${price.toFixed(2)}`;
    }
    return 'N/A';
  };

  const formatDate = (dateString) => {
    try {
      if (!dateString) return 'N/A';
      const date = new Date(dateString);
      if (isNaN(date.getTime())) return 'N/A';
      return date.toLocaleString('en-IN', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
      });
    } catch (error) {
      return 'N/A';
    }
  };

  const getPriceChangeColor = (change) => {
    if (!change || change === 0) return 'rgba(255, 255, 255, 0.7)';
    return change > 0 ? '#10B981' : '#EF4444';
  };

  const getPriceChangeIcon = (change) => {
    if (!change || change === 0) return <FlatIcon />;
    return change > 0 ? <UpIcon /> : <DownIcon />;
  };

  // Filter stocks based on search term
  const filteredStocks = stocks.filter(stock =>
    stock.symbol?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    stock.name?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Pagination
  const paginatedStocks = filteredStocks.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage);

  // Loading state
  if (csvLoading) {
    return <LoadingScreen message="Loading stocks data..." />;
  }

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
              <StocksIcon sx={{ fontSize: 28 }} />
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
                CSV Stocks
              </Typography>
              <Typography variant="h6" sx={{ color: 'rgba(255, 255, 255, 0.8)' }}>
                Live stock prices from CSV data
              </Typography>
            </Box>
          </Box>
          
          <Box sx={{ display: 'flex', gap: 2 }}>
            <Tooltip title="Force CSV Refresh">
              <Button
                variant="outlined"
                startIcon={<StorageIcon />}
                onClick={handleForceRefresh}
                disabled={forceCsvRefreshMutation.isLoading}
                sx={{
                  borderColor: '#F59E0B',
                  color: '#F59E0B',
                  '&:hover': {
                    borderColor: '#F59E0B',
                    background: 'rgba(245, 158, 11, 0.1)',
                  },
                }}
              >
                {forceCsvRefreshMutation.isLoading ? 'Refreshing...' : 'Force Refresh'}
              </Button>
            </Tooltip>
            <Tooltip title="Refresh Stocks">
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
                  <StorageIcon sx={{ fontSize: 40 }} />
                  <Box>
                    <Typography variant="h6" sx={{ fontWeight: 600 }}>
                      Total Stocks
                    </Typography>
                    <Typography variant="h4" sx={{ fontWeight: 700 }}>
                      {stocks.length}
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
                  <AnalyticsIcon sx={{ fontSize: 40 }} />
                  <Box>
                    <Typography variant="h6" sx={{ fontWeight: 600 }}>
                      Market Status
                    </Typography>
                    <Typography variant="h6" sx={{ fontWeight: 700 }}>
                      {csvData?.price_data_status?.market_open ? 'Open' : 'Closed'}
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
                  <AssessmentIcon sx={{ fontSize: 40 }} />
                  <Box>
                    <Typography variant="h6" sx={{ fontWeight: 600 }}>
                      Success Rate
                    </Typography>
                    <Typography variant="h4" sx={{ fontWeight: 700 }}>
                      {csvData?.price_data_status?.success_rate || 0}%
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={3}>
            <Card
              sx={{
                background: 'rgba(28, 28, 30, 0.8)',
                backdropFilter: 'blur(20px)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                color: 'white',
              }}
            >
              <CardContent>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>
                  Last Updated
                </Typography>
                <Typography variant="body2" sx={{ color: 'rgba(255, 255, 255, 0.8)' }}>
                  {formatDate(csvData?.csv_info?.fetch_time)}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Search */}
        <Box sx={{ mb: 3 }}>
          <TextField
            fullWidth
            placeholder="Search stocks by symbol or name..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon sx={{ color: 'rgba(255, 255, 255, 0.5)' }} />
                </InputAdornment>
              ),
            }}
            sx={{
              maxWidth: 400,
              '& .MuiOutlinedInput-root': {
                background: 'rgba(255, 255, 255, 0.05)',
                color: 'white',
                '& fieldset': {
                  borderColor: 'rgba(255, 255, 255, 0.2)',
                },
                '&:hover fieldset': {
                  borderColor: 'rgba(255, 255, 255, 0.3)',
                },
                '&.Mui-focused fieldset': {
                  borderColor: '#007AFF',
                },
              },
              '& .MuiInputBase-input::placeholder': {
                color: 'rgba(255, 255, 255, 0.5)',
                opacity: 1,
              },
            }}
          />
        </Box>

        {/* Stocks Table */}
        <Card
          sx={{
            background: 'rgba(28, 28, 30, 0.8)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
          }}
        >
          <CardContent sx={{ p: 0 }}>
            {stocks.length > 0 ? (
              <>
                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow sx={{ '& .MuiTableCell-head': { borderBottom: '1px solid rgba(255, 255, 255, 0.1)' } }}>
                        <TableCell sx={{ color: 'rgba(255, 255, 255, 0.9)', fontWeight: 600 }}>
                          Symbol
                        </TableCell>
                        <TableCell sx={{ color: 'rgba(255, 255, 255, 0.9)', fontWeight: 600 }}>
                          Name
                        </TableCell>
                        <TableCell sx={{ color: 'rgba(255, 255, 255, 0.9)', fontWeight: 600 }} align="right">
                          Price
                        </TableCell>
                        <TableCell sx={{ color: 'rgba(255, 255, 255, 0.9)', fontWeight: 600 }} align="right">
                          Change
                        </TableCell>
                        <TableCell sx={{ color: 'rgba(255, 255, 255, 0.9)', fontWeight: 600 }} align="right">
                          Change %
                        </TableCell>
                        <TableCell sx={{ color: 'rgba(255, 255, 255, 0.9)', fontWeight: 600 }}>
                          Status
                        </TableCell>
                        <TableCell sx={{ color: 'rgba(255, 255, 255, 0.9)', fontWeight: 600 }}>
                          Last Updated
                        </TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {paginatedStocks.map((stock, index) => (
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
                            <Typography variant="body1" sx={{ fontWeight: 600 }}>
                              {stock.symbol || 'N/A'}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2" sx={{ color: 'rgba(255, 255, 255, 0.8)' }}>
                              {stock.name || stock.symbol || 'N/A'}
                            </Typography>
                          </TableCell>
                          <TableCell align="right">
                            <Typography variant="body1" sx={{ fontWeight: 600 }}>
                              {formatPrice(stock.current_price || stock.price)}
                            </Typography>
                          </TableCell>
                          <TableCell align="right">
                            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 0.5 }}>
                              <Avatar
                                sx={{
                                  width: 24,
                                  height: 24,
                                  background: getPriceChangeColor(stock.price_change),
                                }}
                              >
                                {getPriceChangeIcon(stock.price_change)}
                              </Avatar>
                              <Typography
                                variant="body2"
                                sx={{
                                  color: getPriceChangeColor(stock.price_change),
                                  fontWeight: 500,
                                }}
                              >
                                {stock.price_change ? stock.price_change.toFixed(2) : '0.00'}
                              </Typography>
                            </Box>
                          </TableCell>
                          <TableCell align="right">
                            <Typography
                              variant="body2"
                              sx={{
                                color: getPriceChangeColor(stock.price_change_percent),
                                fontWeight: 500,
                              }}
                            >
                              {stock.price_change_percent ? `${stock.price_change_percent.toFixed(2)}%` : '0.00%'}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Chip
                              label={stock.status || 'Available'}
                              size="small"
                              sx={{
                                background: stock.status === 'error' ? 'rgba(239, 68, 68, 0.2)' : 'rgba(16, 185, 129, 0.2)',
                                color: stock.status === 'error' ? '#EF4444' : '#10B981',
                                border: stock.status === 'error' ? '1px solid rgba(239, 68, 68, 0.4)' : '1px solid rgba(16, 185, 129, 0.4)',
                              }}
                            />
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2" sx={{ color: 'rgba(255, 255, 255, 0.6)' }}>
                              {formatDate(stock.last_updated || stock.timestamp)}
                            </Typography>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>

                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', px: 2, py: 1, borderTop: '1px solid rgba(255, 255, 255, 0.1)' }}>
                  <Typography variant="body2" sx={{ color: 'rgba(255, 255, 255, 0.7)' }}>
                    Showing {paginatedStocks.length} of {filteredStocks.length} stocks
                    {searchTerm && ` (filtered from ${stocks.length} total)`}
                  </Typography>
                  <TablePagination
                    component="div"
                    count={filteredStocks.length}
                    page={page}
                    onPageChange={(event, newPage) => setPage(newPage)}
                    rowsPerPage={rowsPerPage}
                    onRowsPerPageChange={(event) => {
                      setRowsPerPage(parseInt(event.target.value, 10));
                      setPage(0);
                    }}
                    sx={{
                      color: 'rgba(255, 255, 255, 0.7)',
                      '& .MuiSelect-icon': {
                        color: 'rgba(255, 255, 255, 0.7)',
                      },
                      '& .MuiTablePagination-toolbar': {
                        minHeight: 'auto',
                      },
                    }}
                  />
                </Box>
              </>
            ) : (
              <Box sx={{ p: 4, textAlign: 'center' }}>
                <StocksIcon sx={{ fontSize: 64, color: 'rgba(255, 255, 255, 0.3)', mb: 2 }} />
                <Typography variant="h6" sx={{ mb: 1 }}>
                  No Stocks Data Available
                </Typography>
                <Typography variant="body2" sx={{ color: 'rgba(255, 255, 255, 0.6)', mb: 2 }}>
                  CSV stock data is not available. Try refreshing or forcing a CSV refresh.
                </Typography>
                <Button
                  variant="contained"
                  onClick={handleForceRefresh}
                  disabled={forceCsvRefreshMutation.isLoading}
                  sx={{
                    background: 'linear-gradient(135deg, #007AFF 0%, #5856D6 100%)',
                  }}
                >
                  {forceCsvRefreshMutation.isLoading ? 'Loading...' : 'Load CSV Data'}
                </Button>
              </Box>
            )}
          </CardContent>
        </Card>

        {/* CSV Info */}
        {csvData?.csv_info && (
          <Alert
            severity="info"
            sx={{
              mt: 3,
              background: 'rgba(0, 122, 255, 0.1)',
              border: '1px solid rgba(0, 122, 255, 0.3)',
              color: 'rgba(255, 255, 255, 0.9)',
            }}
          >
            <Typography variant="body2">
              <strong>CSV Info:</strong> {csvData.csv_info.total_symbols} symbols loaded, 
              Hash: {csvData.csv_info.csv_hash?.substring(0, 8)}..., 
              Last fetched: {formatDate(csvData.csv_info.fetch_time)}
            </Typography>
          </Alert>
        )}
      </motion.div>
    </Container>
  );
};

export default Stocks;