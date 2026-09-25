# Build stage
FROM docker.m.daocloud.io/library/node:22-alpine AS build-stage
# Use Aliyun Alpine mirror
RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' /etc/apk/repositories

WORKDIR /app
COPY apps/frontend/Admin /app/apps/frontend/Admin
COPY packages/shared /app/packages/shared
RUN npm config set registry https://registry.npmmirror.com
# Install shared package dependencies first
WORKDIR /app/packages/shared
RUN npm install
# Install Admin dependencies
WORKDIR /app/apps/frontend/Admin
RUN npm install && ln -s /app/apps/frontend/Admin/node_modules /app/apps/frontend/node_modules
RUN npx vite build

# Production stage
FROM docker.m.daocloud.io/library/nginx:stable-alpine AS production-stage
COPY --from=build-stage /app/apps/frontend/Admin/dist /usr/share/nginx/html
COPY --from=build-stage /app/apps/frontend/Admin/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
