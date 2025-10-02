# Project Rules and Context
## AI MCP Toolkit Enhancement

This document establishes the rules, context, and guidelines for the AI MCP Toolkit enhancement project.

---

## Project Context

### Current State
- **Project**: AI MCP Toolkit - Text processing system with MCP protocol
- **Status**: Production-ready foundation with 8 AI agents
- **Architecture**: FastAPI backend + SvelteKit frontend + Ollama integration
- **Environment**: Development (local) + Production (own datacenter)

### Production Environment
- **Hardware**: Gigabyte Z590 AORUS ULTRA, i9-11900K, 128GB RAM, RTX 3070 Ti, 6.5TB storage
- **OS**: Ubuntu 25.04 (64-bit), Linux 6.14.0-32-generic
- **Database**: MongoDB Atlas cluster (existing)
- **Proxy**: NGINX (already deployed)
- **Location**: Own datacenter

### Enhancement Goals
1. **Complete MCP Protocol Implementation** - Add resources, prompts, messages
2. **AI Agent Cooperation** - Enable agents to work together
3. **Advanced Workflow Capabilities** - Pipeline processing and orchestration
4. **Production Scalability** - Handle multiple concurrent workflows

---

## Technology Rules

### Database Rules
- **Primary Database**: MongoDB Atlas (existing cluster)
- **ODM**: Beanie for async MongoDB operations
- **Drivers**: Motor (async) + PyMongo (sync)
- **Caching**: Redis for fast access and session storage
- **Migrations**: Use Beanie's built-in migration system

### Backend Rules
- **Framework**: FastAPI (keep existing)
- **Async**: Use asyncio throughout (no blocking operations)
- **Validation**: Pydantic for all data validation
- **Task Queue**: Celery with Redis broker
- **Authentication**: FastAPI-Users with JWT tokens
- **API Design**: RESTful + WebSocket + Server-Sent Events

### Frontend Rules
- **Framework**: SvelteKit (keep existing)
- **Language**: TypeScript (strict mode)
- **Styling**: Tailwind CSS (keep existing)
- **State Management**: Svelte stores + context
- **Real-time**: WebSocket + SSE for live updates
- **UI Components**: Custom components + Lucide icons

### Agent Rules
- **Base Class**: Inherit from existing BaseAgent
- **Communication**: Use Celery tasks + Redis pub/sub
- **State**: Store in MongoDB via Beanie models
- **Error Handling**: Comprehensive error handling and logging
- **Testing**: Unit tests for each agent + integration tests

---

## Development Rules

### Code Quality Rules
1. **Type Hints**: All functions must have type hints
2. **Docstrings**: All public functions must have docstrings
3. **Error Handling**: All external calls must be wrapped in try-catch
4. **Logging**: Use structured logging with appropriate levels
5. **Testing**: Minimum 80% test coverage for new code

### Git Rules
1. **Branching**: Feature branches for each enhancement phase
2. **Commits**: Descriptive commit messages with conventional format
3. **Reviews**: All code must be reviewed before merging
4. **Pre-commit**: Use pre-commit hooks for code quality

### API Rules
1. **RESTful**: Follow REST conventions for all endpoints
2. **Versioning**: Use URL versioning (/api/v1/)
3. **Error Responses**: Consistent error response format
4. **Documentation**: Auto-generated OpenAPI documentation
5. **Rate Limiting**: Implement rate limiting for production

### Database Rules
1. **Schema**: Use Beanie models for all collections
2. **Indexing**: Create appropriate indexes for queries
3. **Validation**: Validate all data before database operations
4. **Backups**: Regular backups of MongoDB Atlas
5. **Migrations**: Use Beanie migrations for schema changes

---

## Architecture Rules

### MCP Protocol Rules
1. **Compliance**: Full MCP protocol compliance
2. **Handlers**: Implement all required MCP handlers
3. **Types**: Use proper MCP types for all operations
4. **Error Handling**: Proper MCP error responses
5. **Documentation**: Document all MCP capabilities

