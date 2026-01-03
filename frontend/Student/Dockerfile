# /Users/f/Desktop/CoffeeOrder/frontend/Student/Dockerfile
FROM node:20-alpine as build-stage
WORKDIR /app
# Build is running in project root context
COPY frontend/Student /app/frontend/Student
COPY frontend/shared /app/frontend/shared
WORKDIR /app/frontend/Student
RUN npm install && ln -s /app/frontend/Student/node_modules /app/frontend/node_modules
# Override build config to output to dist and use root base
RUN npm run build -- --outDir dist

FROM nginx:stable-alpine as production-stage
COPY --from=build-stage /app/frontend/Student/dist /usr/share/nginx/html
# Copy custom Nginx config to enable API proxying
COPY --from=build-stage /app/frontend/Student/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
