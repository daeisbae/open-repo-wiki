FROM node:18-alpine AS builder

WORKDIR /app

COPY package*.json ./

RUN npm install --frozen-lockfile

COPY . .

RUN npm run build


FROM node:18-alpine

WORKDIR /app

COPY package*.json ./

RUN npm install --production --frozen-lockfile

COPY --from=builder /app/.next ./.next
COPY --from=builder /app/package*.json ./

ENV NODE_ENV=production
ENV PORT=3000

EXPOSE 3000

CMD ["npm", "start"]