FROM hashicorp/terraform:1.0.7 as terraform

FROM google/cloud-sdk:alpine

COPY --from=terraform /bin/terraform /bin/

COPY deploy.sh /

WORKDIR /workspace

ENTRYPOINT ["/deploy.sh"]