### Agent Cooperation Rules
1. **Communication**: Use Celery tasks for agent communication
2. **State Sharing**: Use Redis for shared context
3. **Error Propagation**: Proper error handling across agents
4. **Monitoring**: Track agent performance and health
5. **Scaling**: Design for horizontal scaling

### Security Rules
1. **Authentication**: JWT tokens for all API access
2. **Authorization**: Role-based access control
3. **Data Encryption**: Encrypt sensitive data at rest
4. **Input Validation**: Validate all inputs
5. **Audit Logging**: Log all security-relevant events

---

## Implementation Rules

### Phase 1: Core MCP Features
1. **Database Integration**: Set up MongoDB + Redis
2. **Resource Management**: Implement MCP resource handlers
3. **Prompt System**: Create prompt template system
4. **Message Handling**: Add conversation management
5. **Authentication**: Implement user management

### Phase 2: Agent Cooperation
1. **Communication**: Set up Celery + Redis
2. **Shared Context**: Implement context sharing system
3. **Pipeline Processing**: Create workflow engine
4. **Agent Chaining**: Enable agent sequences
5. **Monitoring**: Add agent health monitoring

### Phase 3: Advanced Features
1. **Streaming**: Add WebSocket + SSE support
2. **Event System**: Implement event-driven architecture
3. **Memory**: Add persistent memory system
4. **Security**: Enhance security features
5. **Performance**: Optimize for production

### Phase 4: Production Readiness
1. **Testing**: Comprehensive test suite
2. **Documentation**: Complete documentation
3. **Deployment**: Production deployment scripts
4. **Monitoring**: Full monitoring stack
5. **Scaling**: Load balancing and scaling

---

## File Organization Rules

### Backend Structure
```
src/ai_mcp_toolkit/
├── agents/           # AI agents
├── server/           # MCP server
├── models/           # Database models (Beanie)
├── utils/            # Utilities
├── api/              # FastAPI routes
├── core/             # Core functionality
├── workflows/        # Workflow engine
├── events/           # Event system
└── security/         # Security features
```

### Frontend Structure
```
ui/src/
├── lib/
│   ├── components/   # UI components
│   ├── services/     # API services
│   ├── stores/       # State management
│   └── utils/        # Utilities
├── routes/           # SvelteKit routes
└── static/           # Static assets
```

### Configuration Files
```
├── pyproject.toml    # Python dependencies
├── package.json      # Node.js dependencies
├── docker-compose.yml # Development setup
├── nginx.conf        # Production proxy
├── prometheus.yml    # Monitoring config
└── .env.example      # Environment variables
```

---

## Testing Rules

### Unit Testing
1. **Coverage**: Minimum 80% code coverage
2. **Agents**: Test each agent independently
3. **APIs**: Test all API endpoints
4. **Models**: Test all database models
5. **Utils**: Test all utility functions

### Integration Testing
1. **Agent Communication**: Test agent interactions
2. **Database**: Test database operations
3. **APIs**: Test full API workflows
4. **Workflows**: Test complete workflows
5. **Authentication**: Test auth flows

### End-to-End Testing
1. **User Flows**: Test complete user journeys
2. **Agent Workflows**: Test agent pipelines
3. **Real-time**: Test WebSocket/SSE features
4. **Performance**: Test under load
5. **Security**: Test security features

---

## Documentation Rules

### Code Documentation
1. **Docstrings**: All public functions
2. **Type Hints**: All function parameters and returns
3. **Comments**: Complex logic explanations
4. **README**: Project overview and setup
5. **API Docs**: Auto-generated from code

### User Documentation
1. **Installation**: Step-by-step setup guide
2. **Configuration**: Configuration options
3. **Usage**: How to use each feature
4. **Examples**: Code examples and tutorials
5. **Troubleshooting**: Common issues and solutions

### Developer Documentation
1. **Architecture**: System architecture overview
2. **API Reference**: Complete API documentation
3. **Agent Guide**: How to create new agents
4. **Workflow Guide**: How to create workflows
5. **Deployment**: Production deployment guide

