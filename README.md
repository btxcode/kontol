# Kamehameha Tools Scanner

An advanced web-based vulnerability scanning and security assessment platform that integrates professional security tools with a modern, user-friendly interface.

## Key Features

### 1. Modern Interface
- Sleek, responsive design that works on all devices
- Dark/light theme support with smooth transitions
- Goku-inspired theme elements (ninja icon with power-up animation)
- Real-time feedback and loading animations
- Clean, intuitive navigation

### 2. Advanced Scanning Capabilities
- **Subdomain Discovery** (via Subfinder):
  * Comprehensive subdomain enumeration
  * Multiple source integration
  * Fast and accurate results
- **HTTP Probing** (via httpx):
  * Active server detection
  * Technology fingerprinting
  * SSL/TLS analysis
  * Port scanning
- **Vulnerability Scanning** (via nuclei):
  * Extensive template library
  * Custom template support
  * Multiple severity levels
  * CVSS score integration

### 3. Results Visualization
- Interactive bar charts for vulnerability statistics
- Severity-based categorization (Critical, High, Medium, Low, Info)
- Detailed findings table with:
  * Template information
  * Protocol details
  * Severity indicators
  * Target specifics
- Sortable and filterable results

### 4. Data Management
- Hierarchical organization:
  * Company level
  * Date based grouping
  * Time-specific scans
- Persistent storage of results
- Easy navigation between scans
- Historical data comparison

## Technical Details

### Project Structure
```
vulnerability_scanner/
├── backend/
│   ├── app.py             # Flask application & API endpoints
│   ├── config.py          # Configuration settings
│   ├── scanner.py         # Security tools integration
│   ├── utils.py           # Utility functions
│   └── scan_results/      # Hierarchical result storage
│       └── [company]/
│           └── [date]/
│               └── [time]/
│                   └── result.json
├── frontend/
│   ├── index.html         # Main application interface
│   ├── script.js          # Frontend logic & interactions
│   ├── styles.css         # Styling and animations
│   └── km.gif            # Theme assets
├── requirements.txt       # Python dependencies
└── run.py                # Application entry point
```

### Frontend Components
1. **Interface Elements**
   - Responsive header with animated logo
   - Dynamic form validation
   - Modal dialogs for results
   - Loading overlays with spinners
   - Interactive charts using Chart.js

2. **JavaScript Features**
   - Real-time form validation
   - Dynamic chart generation
   - Modal management
   - API integration
   - Error handling
   - Theme switching

3. **CSS Features**
   - CSS variables for theming
   - Flexbox/Grid layouts
   - Custom animations
   - Media queries
   - Dark mode support

### Backend Components
1. **API Endpoints**
   ```
   POST /apiv1/scan
   - Starts new scan
   - Accepts: domain, company
   - Returns: scan status

   GET /apiv1/companies
   - Lists all companies
   - Returns: company list

   GET /apiv1/<company>/dates
   - Lists scan dates
   - Returns: date list

   GET /apiv1/<company>/<date>/times
   - Lists scan times
   - Returns: time list

   GET /apiv1/<company>/<date>/<time>/results
   - Gets scan results
   - Returns: detailed findings
   ```

2. **Scanner Integration**
   - Subprocess management
   - Tool output parsing
   - Result aggregation
   - Error handling

3. **Data Storage**
   - JSON-based storage
   - Hierarchical structure
   - Result caching
   - File management

### Prerequisites & Setup

1. **System Requirements**
   - Python 3.8+
   - Go 1.16+
   - 2GB RAM minimum
   - 500MB disk space

2. **Tool Installation**
   ```bash
   # Install Go
   sudo apt-get install golang

   # Install security tools
   GO111MODULE=on go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
   GO111MODULE=on go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest
   GO111MODULE=on go install -v github.com/projectdiscovery/nuclei/v2/cmd/nuclei@latest

   # Install Python dependencies
   pip install -r requirements.txt
   ```

3. **Running the Application**
   ```bash
   python run.py
   ```
   Access at: http://localhost:5000

## Usage Guide

1. **Starting a Scan**
   - Enter domain name (e.g., example.com)
   - Enter company name
   - Click "Launch Scan"

2. **Viewing Results**
   - Select company from list
   - Choose scan date
   - Select specific scan time
   - View statistics and findings

3. **Understanding Results**
   - Chart shows vulnerability distribution
   - Table provides detailed findings
   - Click entries for more details

## Security & Performance

### Security Considerations
- Ensure proper authorization before scanning
- Follow responsible disclosure practices
- Be aware of rate limiting and bandwidth usage
- Consider target server load
- Review local security laws and regulations

### Performance Features
- Async scan operations
- Result caching
- Optimized API calls
- Efficient data storage
- Resource management

### Error Handling
- Input validation with clear feedback
- Connection error recovery
- Tool failure management
- Result parsing fallbacks
- Storage error handling

## Future Enhancements
- Additional tool integration
- Advanced filtering options
- Custom template support
- Result export features
- API authentication
- Multi-user support

## License
This project is licensed under the MIT License - see the LICENSE file for details.
