# Database Setup Guide

## Overview

AI MCP Toolkit uses MongoDB for persistent storage and Redis for caching. This guide covers setup options for both local development and production deployment.

## Quick Start (Local Development)

### Option 1: Local MongoDB + Local Redis (Recommended for Development)

```bash
# Install MongoDB (macOS)
brew tap mongodb/brew
brew install mongodb-community@7.0

# Install Redis (macOS)
brew install redis

# Start MongoDB
brew services start mongodb-community@7.0

# Start Redis
brew services start redis

# Your .env should have:
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=ai_mcp_toolkit
REDIS_URL=redis://localhost:6379
REDIS_DB=0
```

### Option 2: MongoDB Atlas (Cloud) + Local Redis

1. **Create MongoDB Atlas account**: https://www.mongodb.com/cloud/atlas/register
2. **Create a free cluster** (M0 tier is free forever)
3. **Get connection string**:
   - Click "Connect" → "Connect your application"
   - Copy the connection string
   - Replace `<password>` with your database user password

```bash
# Your .env should have:
MONGODB_URL=mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
MONGODB_DATABASE=ai_mcp_toolkit
REDIS_URL=redis://localhost:6379
REDIS_DB=0
```

## Environment Variables

### Required MongoDB Variables

```bash
# MongoDB Connection URL
# Local: mongodb://localhost:27017
# Atlas: mongodb+srv://<username>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority
MONGODB_URL=mongodb://localhost:27017

# Database name (will be created automatically)
MONGODB_DATABASE=ai_mcp_toolkit
```

### Optional MongoDB Variables

```bash
# Connection pool settings (use defaults for most cases)
MONGODB_MAX_POOL_SIZE=100      # Maximum connections in pool
MONGODB_MIN_POOL_SIZE=10       # Minimum connections in pool
MONGODB_MAX_IDLE_TIME_MS=30000 # Max idle time in milliseconds
```

### Redis Variables (Optional - for caching)

```bash
# Redis Connection URL
# Local: redis://localhost:6379
# Cloud: redis://<username>:<password>@<host>:<port>
REDIS_URL=redis://localhost:6379

# Redis database number (0-15)
REDIS_DB=0
```

**Note**: Redis is optional. If Redis is not available, the application will continue to work without caching.

## MongoDB Atlas Setup (Detailed)

### Step 1: Create Account and Cluster

1. Go to https://www.mongodb.com/cloud/atlas/register
2. Sign up for a free account
3. Create a new project (e.g., "AI MCP Toolkit")
4. Click "Build a Database"
5. Choose "M0 Free" tier
6. Select your preferred cloud provider and region
7. Name your cluster (e.g., "ai-mcp-cluster")
8. Click "Create"

### Step 2: Configure Database Access

1. Go to "Database Access" in the left sidebar
2. Click "Add New Database User"
3. Choose "Password" authentication
4. Create username and password (save these securely!)
5. Set user privileges to "Read and write to any database"
6. Click "Add User"

### Step 3: Configure Network Access

1. Go to "Network Access" in the left sidebar
2. Click "Add IP Address"
3. For development: Click "Allow Access from Anywhere" (0.0.0.0/0)
4. For production: Add your server's specific IP address
5. Click "Confirm"

### Step 4: Get Connection String

1. Go back to "Database" in the left sidebar
2. Click "Connect" on your cluster
3. Choose "Connect your application"
4. Select "Python" and version "3.12 or later"
5. Copy the connection string
6. Replace `<password>` with your actual database user password
7. Add to your `.env` file:

```bash
MONGODB_URL=mongodb+srv://your-username:your-password@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
```

### Step 5: Verify Connection

```bash
# Test the connection
python -c "from motor.motor_asyncio import AsyncIOMotorClient; import asyncio; asyncio.run(AsyncIOMotorClient('YOUR_MONGODB_URL').admin.command('ping')); print('✅ MongoDB connection successful!')"
```

## Local MongoDB Setup (Detailed)

### macOS

```bash
# Install MongoDB using Homebrew
brew tap mongodb/brew
brew install mongodb-community@7.0

# Start MongoDB service
brew services start mongodb-community@7.0

# Verify MongoDB is running
brew services list | grep mongodb

# Test connection
mongosh

# Stop MongoDB (when needed)
brew services stop mongodb-community@7.0
```

### Linux (Ubuntu/Debian)

```bash
# Import MongoDB public GPG key
wget -qO - https://www.mongodb.org/static/pgp/server-7.0.asc | sudo apt-key add -

# Add MongoDB repository
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu $(lsb_release -cs)/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list

# Update package database
sudo apt-get update

# Install MongoDB
sudo apt-get install -y mongodb-org

# Start MongoDB
sudo systemctl start mongod
sudo systemctl enable mongod  # Enable auto-start on boot

# Verify status
sudo systemctl status mongod
```

### Docker (All Platforms)

```bash
# Run MongoDB in Docker
docker run -d \
  --name mongodb \
  -p 27017:27017 \
  -v mongodb_data:/data/db \
  mongo:7.0

# Verify it's running
docker ps | grep mongodb

# Stop MongoDB
docker stop mongodb

# Start MongoDB
docker start mongodb
```

## Redis Setup (Optional but Recommended)

### macOS

