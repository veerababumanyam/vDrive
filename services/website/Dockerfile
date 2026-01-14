# vDrive Website Service Dockerfile
# Multi-stage build for Astro with Node.js adapter

# ===========================================
# Stage 1: Dependencies
# ===========================================
FROM node:20-alpine AS deps

WORKDIR /app

# Install dependencies only
COPY package.json package-lock.json* ./
RUN npm ci --only=production=false

# ===========================================
# Stage 2: Builder
# ===========================================
FROM node:20-alpine AS builder

WORKDIR /app

# Copy dependencies
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Set build-time environment variables
ARG SITE_URL=https://www.vdrive.io
ARG APP_URL=https://app.vdrive.io
ENV SITE_URL=$SITE_URL
ENV APP_URL=$APP_URL

# Build the application
RUN npm run build

# ===========================================
# Stage 3: Runner (Production)
# ===========================================
FROM node:20-alpine AS runner

WORKDIR /app

# Set production environment
ENV NODE_ENV=production
ENV HOST=0.0.0.0
ENV PORT=8020

# Create non-root user
RUN addgroup --system --gid 1001 nodejs && \
  adduser --system --uid 1001 astro

# Copy built application
COPY --from=builder --chown=astro:nodejs /app/dist ./dist
COPY --from=builder --chown=astro:nodejs /app/node_modules ./node_modules
COPY --from=builder --chown=astro:nodejs /app/package.json ./package.json

# Switch to non-root user
USER astro

# Expose port
EXPOSE 8020

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:8020/ || exit 1

# Start the server
CMD ["node", "./dist/server/entry.mjs"]
