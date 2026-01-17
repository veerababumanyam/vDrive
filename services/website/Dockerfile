# RawDrive Website Service Dockerfile
# Multi-stage build for Astro static site

# ===========================================
# Stage 1: Dependencies
# ===========================================
FROM public.ecr.aws/docker/library/node:20-alpine AS deps

WORKDIR /app

# Install dependencies only
COPY package.json package-lock.json* ./
RUN npm ci --only=production=false

# ===========================================
# Stage 2: Builder
# ===========================================
FROM public.ecr.aws/docker/library/node:20-alpine AS builder

WORKDIR /app

# Copy dependencies
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Set build-time environment variables
ARG SITE_URL=https://www.RawDrive.io
ARG APP_URL=https://app.RawDrive.io
ENV SITE_URL=$SITE_URL
ENV APP_URL=$APP_URL

# Build the application
RUN npm run build

# ===========================================
# Stage 3: Runner (Production) - Nginx for static files
# ===========================================
FROM public.ecr.aws/nginx/nginx:alpine AS runner

# Copy built static files
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom nginx config for SPA routing
RUN echo 'server { \
    listen 8020; \
    server_name localhost; \
    root /usr/share/nginx/html; \
    index index.html; \
    \
    # Gzip compression \
    gzip on; \
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml; \
    \
    # Security headers \
    add_header X-Frame-Options "SAMEORIGIN" always; \
    add_header X-Content-Type-Options "nosniff" always; \
    add_header X-XSS-Protection "1; mode=block" always; \
    \
    # Static file caching \
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ { \
        expires 1y; \
        add_header Cache-Control "public, immutable"; \
    } \
    \
    # Try files or 404 \
    location / { \
        try_files $uri $uri/ $uri.html /index.html; \
    } \
}' > /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 8020

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:8020/ || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
