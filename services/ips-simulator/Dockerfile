# IPS Simulator
FROM node:20-alpine

# Create non-root user for security
RUN addgroup -g 1001 -S appgroup && \
    adduser -S appuser -u 1001 -G appgroup

WORKDIR /app
COPY package*.json ./
RUN npm install --omit=dev
COPY src/ ./src/

# Set proper permissions
RUN chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

HEALTHCHECK --interval=30s --timeout=10s CMD wget -qO- http://localhost:3000/health || exit 1
EXPOSE 3000
CMD ["node", "src/index.js"]
