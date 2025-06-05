FROM openeuler/openeuler:24.03

RUN yum install shadow-utils python3-pip -y
RUN groupadd -g 1001 hotopic \
    && useradd -u 1001 -g hotopic -s /bin/bash -m hotopic

WORKDIR /app
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

USER hotopic

# CMD ["python", "app/main.py"]
