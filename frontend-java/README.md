# Investment Dashboard - Premium Java Frontend

A premium investment rebalancing dashboard built with Spring Boot and React, featuring Apple and Tesla-inspired UI design.

## 🎯 Features

### Premium UI/UX
- **Apple-inspired Design**: Clean, minimalist interface with premium typography and spacing
- **Tesla-inspired Elements**: Futuristic glass morphism effects and smooth animations
- **Dark Theme**: Premium dark mode with subtle gradients and ambient lighting
- **Responsive Design**: Optimized for desktop, tablet, and mobile devices
- **Smooth Animations**: Framer Motion-powered transitions and micro-interactions

### Core Functionality
- **Real-time Portfolio Tracking**: Live portfolio values and performance metrics
- **Investment Management**: Initial investment setup and portfolio rebalancing
- **Zerodha Integration**: Secure authentication and live market data
- **Order Management**: Complete order history and transaction tracking
- **Stock Analysis**: CSV-based stock selection with live price feeds

### Technical Excellence
- **Spring Boot 3.2**: Modern Java backend with reactive programming
- **React 18**: Latest React with hooks and functional components
- **Material-UI v5**: Premium component library with custom theming
- **TypeScript**: Type-safe development (optional, can be added)
- **PWA Ready**: Progressive Web App capabilities

## 🚀 Quick Start

### Prerequisites
- Java 17 or higher
- Node.js 18 or higher
- Maven 3.8 or higher
- Python backend running on port 8000

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd frontend-java
   ```

2. **Install dependencies and build**
   ```bash
   mvn clean install
   ```

3. **Run the application**
   ```bash
   mvn spring-boot:run
   ```

4. **Access the application**
   ```
   http://localhost:8080
   ```

### Development Mode

For frontend development with hot reload:

```bash
cd src/main/frontend
npm start
```

This will start the React development server on port 3000 with proxy to the Spring Boot backend.

## 🏗️ Architecture

### Backend (Spring Boot)
```
src/main/java/com/investment/
├── InvestmentDashboardApplication.java    # Main application class
├── config/
│   ├── SecurityConfig.java               # Security configuration
│   └── WebConfig.java                    # CORS and routing config
├── controller/
│   ├── ApiController.java                # API proxy controller
│   └── MainController.java               # SPA routing controller
└── service/
    └── InvestmentApiService.java         # Python backend integration
```

### Frontend (React)
```
src/main/frontend/src/
├── components/
│   ├── Layout/                          # Layout components
│   ├── UI/                             # Reusable UI components
│   ├── Auth/                           # Authentication components
│   ├── Investment/                     # Investment flow components
│   └── Portfolio/                      # Portfolio components
├── pages/
│   ├── Dashboard/                      # Main dashboard
│   ├── Portfolio/                      # Portfolio page
│   ├── Orders/                         # Orders page
│   ├── Stocks/                         # Stocks page
│   └── Settings/                       # Settings page
├── hooks/
│   └── useApi.js                       # API hooks with React Query
├── theme/
│   └── theme.js                        # Material-UI theme
└── App.js                              # Main app component
```

## 🎨 Design System

### Color Palette
- **Primary**: #007AFF (Apple Blue)
- **Secondary**: #5856D6 (Apple Purple) 
- **Success**: #10B981 (Emerald)
- **Error**: #EF4444 (Red)
- **Warning**: #F59E0B (Amber)
- **Background**: #000000 to #111111 (Gradient)

### Typography
- **Primary Font**: Inter (System fallback: SF Pro Display)
- **Weights**: 300, 400, 500, 600, 700, 800, 900
- **Scale**: Harmonious type scale with proper hierarchy

### Effects
- **Glass Morphism**: Backdrop blur with subtle borders
- **Shadows**: Multi-layered shadows with color tints
- **Gradients**: Premium linear gradients for accents
- **Animations**: Smooth 60fps animations with proper easing

## 🔧 Configuration

### Backend Configuration (`application.yml`)
```yaml
investment:
  backend:
    url: http://127.0.0.1:8000  # Python backend URL
    timeout: 30000              # Request timeout in ms

server:
  port: 8080                    # Java frontend port
```

### Frontend Configuration
- **API Base URL**: Configured via axios defaults
- **Query Cache**: React Query with 30s stale time
- **Theme**: Customizable Material-UI theme

## 📱 Responsive Design

### Breakpoints
- **Mobile**: < 768px
- **Tablet**: 768px - 1024px  
- **Desktop**: > 1024px
- **Wide**: > 1400px

### Adaptive Features
- Collapsible sidebar on mobile
- Responsive grid layouts
- Touch-friendly interactions
- Optimized font sizes

## 🔒 Security

### Authentication
- Zerodha OAuth integration
- JWT token management
- Secure token storage
- Auto-refresh capabilities

### API Security
- CORS configuration
- Request timeout limits
- Error boundary protection
- Sanitized error messages

## 🚀 Performance

### Optimization Features
- Lazy-loaded routes
- Code splitting
- React Query caching
- Memoized components
- Optimized bundle size

### Monitoring
- Performance metrics
- Error tracking
- API response times
- User interaction analytics

## 🛠️ Development

### Available Scripts
- `mvn spring-boot:run` - Start the application
- `mvn clean install` - Build the application
- `mvn test` - Run tests
- `npm start` - Frontend development mode
- `npm run build` - Build frontend for production

### Adding New Features
1. Create React components in appropriate directories
2. Add API endpoints in `ApiController.java`
3. Implement backend service calls in `InvestmentApiService.java`
4. Add routes in `App.js`
5. Update navigation in `Layout.js`

## 📦 Build & Deployment

### Production Build
```bash
mvn clean package -Pprod
```

### Docker Deployment
```dockerfile
FROM openjdk:17-jdk-slim
COPY target/investment-dashboard-1.0.0.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "/app.jar"]
```

### Environment Variables
```bash
SPRING_PROFILES_ACTIVE=prod
INVESTMENT_BACKEND_URL=http://backend:8000
SERVER_PORT=8080
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the documentation
- Review the code examples

---

**Built with ❤️ using Spring Boot + React**