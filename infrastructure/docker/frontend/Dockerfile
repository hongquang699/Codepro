FROM node:20-alpine

WORKDIR /app

COPY apps/web/package*.json ./apps/web/
RUN cd apps/web && npm ci --omit=dev

COPY apps/web/ ./apps/web/
COPY frontend/ ./frontend/
COPY favicon.ico ./favicon.ico

EXPOSE 8888

CMD ["node", "apps/web/server.js"]
