# Build stage
FROM node:18-alpine as build-stage
WORKDIR /app
COPY frontend/Barista /app/frontend/Barista
COPY frontend/shared /app/frontend/shared
WORKDIR /app/frontend/Barista
RUN rm -f package-lock.json && npm install && ln -s /app/frontend/Barista/node_modules /app/frontend/node_modules
RUN npx vite build --outDir dist

# Production stage
FROM nginx:stable-alpine as production-stage
COPY --from=build-stage /app/frontend/Barista/dist /usr/share/nginx/html
COPY --from=build-stage /app/frontend/Barista/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
