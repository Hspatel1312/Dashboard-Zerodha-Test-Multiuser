import React, { Suspense } from 'react';
import { Routes, Route } from 'react-router-dom';
import { Box } from '@mui/material';
import { motion, AnimatePresence } from 'framer-motion';

// Components
import Layout from './components/Layout/Layout';
import LoadingScreen from './components/UI/LoadingScreen';

// Pages (lazy loaded for better performance)
const Dashboard = React.lazy(() => import('./pages/Dashboard/Dashboard'));
const Portfolio = React.lazy(() => import('./pages/Portfolio/Portfolio'));
const Orders = React.lazy(() => import('./pages/Orders/Orders'));
const Stocks = React.lazy(() => import('./pages/Stocks/Stocks'));
const Settings = React.lazy(() => import('./pages/Settings/Settings'));
const Login = React.lazy(() => import('./pages/Auth/Login'));

// Page transition variants
const pageVariants = {
  initial: {
    opacity: 0,
    y: 20,
  },
  in: {
    opacity: 1,
    y: 0,
  },
  out: {
    opacity: 0,
    y: -20,
  },
};

const pageTransition = {
  type: 'tween',
  ease: 'anticipate',
  duration: 0.5,
};

function App() {
  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #000000 0%, #111111 100%)',
        color: 'white',
      }}
    >
      <Layout>
        <AnimatePresence mode="wait">
          <Suspense fallback={<LoadingScreen />}>
            <Routes>
              <Route
                path="/"
                element={
                  <motion.div
                    initial="initial"
                    animate="in"
                    exit="out"
                    variants={pageVariants}
                    transition={pageTransition}
                  >
                    <Dashboard />
                  </motion.div>
                }
              />
              <Route
                path="/dashboard"
                element={
                  <motion.div
                    initial="initial"
                    animate="in"
                    exit="out"
                    variants={pageVariants}
                    transition={pageTransition}
                  >
                    <Dashboard />
                  </motion.div>
                }
              />
              <Route
                path="/portfolio"
                element={
                  <motion.div
                    initial="initial"
                    animate="in"
                    exit="out"
                    variants={pageVariants}
                    transition={pageTransition}
                  >
                    <Portfolio />
                  </motion.div>
                }
              />
              <Route
                path="/orders"
                element={
                  <motion.div
                    initial="initial"
                    animate="in"
                    exit="out"
                    variants={pageVariants}
                    transition={pageTransition}
                  >
                    <Orders />
                  </motion.div>
                }
              />
              <Route
                path="/stocks"
                element={
                  <motion.div
                    initial="initial"
                    animate="in"
                    exit="out"
                    variants={pageVariants}
                    transition={pageTransition}
                  >
                    <Stocks />
                  </motion.div>
                }
              />
              <Route
                path="/settings"
                element={
                  <motion.div
                    initial="initial"
                    animate="in"
                    exit="out"
                    variants={pageVariants}
                    transition={pageTransition}
                  >
                    <Settings />
                  </motion.div>
                }
              />
              <Route
                path="/login"
                element={
                  <motion.div
                    initial="initial"
                    animate="in"
                    exit="out"
                    variants={pageVariants}
                    transition={pageTransition}
                  >
                    <Login />
                  </motion.div>
                }
              />
            </Routes>
          </Suspense>
        </AnimatePresence>
      </Layout>
    </Box>
  );
}

export default App;