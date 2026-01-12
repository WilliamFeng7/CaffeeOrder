# /Users/f/Desktop/CoffeeOrder/frontend/Student/Dockerfile
FROM docker.m.daocloud.io/library/node:20-alpine as build-stage
# Use Aliyun Alpine mirror
RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' /etc/apk/repositories

WORKDIR /app
# Build is running in project root context
COPY frontend/Student /app/frontend/Student
COPY frontend/shared /app/frontend/shared
WORKDIR /app/frontend/Student
RUN npm config set registry https://registry.npmmirror.com
RUN npm install && ln -s /app/frontend/Student/node_modules /app/frontend/node_modules
# Override build config to output to dist and use root base
RUN npm run build -- --outDir dist

FROM docker.m.daocloud.io/library/nginx:stable-alpine as production-stage
COPY --from=build-stage /app/frontend/Student/dist /usr/share/nginx/html
# Copy custom Nginx config to enable API proxying
COPY --from=build-stage /app/frontend/Student/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
