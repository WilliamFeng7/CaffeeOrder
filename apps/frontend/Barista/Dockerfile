# Build stage
FROM docker.m.daocloud.io/library/node:22-alpine AS build-stage
# Use Aliyun Alpine mirror
RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' /etc/apk/repositories

WORKDIR /app
COPY apps/frontend/Barista /app/apps/frontend/Barista
COPY packages/shared /app/packages/shared
RUN npm config set registry https://registry.npmmirror.com
# Install shared package dependencies first
WORKDIR /app/packages/shared
RUN npm install
# Install Barista dependencies
WORKDIR /app/apps/frontend/Barista
RUN rm -f package-lock.json && npm install && ln -s /app/apps/frontend/Barista/node_modules /app/apps/frontend/node_modules
RUN npx vite build --outDir dist

# Production stage
FROM docker.m.daocloud.io/library/nginx:stable-alpine AS production-stage
COPY --from=build-stage /app/apps/frontend/Barista/dist /usr/share/nginx/html
COPY --from=build-stage /app/apps/frontend/Barista/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
