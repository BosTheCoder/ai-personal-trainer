FROM node:18-alpine

RUN apk add --no-cache curl

WORKDIR /app

COPY package*.json ./

RUN npm install

COPY . .

RUN npm run build

EXPOSE 3000

ENV HOSTNAME=0.0.0.0

CMD ["node", ".next/standalone/server.js"]
