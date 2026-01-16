##############
# BASE STAGE #
##############
FROM node:22-alpine AS build

WORKDIR /app

ARG VITE_BASE_URL
ARG VITE_API_BASE_URL
ARG VITE_RASA_TRAINING_BASE_URL

ENV VITE_BASE_URL=${VITE_BASE_URL}
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
ENV VITE_RASA_TRAINING_BASE_URL=${VITE_RASA_TRAINING_BASE_URL}

COPY package*.json ./
RUN npm ci --legacy-peer-deps

COPY . .

RUN NODE_OPTIONS=--max-old-space-size=4096 npm run build

###############
# FINAL STAGE #
###############
FROM nginx:stable-alpine AS production

RUN apk add --no-cache bash
RUN rm -rf /usr/share/nginx/html/*
COPY nginx.conf /etc/nginx/nginx.conf

COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
