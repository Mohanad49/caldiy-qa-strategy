FROM node:20.19.5-alpine3.22@sha256:6178e78b972f79c335df281f4b7674a2d85071aae2af020ffa39f0a770265435

ARG API_BUILD_HEAP_MB=8192
ARG CALDIY_SOURCE_SHA
ARG DATABASE_DIRECT_URL
ARG DATABASE_URL

LABEL org.opencontainers.image.source="https://github.com/calcom/cal.diy" \
      org.opencontainers.image.revision="${CALDIY_SOURCE_SHA}" \
      org.opencontainers.image.version="v6.2.0" \
      org.opencontainers.image.licenses="UNLICENSED" \
      io.caldiy.qa.redistributable="false" \
      io.caldiy.qa.build-heap-mb="${API_BUILD_HEAP_MB}"

WORKDIR /calcom

RUN set -eux; \
    ln -s /usr/lib/libssl.so.3 /lib/libssl.so.3

ENV NODE_ENV="production" \
    NODE_OPTIONS="--max-old-space-size=${API_BUILD_HEAP_MB}" \
    DATABASE_DIRECT_URL="${DATABASE_DIRECT_URL}" \
    DATABASE_URL="${DATABASE_URL}" \
    USE_POOL="true"

COPY . .

RUN yarn install
RUN yarn workspace @calcom/api-v2 run generate-schemas
RUN yarn workspace @calcom/api-v2 run build:docker
RUN yarn workspace @calcom/api-v2 run build

EXPOSE 5555

CMD ["yarn", "workspace", "@calcom/api-v2", "start:prod"]
