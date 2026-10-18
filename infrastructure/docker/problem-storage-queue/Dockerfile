FROM node:20-alpine
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --omit=dev
COPY apps/problem-storage-queue/index.js ./index.js
USER node
CMD ["node", "index.js"]