```bash
# Install Redis using Homebrew
brew install redis

# Start Redis service
brew services start redis

# Verify Redis is running
redis-cli ping  # Should return "PONG"

# Stop Redis (when needed)
brew services stop redis
```

### Linux (Ubuntu/Debian)

```bash
# Install Redis
sudo apt-get update
sudo apt-get install redis-server

# Start Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server  # Enable auto-start on boot

# Verify status
sudo systemctl status redis-server

# Test connection
redis-cli ping  # Should return "PONG"
```

### Docker

```bash
# Run Redis in Docker
docker run -d \
  --name redis \
  -p 6379:6379 \
  redis:7-alpine

# Verify it's running
docker ps | grep redis

# Test connection
docker exec redis redis-cli ping  # Should return "PONG"
```

## Database Collections

The application automatically creates these collections in MongoDB:

- **users** - User accounts and authentication
- **sessions** - Active user sessions
- **audit_logs** - Security and action audit trail
- **resources** - MCP protocol resources
- **prompts** - Prompt templates
- **messages** - Chat messages
- **conversations** - Conversation history per user
- **agent_states** - Agent execution states
- **workflows** - Workflow definitions

Indexes are automatically created for optimal performance.

## Troubleshooting

### MongoDB Connection Issues

**Problem**: `ServerSelectionTimeoutError: connection timeout`

**Solutions**:
1. Check MongoDB is running: `brew services list` (macOS) or `sudo systemctl status mongod` (Linux)
2. Verify connection string in `.env` is correct
3. For Atlas: Check Network Access allows your IP
4. For Atlas: Verify username/password in connection string

**Problem**: `Authentication failed`

**Solutions**:
1. Verify username and password in connection string
2. Check database user has correct permissions in Atlas
3. Ensure password doesn't contain special characters (URL encode if needed)

### Redis Connection Issues

**Problem**: `Connection refused to redis://localhost:6379`

**Solutions**:
1. Check Redis is running: `brew services list` (macOS) or `sudo systemctl status redis` (Linux)
2. Try connecting manually: `redis-cli ping`
3. If Redis fails, the app will continue without caching (warning logged)

### Migration from Old Data

If you were using local storage before:

```bash
# Conversations are now in MongoDB
# Old localStorage data won't automatically migrate
# Users will need to start fresh conversations
```

## Production Deployment

### Recommended Setup

- **MongoDB**: Use MongoDB Atlas (M10+ tier for production workloads)
- **Redis**: Use managed Redis (Redis Cloud, AWS ElastiCache, etc.)
- **Backups**: Enable automated backups in MongoDB Atlas
- **Monitoring**: Enable MongoDB Atlas monitoring and alerts

### Security Best Practices

1. **Use strong passwords** for database users
2. **Restrict network access** to specific IP addresses
3. **Enable SSL/TLS** for connections (Atlas enables this by default)
4. **Rotate credentials** regularly
5. **Monitor access logs** for suspicious activity
6. **Use environment variables** for sensitive configuration (never commit passwords)

### Connection String Security

❌ **Don't do this**:
```bash
# Committing credentials to git
MONGODB_URL=mongodb+srv://admin:password123@cluster0.mongodb.net/
```

✅ **Do this**:
```bash
# Use environment variables
MONGODB_URL=${MONGODB_CONNECTION_STRING}

# Or use secrets management
MONGODB_URL=$(aws secretsmanager get-secret-value --secret-id mongodb-url --query SecretString --output text)
```

## Testing Database Connection

Test your database configuration:

```bash
# Start the server and check logs
python main.py

# Look for these messages:
# ✅ "Connected to MongoDB Atlas: ai_mcp_toolkit"
# ✅ "Beanie initialized with document models"
# ✅ "Connected to Redis: redis://localhost:6379"
# ✅ "Database connections established successfully"
```

Check the health endpoint:

```bash
curl http://localhost:8000/health

# Expected response:
{
  "status": "healthy",
  "database": {
    "mongodb": true,
    "redis": true,
    "overall": true
  }
}
```

## Docker Compose Example

For easy local development with Docker:

```yaml
version: '3.8'

services:
  mongodb:
    image: mongo:7.0
    container_name: ai-mcp-mongodb
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db
    environment:
      MONGO_INITDB_DATABASE: ai_mcp_toolkit

  redis:
    image: redis:7-alpine
    container_name: ai-mcp-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  mongodb_data:
  redis_data:
```

Save as `docker-compose.yml` and run:

```bash
docker-compose up -d
```

## Performance Optimization

### MongoDB Indexes

Indexes are automatically created by Beanie. Manual index creation (if needed):

```javascript
// Connect to MongoDB
use ai_mcp_toolkit

// Check existing indexes
db.conversations.getIndexes()

// Create custom index (example)
db.conversations.createIndex({ "user_id": 1, "created_at": -1 })
```

### Redis Optimization

```bash
# Check Redis memory usage
redis-cli info memory

# Set max memory policy (optional)
redis-cli CONFIG SET maxmemory 256mb
redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

## Related Documentation

- [MongoDB Atlas Documentation](https://docs.atlas.mongodb.com/)
- [Motor (Async MongoDB Driver)](https://motor.readthedocs.io/)
- [Beanie ODM](https://beanie-odm.dev/)
- [Redis Documentation](https://redis.io/documentation)

---

**Need help?** Check the logs or create an issue on GitHub with your error messages (redact any sensitive information like passwords or connection strings).
