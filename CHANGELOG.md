# Changelog

All notable changes to the AI MCP Toolkit project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### 🔧 Fixed
- **Model Switching Without Restart** - Fixed `/ollama/models/switch` endpoint to physically unload old model and load new one
  - Previously only updated Python config variable, requiring server restart
  - Now uses `keep_alive: 0` to unload old model (like `ollama stop`)
  - Pre-loads new model with warmup prompt (like `ollama run`)
  - No server restart needed after switching models
  - Matches behavior of the original bash script `switch-model.sh`

---

## [0.3.0] - 2025-01-18

### 🚀 Major Features & Enhancements

#### Added
- **GPU Monitoring Dashboard** - Real-time GPU performance monitoring with web UI
- **Network Access Support** - Full remote access capability for multi-machine deployment
- **Enhanced Navigation** - Expandable submenu system with smooth animations
- **Advanced Text Cleaning** - Improved symbol removal with better default behavior
- **Cross-Platform Optimization** - Intelligent environment detection and configuration

#### Enhanced
- **GPU Performance Tracking** - Comprehensive monitoring of NVIDIA RTX 3070 Ti utilization
- **API Integration** - New endpoints for GPU health, metrics, and recommendations
- **User Experience** - ChatGPT-like interface with improved conversation management
- **Text Processing** - Enhanced Text Cleaner with automatic problematic symbol removal
- **Mobile Responsiveness** - Optimized layouts for all device sizes

#### Fixed
- **Navigation Issues** - Resolved AI Agents submenu expansion problems
- **Text Cleaning** - Fixed symbol removal to show visible improvements
- **Network Deployment** - Resolved localhost dependency issues for remote access
- **UI Consistency** - Improved visual hierarchy and component interactions

### 🔧 Technical Improvements

#### GPU Acceleration
- Real-time GPU utilization monitoring (100% utilization achieved)
- Performance metrics tracking with tokens/second measurement
- Temperature and memory usage optimization
- Automated optimization recommendations

#### Network Architecture
- Server-side API proxy for Ollama integration
- CORS configuration for cross-origin requests
- Environment-based host configuration (0.0.0.0 support)
- Seamless remote access without localhost dependencies

#### UI/UX Enhancements
- Interactive submenu expansion with visual feedback
- Smooth CSS transitions and animations
- Improved mobile responsiveness
- Better error handling and loading states

### 📚 Documentation
- Updated README with comprehensive feature descriptions
- Added GPU monitoring setup guides
- Enhanced configuration documentation
- Cross-platform installation instructions

### 🛠️ Development
- Improved component architecture in Svelte
- Enhanced state management for conversations
- Better error boundaries and fallback mechanisms
- Optimized build process and performance

### Migration Notes
- **Breaking Changes**: None - fully backward compatible
- **New Features**: All enhancements are opt-in and work with existing configurations
- **Configuration**: No changes required - works with existing setups

---

## [0.2.0] - 2025-01-30

### 🎨 Major UI/UX Overhaul - Enhanced Chat Interface

#### Added
- **ChatGPT-like Modern Interface** - Complete redesign of the chat interface with professional, modern styling
- **Smart Auto-Scroll System** - Intelligent automatic scrolling with user scroll position detection (50px threshold)
- **Advanced Conversation Management**:
  - Create, rename, and delete individual conversations
  - Bulk "Clear All" functionality with confirmation dialog
  - Search and filter conversations by title and content
  - Timeline organization (Today, Yesterday, This Week, etc.)
- **Enhanced Message Features**:
  - Copy messages with one-click functionality
  - Response regeneration for better AI answers
  - Request cancellation mid-generation
  - Real-time performance metrics (response time, tokens/second)
- **Dynamic Message Styling**:
  - Adaptive message bubble widths based on content length
  - User messages: `max-w-fit` with `min-w-[100px]` and `max-w-[80%]` constraints
  - Darker user message backgrounds (`bg-gray-200 dark:bg-gray-700`)
  - Consistent typography between user and AI messages
- **Responsive Sidebar**:
  - Collapsible conversation history (30% width when open)
  - Mobile-optimized with touch-friendly interactions
  - Conversation statistics and metrics display

#### Enhanced
- **Visual Design Improvements**:
  - Clean visual hierarchy with proper spacing (`py-4`, `space-y-3`)
  - Smooth animations and transitions
  - Professional ChatGPT-inspired layout
  - Dark/light theme consistency across all components
- **Performance Optimizations**:
  - Optimized chat container height calculation (`calc(100vh - 6.1rem)`)
  - Efficient DOM updates with `requestAnimationFrame`
  - Smart scroll detection to preserve user reading position
- **User Experience**:
  - Info bar repositioned to the right for better visual flow
  - Removed edit functionality (focused on copy-only for clarity)
  - Persistent conversation state across browser sessions
  - Auto-titling of conversations based on first user message

#### Fixed
- **Scroll Behavior**: Fixed chat container scrolling issues with proper height calculations
- **Message Positioning**: Resolved icon positioning problems with absolute positioning
- **Container Gaps**: Eliminated unwanted spacing caused by floating elements
- **Font Consistency**: Standardized text sizing between user and AI messages (`prose prose-gray` instead of `prose-sm`)

### 🔧 Technical Improvements

#### Enhanced
- **Real-time Model Detection**: Dynamic model switching without application restart
- **GPU Monitoring Integration**: Comprehensive system metrics dashboard
- **API Error Handling**: Improved fallback mechanisms and error recovery
- **Mobile Responsiveness**: Optimized layouts for all device sizes
- **Code Quality**: Removed unused imports and cleaned up component structure

#### Security
- **Input Validation**: Enhanced security measures for user input processing
- **Error Handling**: Improved error boundaries and graceful failure recovery

### 📚 Documentation

#### Added
- **Enhanced Chat Interface Section**: Comprehensive documentation of new UI features
- **Usage Guidelines**: Step-by-step instructions for using the modern interface
- **Recent Updates Section**: Clear changelog integration in README.md

#### Updated
- **README.md**: Complete overhaul with current feature descriptions
- **API Documentation**: Updated endpoints and integration examples
- **Configuration Guide**: Enhanced with new UI-related settings

### 🛠️ Development

#### Improved
- **Component Architecture**: Cleaner separation of concerns in Svelte components
- **State Management**: Enhanced conversation state handling with better persistence
- **Build Process**: Optimized frontend build configuration

### Migration Notes

- **Breaking Changes**: None - fully backward compatible
- **New Features**: All new chat interface features are enabled by default
- **Configuration**: No configuration changes required - works with existing setups

### Contributors

Special thanks to all contributors who helped make this release possible through testing, feedback, and feature requests.

---

## [0.1.0] - Initial Release

### Added
- Initial MCP protocol implementation
- Basic text processing agents
- Ollama integration
- Command-line interface
- Basic web UI
- Docker support
- Core configuration system