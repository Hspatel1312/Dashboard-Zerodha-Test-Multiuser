import React from 'react';
import { Box, Typography, Button, Alert, Container } from '@mui/material';
import { Refresh as RefreshIcon } from '@mui/icons-material';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    this.setState({
      error: error,
      errorInfo: errorInfo
    });
  }

  render() {
    if (this.state.hasError) {
      return (
        <Container maxWidth="lg" sx={{ py: 4 }}>
          <Alert severity="error" sx={{ mb: 3 }}>
            <Typography variant="h6" sx={{ mb: 2 }}>
              Something went wrong with the Portfolio page
            </Typography>
            <Typography variant="body2" sx={{ mb: 2 }}>
              A JavaScript error occurred. Check the browser console for details.
            </Typography>
            {this.state.error && (
              <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem', mb: 2 }}>
                Error: {this.state.error.toString()}
              </Typography>
            )}
          </Alert>
          
          <Box sx={{ display: 'flex', gap: 2 }}>
            <Button
              variant="contained"
              startIcon={<RefreshIcon />}
              onClick={() => window.location.reload()}
              sx={{
                background: 'linear-gradient(135deg, #007AFF 0%, #5856D6 100%)',
              }}
            >
              Reload Page
            </Button>
            <Button
              variant="outlined"
              onClick={() => this.setState({ hasError: false, error: null, errorInfo: null })}
            >
              Try Again
            </Button>
          </Box>
        </Container>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;