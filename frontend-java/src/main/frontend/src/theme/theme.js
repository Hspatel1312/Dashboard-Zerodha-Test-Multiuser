import { createTheme } from '@mui/material/styles';

// Premium Apple/Tesla inspired theme
const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#007AFF', // Apple Blue
      light: '#5AC8FA',
      dark: '#0051D5',
      contrastText: '#ffffff',
    },
    secondary: {
      main: '#5856D6', // Apple Purple
      light: '#AF52DE',
      dark: '#3A3A8C',
      contrastText: '#ffffff',
    },
    error: {
      main: '#FF3B30', // Apple Red
      light: '#FF6961',
      dark: '#D70015',
    },
    warning: {
      main: '#FF9500', // Apple Orange
      light: '#FFB84D',
      dark: '#CC7700',
    },
    success: {
      main: '#34C759', // Apple Green
      light: '#67E085',
      dark: '#1FA440',
    },
    info: {
      main: '#5AC8FA', // Apple Light Blue
      light: '#8ED6FB',
      dark: '#3AA0D1',
    },
    background: {
      default: '#000000',
      paper: 'rgba(28, 28, 30, 0.95)',
      surface: 'rgba(44, 44, 46, 0.8)',
    },
    text: {
      primary: '#ffffff',
      secondary: 'rgba(255, 255, 255, 0.7)',
      disabled: 'rgba(255, 255, 255, 0.3)',
    },
    divider: 'rgba(255, 255, 255, 0.1)',
  },
  typography: {
    fontFamily: [
      'Inter',
      '-apple-system',
      'BlinkMacSystemFont',
      '"SF Pro Display"',
      '"Segoe UI"',
      'Roboto',
      'sans-serif',
    ].join(','),
    h1: {
      fontWeight: 800,
      fontSize: '3.5rem',
      lineHeight: 1.1,
      letterSpacing: '-0.02em',
      background: 'linear-gradient(135deg, #007AFF 0%, #5856D6 50%, #FF2D92 100%)',
      backgroundClip: 'text',
      WebkitBackgroundClip: 'text',
      WebkitTextFillColor: 'transparent',
    },
    h2: {
      fontWeight: 700,
      fontSize: '2.5rem',
      lineHeight: 1.2,
      letterSpacing: '-0.01em',
    },
    h3: {
      fontWeight: 600,
      fontSize: '2rem',
      lineHeight: 1.3,
      letterSpacing: '-0.01em',
    },
    h4: {
      fontWeight: 600,
      fontSize: '1.5rem',
      lineHeight: 1.4,
    },
    h5: {
      fontWeight: 600,
      fontSize: '1.25rem',
      lineHeight: 1.4,
    },
    h6: {
      fontWeight: 600,
      fontSize: '1rem',
      lineHeight: 1.5,
    },
    body1: {
      fontSize: '1rem',
      lineHeight: 1.6,
      fontWeight: 400,
    },
    body2: {
      fontSize: '0.875rem',
      lineHeight: 1.5,
      fontWeight: 400,
    },
    button: {
      fontWeight: 600,
      fontSize: '0.875rem',
      textTransform: 'none',
      letterSpacing: '0.02em',
    },
    caption: {
      fontSize: '0.75rem',
      lineHeight: 1.4,
      fontWeight: 500,
      opacity: 0.7,
    },
  },
  shape: {
    borderRadius: 16,
  },
  spacing: 8,
  shadows: [
    'none',
    '0px 1px 3px rgba(0, 0, 0, 0.2)',
    '0px 2px 6px rgba(0, 0, 0, 0.15)',
    '0px 4px 12px rgba(0, 0, 0, 0.15)',
    '0px 8px 24px rgba(0, 0, 0, 0.15)',
    '0px 12px 32px rgba(0, 0, 0, 0.15)',
    '0px 16px 48px rgba(0, 0, 0, 0.15)',
    '0px 20px 64px rgba(0, 0, 0, 0.15)',
    '0px 24px 80px rgba(0, 0, 0, 0.15)',
    '0px 28px 96px rgba(0, 0, 0, 0.15)',
    // Tesla-inspired glow effects
    '0px 0px 20px rgba(0, 122, 255, 0.3)',
    '0px 0px 30px rgba(0, 122, 255, 0.4)',
    '0px 0px 40px rgba(0, 122, 255, 0.5)',
    '0px 0px 50px rgba(0, 122, 255, 0.6)',
    '0px 0px 60px rgba(0, 122, 255, 0.7)',
    // Premium glass effects
    '0px 8px 32px rgba(0, 0, 0, 0.3), 0px 0px 0px 1px rgba(255, 255, 255, 0.05)',
    '0px 12px 48px rgba(0, 0, 0, 0.4), 0px 0px 0px 1px rgba(255, 255, 255, 0.08)',
    '0px 16px 64px rgba(0, 0, 0, 0.5), 0px 0px 0px 1px rgba(255, 255, 255, 0.1)',
    '0px 20px 80px rgba(0, 0, 0, 0.6), 0px 0px 0px 1px rgba(255, 255, 255, 0.12)',
    // Ultra premium effects
    '0px 24px 96px rgba(0, 0, 0, 0.7), 0px 0px 0px 1px rgba(255, 255, 255, 0.15)',
    '0px 32px 128px rgba(0, 0, 0, 0.8), 0px 0px 0px 1px rgba(255, 255, 255, 0.2)',
    '0px 40px 160px rgba(0, 0, 0, 0.9), 0px 0px 0px 1px rgba(255, 255, 255, 0.25)',
    '0px 48px 192px rgba(0, 0, 0, 1), 0px 0px 0px 1px rgba(255, 255, 255, 0.3)',
    '0px 56px 224px rgba(0, 0, 0, 1), 0px 0px 0px 1px rgba(255, 255, 255, 0.35)',
    '0px 64px 256px rgba(0, 0, 0, 1), 0px 0px 0px 1px rgba(255, 255, 255, 0.4)',
  ],
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          background: 'linear-gradient(135deg, #000000 0%, #111111 100%)',
          '&::-webkit-scrollbar': {
            width: '8px',
          },
          '&::-webkit-scrollbar-track': {
            background: '#0a0a0a',
          },
          '&::-webkit-scrollbar-thumb': {
            background: 'linear-gradient(135deg, #333333 0%, #444444 100%)',
            borderRadius: '4px',
          },
          '&::-webkit-scrollbar-thumb:hover': {
            background: 'linear-gradient(135deg, #444444 0%, #555555 100%)',
          },
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          background: 'rgba(28, 28, 30, 0.95)',
          backdropFilter: 'blur(20px)',
          WebkitBackdropFilter: 'blur(20px)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          borderRadius: 16,
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          background: 'rgba(28, 28, 30, 0.8)',
          backdropFilter: 'blur(20px)',
          WebkitBackdropFilter: 'blur(20px)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          borderRadius: 16,
          transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          '&:hover': {
            transform: 'translateY(-4px)',
            boxShadow: '0px 20px 40px rgba(0, 0, 0, 0.3), 0px 0px 0px 1px rgba(255, 255, 255, 0.1)',
          },
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          textTransform: 'none',
          fontWeight: 600,
          fontSize: '0.875rem',
          padding: '12px 24px',
          transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          '&:hover': {
            transform: 'translateY(-2px)',
          },
        },
        contained: {
          background: 'linear-gradient(135deg, #007AFF 0%, #5856D6 100%)',
          boxShadow: '0px 4px 12px rgba(0, 122, 255, 0.3)',
          '&:hover': {
            background: 'linear-gradient(135deg, #1A8FFF 0%, #6B66E6 100%)',
            boxShadow: '0px 8px 25px rgba(0, 122, 255, 0.5)',
          },
        },
        outlined: {
          background: 'rgba(255, 255, 255, 0.05)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(255, 255, 255, 0.2)',
          '&:hover': {
            background: 'rgba(255, 255, 255, 0.1)',
            border: '1px solid rgba(255, 255, 255, 0.3)',
          },
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            background: 'rgba(255, 255, 255, 0.05)',
            backdropFilter: 'blur(20px)',
            borderRadius: 12,
            '& fieldset': {
              borderColor: 'rgba(255, 255, 255, 0.2)',
            },
            '&:hover fieldset': {
              borderColor: 'rgba(255, 255, 255, 0.3)',
            },
            '&.Mui-focused fieldset': {
              borderColor: '#007AFF',
              boxShadow: '0 0 0 3px rgba(0, 122, 255, 0.1)',
            },
          },
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          background: 'rgba(0, 0, 0, 0.8)',
          backdropFilter: 'blur(20px)',
          WebkitBackdropFilter: 'blur(20px)',
          border: 'none',
          borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
          boxShadow: '0px 4px 20px rgba(0, 0, 0, 0.3)',
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          background: 'rgba(0, 0, 0, 0.95)',
          backdropFilter: 'blur(20px)',
          WebkitBackdropFilter: 'blur(20px)',
          border: 'none',
          borderRight: '1px solid rgba(255, 255, 255, 0.1)',
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          background: 'rgba(255, 255, 255, 0.1)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(255, 255, 255, 0.2)',
          borderRadius: 8,
          fontWeight: 600,
        },
      },
    },
    MuiAlert: {
      styleOverrides: {
        root: {
          background: 'rgba(28, 28, 30, 0.9)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          borderRadius: 12,
        },
      },
    },
  },
});

export default theme;