# =============================================================================
# Frontend Dockerfile - Multi-stage build with Nginx
# =============================================================================
# This Dockerfile creates an optimized React/Vite application with Nginx
# For deployment with Coolify or any Docker-based platform
# =============================================================================

# =============================================================================
# Stage 1: Builder - Build the React application
# =============================================================================
FROM node:20-alpine AS builder

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
# Use --legacy-peer-deps if you have peer dependency conflicts
RUN npm ci --legacy-peer-deps

# Copy application source
COPY . .

# Build arguments for environment variables
# These will be baked into the build at build time
# Note: VITE_SUPABASE_KEY is the public anon key (safe to expose in client-side code)
ARG VITE_SUPABASE_URL
ARG VITE_SUPABASE_KEY
ARG VITE_BACKEND_URL

# Set environment variables for build
ENV VITE_SUPABASE_URL=$VITE_SUPABASE_URL
ENV VITE_SUPABASE_KEY=$VITE_SUPABASE_KEY
ENV VITE_BACKEND_URL=$VITE_BACKEND_URL

# Build the application
RUN npm run build


# =============================================================================
# Stage 2: Runtime - Serve with Nginx
# =============================================================================
FROM nginx:1.25-alpine

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built application from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://127.0.0.1:3000/health || exit 1

# Expose port 3000 (Coolify will use this)
EXPOSE 3000

# Start Nginx (runs as daemon off to keep container running)
CMD ["nginx", "-g", "daemon off;"]
