FROM node:20-alpine
RUN apk add --no-cache git
WORKDIR /app
COPY package.json ./
RUN npm install
COPY index.js .
EXPOSE 3000
VOLUME [ "/app/session" ]
CMD ["node", "index.js"]
