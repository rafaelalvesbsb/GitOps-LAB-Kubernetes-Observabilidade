# Build estático, sem CGO — permite usar "scratch" como imagem final (sem shell, sem
# pacotes de SO, superfície de ataque mínima e poucos achados de CVE no Trivy).
FROM golang:1.22-alpine AS build
WORKDIR /src
COPY src/go.mod ./
COPY src/*.go ./
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o /sample-app .

FROM scratch
ARG VERSION=dev
ENV VERSION=${VERSION}
COPY --from=build /sample-app /sample-app
USER 65532:65532
EXPOSE 8080
ENTRYPOINT ["/sample-app"]
