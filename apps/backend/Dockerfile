# --- build -------------------------------------------------------------------
FROM docker.m.daocloud.io/library/golang:1.26-alpine AS build
WORKDIR /src
ENV GOPROXY=https://goproxy.cn,direct CGO_ENABLED=0
COPY go.mod go.sum ./
RUN go mod download
COPY cmd ./cmd
COPY internal ./internal
RUN go build -trimpath -ldflags="-s -w" -o /out/server ./cmd/server \
 && go build -trimpath -ldflags="-s -w" -o /out/createuser ./cmd/createuser

# --- run ---------------------------------------------------------------------
FROM docker.m.daocloud.io/library/alpine:3.20
WORKDIR /app
COPY --from=build /out/server /out/createuser ./
COPY static ./static
# Runs as root like the Python image did, so the existing ./data volume stays
# writable without changing its ownership on the server.
RUN mkdir -p static/uploads /data
EXPOSE 80
# SECRET_KEY, DATABASE_URL and FORWARDED_ALLOW_IPS come from docker-compose.
CMD ["./server", "-addr", ":80", "-dir", "/app"]
