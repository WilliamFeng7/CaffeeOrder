# Build stage
FROM docker.m.daocloud.io/library/node:22-alpine AS build-stage
# Use Aliyun Alpine mirror
RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' /etc/apk/repositories

WORKDIR /app
# Build is running in project root context (CoffeeOrder/)
COPY apps/frontend/Student /app/apps/frontend/Student
COPY packages/shared /app/packages/shared
RUN npm config set registry https://registry.npmmirror.com
# Install shared package dependencies first
WORKDIR /app/packages/shared
RUN npm install
# Install Student dependencies
WORKDIR /app/apps/frontend/Student
RUN npm install && ln -s /app/apps/frontend/Student/node_modules /app/apps/frontend/node_modules
# Override build config to output to dist and use root base
RUN npm run build -- --outDir dist

# Production stage
FROM docker.m.daocloud.io/library/nginx:stable-alpine AS production-stage
COPY --from=build-stage /app/apps/frontend/Student/dist /usr/share/nginx/html
COPY --from=build-stage /app/apps/frontend/Student/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
