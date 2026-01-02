# Build stage
FROM node:18-alpine as build-stage
WORKDIR /app
COPY frontend/Admin /app/frontend/Admin
COPY frontend/shared /app/frontend/shared
WORKDIR /app/frontend/Admin
RUN npm install
RUN npm run build

# Production stage
FROM nginx:stable-alpine as production-stage
COPY --from=build-stage /app/frontend/Admin/dist /usr/share/nginx/html
COPY --from=build-stage /app/frontend/Admin/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
