# Stage 1: Builder
FROM node:22-alpine AS builder

WORKDIR /app

# Enable pnpm
RUN corepack enable && corepack prepare pnpm@latest --activate

# Copy package descriptors
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

# Copy application source
COPY . ./

# Build Nuxt 3 production server
RUN pnpm run build

# Stage 2: Lightweight Production Runner
FROM node:22-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production
ENV PORT=3000
ENV HOST=0.0.0.0

# Security: Non-root user
USER node

# Copy compiled output
COPY --from=builder --chown=node:node /app/.output ./.output

EXPOSE 3000

CMD ["node", ".output/server/index.mjs"]
