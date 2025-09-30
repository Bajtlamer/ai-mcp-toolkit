# Changelog

All notable changes to the AI MCP Toolkit project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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