---

## Performance Rules

### Backend Performance
1. **Async**: Use async/await throughout
2. **Caching**: Cache frequently accessed data
3. **Database**: Optimize database queries
4. **Memory**: Monitor memory usage
5. **CPU**: Optimize CPU-intensive operations

### Frontend Performance
1. **Bundle Size**: Keep bundle size minimal
2. **Lazy Loading**: Load components on demand
3. **Caching**: Cache API responses
4. **Images**: Optimize images and assets
5. **Real-time**: Efficient WebSocket usage

### Database Performance
1. **Indexes**: Create appropriate indexes
2. **Queries**: Optimize query patterns
3. **Aggregation**: Use MongoDB aggregation
4. **Sharding**: Plan for horizontal scaling
5. **Monitoring**: Monitor query performance

---

## Security Rules

### Authentication
1. **JWT Tokens**: Use JWT for authentication
2. **Token Expiry**: Implement token expiration
3. **Refresh Tokens**: Use refresh token pattern
4. **Password Hashing**: Use bcrypt for passwords
5. **Session Management**: Secure session handling

### Authorization
1. **RBAC**: Role-based access control
2. **Permissions**: Fine-grained permissions
3. **API Keys**: Support API key authentication
4. **Rate Limiting**: Implement rate limiting
5. **Audit Logs**: Log all access attempts

### Data Protection
1. **Encryption**: Encrypt sensitive data
2. **Validation**: Validate all inputs
3. **Sanitization**: Sanitize user inputs
4. **CORS**: Configure CORS properly
5. **HTTPS**: Use HTTPS in production

---

## Monitoring Rules

### Application Monitoring
1. **Metrics**: Collect application metrics
2. **Logs**: Structured logging
3. **Errors**: Track and alert on errors
4. **Performance**: Monitor response times
5. **Health**: Health check endpoints

### Infrastructure Monitoring
1. **System**: Monitor CPU, RAM, disk
2. **Network**: Monitor network usage
3. **Database**: Monitor database performance
4. **Cache**: Monitor Redis performance
5. **GPU**: Monitor GPU usage

### Alerting
1. **Critical**: Alert on critical errors
2. **Performance**: Alert on performance issues
3. **Capacity**: Alert on resource usage
4. **Security**: Alert on security events
5. **Availability**: Alert on service downtime

---

## Deployment Rules

### Development Environment
1. **Docker**: Use Docker for development
2. **Docker Compose**: Use compose for services
3. **Environment**: Use .env files for config
4. **Hot Reload**: Enable hot reload for development
5. **Debugging**: Enable debug logging

### Production Environment
1. **NGINX**: Use NGINX as reverse proxy
2. **SSL**: Use SSL certificates
3. **Monitoring**: Deploy monitoring stack
4. **Backups**: Regular database backups
5. **Updates**: Automated updates and deployments

### Scaling Rules
1. **Horizontal**: Design for horizontal scaling
2. **Load Balancing**: Use NGINX load balancing
3. **Database**: Plan for database scaling
4. **Caching**: Use Redis for scaling
5. **Monitoring**: Monitor scaling metrics

---

## Maintenance Rules

### Regular Maintenance
1. **Updates**: Regular dependency updates
2. **Security**: Security patches and updates
3. **Backups**: Regular backup verification
4. **Monitoring**: Review monitoring data
5. **Performance**: Performance optimization

### Documentation Updates
1. **Code Changes**: Update code documentation
2. **API Changes**: Update API documentation
3. **User Guide**: Update user documentation
4. **Deployment**: Update deployment guides
5. **Troubleshooting**: Update troubleshooting guides

### Version Control
1. **Semantic Versioning**: Use semantic versioning
2. **Changelog**: Maintain changelog
3. **Releases**: Tag releases properly
4. **Rollback**: Plan for rollback procedures
5. **Migration**: Plan for data migrations

---

*These rules ensure consistency, quality, and maintainability throughout the AI MCP Toolkit enhancement project. All team members should follow these rules and update them as the project evolves.*
