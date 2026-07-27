ARG FRAPPE_IMAGE=frappe/erpnext:v16.22.0
FROM ${FRAPPE_IMAGE}

USER root

COPY --chown=frappe:frappe . /home/frappe/frappe-bench/apps/consultation_center

RUN /home/frappe/frappe-bench/env/bin/pip install \
      --no-cache-dir \
      --editable /home/frappe/frappe-bench/apps/consultation_center \
    && printf '\nconsultation_center\n' >> /home/frappe/frappe-bench/sites/apps.txt \
    && sort -u /home/frappe/frappe-bench/sites/apps.txt \
      -o /home/frappe/frappe-bench/sites/apps.txt \
    && ln -sfn \
      /home/frappe/frappe-bench/apps/consultation_center/consultation_center/public \
      /home/frappe/frappe-bench/assets/consultation_center \
    && chmod 0755 \
      /home/frappe/frappe-bench/apps/consultation_center/docker/configure-runtime.sh \
      /home/frappe/frappe-bench/apps/consultation_center/docker/create-site.sh

USER frappe
